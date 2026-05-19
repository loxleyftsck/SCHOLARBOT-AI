"""Tests for scholarbot/api.py FastAPI Server."""

import os
import io
import sys
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
        assert response.status_code == 422  # validation error from pydantic since empty strings aren't parsed as valid, or 400


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
        session_id = "test-session-reset-123"
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
        session_id = "test-session-clear-docs-123"
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
