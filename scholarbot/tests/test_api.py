"""Tests for scholarbot/api.py FastAPI Server."""

import os
import io
import json
import sys
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add scholarship root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app, SESSIONS


@pytest.fixture
def client():
    """Create a TestClient instance."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check API."""

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "groq_configured" in data


class TestChatEndpoint:
    """Test Chat & Streaming endpoint."""

    @patch("api.stream_chat")
    def test_chat_streaming(self, mock_stream_chat, client):
        # Mock streaming tokens
        mock_stream_chat.return_value = iter(["Halo", " ", "dunia", "!"])

        payload = {
            "message": "Halo asisten",
            "personality": "😊 Santai & Friendly",
            "user_name": "Budi",
            "mode": "belajar"
        }

        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert response.text == "Halo dunia!"

        # Verify session was created
        session_ids = list(SESSIONS.keys())
        assert len(session_ids) > 0
        session_id = session_ids[0]
        state = SESSIONS[session_id]

        # Verify messages list has user and bot messages
        assert len(state.messages) == 2
        assert state.messages[0]["role"] == "user"
        assert state.messages[0]["content"] == "Halo asisten"
        assert state.messages[1]["role"] == "assistant"
        assert state.messages[1]["content"] == "Halo dunia!"

    def test_chat_empty_message_returns_error(self, client):
        payload = {
            "message": "",
            "mode": "belajar"
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code in (400, 422)  # validation error or explicit check

    @patch("api.stream_chat")
    def test_chat_short_command_not_expanded_outside_quiz(self, mock_stream_chat, client):
        mock_stream_chat.return_value = iter(["Respons"])
        SESSIONS.clear()

        payload = {
            "message": "jelaskan",
            "personality": "🎓 Formal Tutor",
            "user_name": "Budi",
            "mode": "belajar"
        }

        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200

        session_id = list(SESSIONS.keys())[0]
        state = SESSIONS[session_id]
        
        # Verify that the message was saved exactly as is and not expanded
        assert state.messages[0]["content"] == "jelaskan"
        assert state.current_context != "quiz"
        assert state.last_question == ""


class TestCitationSystem:
    """Chat answers must carry numbered, verifiable sources (v4.0 citation system)."""

    def _session_with_docs(self, client):
        """Upload a document so RAG retrieval kicks in for the next chat call."""
        SESSIONS.clear()
        body = (
            "Elastisitas permintaan mengukur kepekaan jumlah barang terhadap harga.\n\n"
            "Permintaan disebut elastis bila perubahan harga sangat memengaruhi jumlah beli.\n\n"
            "Fotosintesis adalah proses tumbuhan mengubah cahaya menjadi energi kimia."
        )
        response = client.post(
            "/api/upload",
            files={"file": ("ekonomi.txt", io.BytesIO(body.encode("utf-8")), "text/plain")}
        )
        assert response.status_code == 200
        return response.json()["session_id"]

    @patch("api.retrieve")
    @patch("api.stream_chat")
    def test_sources_are_numbered_for_the_frontend(self, mock_stream_chat, mock_retrieve, client):
        from services.retriever import RetrievedChunk

        session_id = self._session_with_docs(client)
        mock_retrieve.return_value = [
            RetrievedChunk(content="Elastisitas mengukur kepekaan.", score=0.91,
                           source_filename="ekonomi.txt", chunk_index=0),
            RetrievedChunk(content="Permintaan elastis bila harga berpengaruh.", score=0.77,
                           source_filename="ekonomi.txt", chunk_index=1),
        ]
        mock_stream_chat.return_value = iter(["Elastisitas mengukur kepekaan permintaan. [1]"])

        response = client.post("/api/chat", json={
            "message": "Apa itu elastisitas permintaan?",
            "session_id": session_id,
            "mode": "belajar"
        })
        assert response.status_code == 200

        sources = json.loads(response.headers["X-RAG-Sources"])
        assert [s["id"] for s in sources] == [1, 2]
        assert sources[0]["source"] == "ekonomi.txt"
        assert sources[0]["chunk_index"] == 0
        assert sources[0]["score"] == pytest.approx(0.91)

    @patch("api.retrieve")
    @patch("api.stream_chat")
    def test_cited_ids_recorded_and_hallucinated_ones_dropped(self, mock_stream_chat, mock_retrieve, client):
        from services.retriever import RetrievedChunk

        session_id = self._session_with_docs(client)
        mock_retrieve.return_value = [
            RetrievedChunk(content="Elastisitas mengukur kepekaan.", score=0.91,
                           source_filename="ekonomi.txt", chunk_index=0),
        ]
        # The model cites source 1 correctly but invents source 5
        mock_stream_chat.return_value = iter(["Elastisitas itu kepekaan. [1] Klaim tambahan. [5]"])

        response = client.post("/api/chat", json={
            "message": "Apa itu elastisitas permintaan?",
            "session_id": session_id,
            "mode": "belajar"
        })
        assert response.status_code == 200

        state = SESSIONS[session_id]
        bot_msg = state.messages[-1]
        assert bot_msg["role"] == "assistant"
        assert bot_msg["cited_ids"] == [1]

    @patch("api.stream_chat")
    def test_no_documents_means_no_sources(self, mock_stream_chat, client):
        SESSIONS.clear()
        mock_stream_chat.return_value = iter(["Jawaban umum tanpa dokumen."])

        response = client.post("/api/chat", json={"message": "Apa itu fotosintesis?", "mode": "belajar"})
        assert response.status_code == 200
        assert json.loads(response.headers["X-RAG-Sources"]) == []

        state = SESSIONS[list(SESSIONS.keys())[0]]
        assert state.messages[-1]["cited_ids"] == []




class TestUploadEndpoint:
    """Test RAG document upload and chunking."""

    def test_upload_text_file(self, client):
        file_content = b"Ini adalah isi dokumen test untuk RAG ScholarBot."
        file_name = "test_document.txt"

        response = client.post(
            "/api/upload",
            files={"file": (file_name, io.BytesIO(file_content), "text/plain")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["filename"] == "test_document.txt"
        assert data["chunks_count"] > 0
        assert len(data["uploaded_docs"]) == 1
        assert data["uploaded_docs"][0]["filename"] == "test_document.txt"

        # Verify session ID was returned and contains chunks
        session_id = data["session_id"]
        assert session_id in SESSIONS
        state = SESSIONS[session_id]
        assert len(state.doc_chunks) > 0
        assert state.doc_chunks[0]["source"] == "test_document.txt"

    def test_upload_invalid_extension(self, client):
        response = client.post(
            "/api/upload",
            files={"file": ("test.png", io.BytesIO(b"dummy image content"), "image/png")}
        )
        assert response.status_code == 400
        assert "Hanya mendukung file .txt atau .pdf" in response.json()["detail"]


class TestSessionManagement:
    """Test session lifecycle controls."""

    def test_reset_session(self, client):
        # 1. Initialize a session with a dummy state
        session_id = f"test-reset-{uuid.uuid4().hex[:8]}"
        client.post(
            "/api/upload",
            data={"session_id": session_id},
            files={"file": ("doc.txt", io.BytesIO(b"Doc content"), "text/plain")}
        )
        
        # Add messages
        SESSIONS[session_id].messages = [{"role": "user", "content": "hi"}]
        SESSIONS[session_id].topics_discussed = ["hi"]
        SESSIONS[session_id].current_context = "quiz"

        # 2. Reset session
        response = client.post(f"/api/session/{session_id}/reset")
        assert response.status_code == 200
        assert response.json()["message"] == "Sesi obrolan berhasil dibersihkan"

        # 3. Check memory preserved / cleared correctly
        state = SESSIONS[session_id]
        assert len(state.messages) == 0
        assert len(state.topics_discussed) == 0
        assert state.current_context == ""
        # Uploaded docs must remain after obrolan reset!
        assert len(state.uploaded_docs) == 1
        assert len(state.doc_chunks) == 1

    def test_clear_documents(self, client):
        # 1. Initialize session with document
        session_id = f"test-clear-{uuid.uuid4().hex[:8]}"
        client.post(
            "/api/upload",
            data={"session_id": session_id},
            files={"file": ("doc.txt", io.BytesIO(b"Doc content"), "text/plain")}
        )
        
        assert len(SESSIONS[session_id].uploaded_docs) == 1
        assert len(SESSIONS[session_id].doc_chunks) == 1

        # 2. Clear docs
        response = client.post(f"/api/session/{session_id}/clear-docs")
        assert response.status_code == 200
        assert response.json()["message"] == "Semua dokumen berhasil dihapus"

        # 3. Verify cleared
        state = SESSIONS[session_id]
        assert len(state.uploaded_docs) == 0
        assert len(state.doc_chunks) == 0


class TestMindMapEndpoints:
    """Test dynamic mind map generation and expansion endpoints."""

    @patch("api.chat")
    def test_generate_mindmap(self, mock_chat, client):
        mock_chat.return_value = '{"nodes": [{"id": "1", "label": "ML", "type": "root", "desc": "Desc"}], "edges": []}'

        payload = {
            "topic": "Machine Learning",
            "session_id": "test-session"
        }

        response = client.post("/api/mindmap/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert data["nodes"][0]["label"] == "ML"

    @patch("api.chat")
    def test_expand_mindmap(self, mock_chat, client):
        mock_chat.return_value = '{"nodes": [{"id": "2", "label": "Supervised", "type": "sub-branch", "desc": "Desc"}], "edges": [{"source": "1", "target": "2"}]}'

        payload = {
            "topic": "Machine Learning",
            "node_id": "1",
            "node_label": "Machine Learning",
            "existing_nodes": [{"id": "1", "label": "Machine Learning", "type": "root", "desc": "Desc"}],
            "existing_edges": [],
            "session_id": "test-session"
        }

        response = client.post("/api/mindmap/expand", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert data["nodes"][0]["label"] == "Supervised"

