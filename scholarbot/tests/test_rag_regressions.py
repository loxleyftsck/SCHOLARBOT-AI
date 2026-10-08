"""Offline regressions for phase A: evidence selection, routing and chunk coverage."""
import json
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from services.chunker import Chunk, chunk_text, chunk_semantically, chunk_by_size
from services.retriever import RetrievedChunk, retrieve, compute_relevance_score, select_context_chunks, format_retrieved_context
from core.rag_context import should_use_rag, build_rag_system_prompt
from api import app, SESSIONS, SessionState


def evidence(content, index=0):
    return RetrievedChunk(content, 0.9, "materi.txt", index)


def test_no_overlap_is_not_relevant():
    text = "Pengelolaan keuangan meliputi anggaran dan pencatatan transaksi."
    assert compute_relevance_score("fotosintesis", text) == 0
    assert retrieve("fotosintesis", [Chunk(text, 0, "keuangan.txt")]) == []


def test_substrings_do_not_count_as_terms():
    assert compute_relevance_score("fisika", "metafisika") == 0


@pytest.mark.parametrize("message", ["Jelaskan dokumen ini", "Apa isi file saya?", "Bagaimana cara menghapus data?", "lanjut", "hint"])
def test_document_questions_keep_rag(message):
    assert should_use_rag(message, True)


@pytest.mark.parametrize("message", ["hapus dokumen ini", "tolong reset chat", "unggah file", "clear", "oke"])
def test_control_commands_skip_rag(message):
    assert not should_use_rag(message, True)


@pytest.mark.parametrize("strategy", ["auto", "semantic", "paragraph", "size"])
def test_bounded_chunks_preserve_tail_when_embeddings_fail(strategy):
    text = "Ini kalimat materi pembelajaran. " * 110 + "PENANDA AKHIR PENTING"
    with patch("services.semantic_search.get_embeddings_batch", return_value=None):
        chunks = chunk_text(text, strategy=strategy, filename="contoh.txt", max_chars=200)
    assert all(0 < len(c.content) <= 200 for c in chunks)
    assert any("PENANDA AKHIR PENTING" in c.content for c in chunks)
    assert all(c.source_filename == "contoh.txt" for c in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_short_paragraphs_not_discarded():
    text = "Fotosintesis memakai cahaya.\n\n" + "Materi panjang. " * 100 + "\n\nOksigen dihasilkan."
    chunks = chunk_text(text, strategy="paragraph", max_chars=200)
    assert "Fotosintesis memakai cahaya." in " ".join(c.content for c in chunks)
    assert "Oksigen dihasilkan." in " ".join(c.content for c in chunks)


def test_long_sentence_semantic_path_stays_bounded():
    with patch("services.semantic_search.get_embeddings_batch", return_value=None):
        chunks = chunk_semantically("kata " * 400, max_chunk_chars=100)
    assert max(len(c.content) for c in chunks) <= 100


def test_budget_includes_labels_and_only_lists_available_sources():
    chunks = [evidence("A" * 800, 0), evidence("B" * 800, 1), evidence("C" * 800, 2)]
    selected = select_context_chunks(chunks)
    assert len(selected) == 2
    assert len(format_retrieved_context(selected)) <= 1200
    assert select_context_chunks(selected) == selected
    prompt = build_rag_system_prompt("BASE", chunks)
    assert "[3]" not in prompt
    assert "[1], [2]" in prompt
    assert "A" * 100 in prompt
    assert "C" * 100 not in prompt


def test_tiny_budget_does_not_create_empty_sources():
    assert select_context_chunks([evidence("materi")], max_chars=5) == []


def test_chunk_size_validation():
    with pytest.raises(ValueError):
        chunk_by_size("hello", chunk_size=0)


@pytest.fixture
def api_session():
    import uuid
    sid = str(uuid.uuid4())
    state = SessionState()
    state.doc_chunks = [Chunk("contoh materi", 0, "materi.txt")]
    SESSIONS[sid] = state
    with patch("api.persist_session"):
        yield TestClient(app), sid, state
    SESSIONS.pop(sid, None)


def test_api_sources_equal_exact_prompt_evidence(api_session):
    client, sid, state = api_session
    results = [evidence("A" * 800, 0), evidence("B" * 800, 1), evidence("C" * 800, 2)]
    with patch("api.retrieve", return_value=results), patch("api.stream_chat", return_value=iter(["Jawaban. [1]"])) as stream:
        response = client.post("/api/chat", json={"message": "Jelaskan dokumen ini", "session_id": sid})
    assert response.status_code == 200
    sources = json.loads(response.headers["X-RAG-Sources"])
    prompt = stream.call_args.kwargs["messages"][0]["content"]
    assert len(sources) == 2
    assert "[3]" not in prompt
    for source in sources:
        assert source["content"] in prompt
    assert state.messages[-1]["sources"] == sources


def test_control_does_not_retrieve_or_expose_sources(api_session):
    client, sid, _ = api_session
    with patch("api.retrieve") as retrieval, patch("api.stream_chat", return_value=iter(["OK"])):
        response = client.post("/api/chat", json={"message": "hapus dokumen ini", "session_id": sid})
    retrieval.assert_not_called()
    assert json.loads(response.headers["X-RAG-Sources"]) == []


def test_missing_evidence_is_explicit_in_prompt(api_session):
    client, sid, _ = api_session
    with patch("api.retrieve", return_value=[]), patch("api.stream_chat", return_value=iter(["Sumber belum cukup."])) as stream:
        client.post("/api/chat", json={"message": "Apa itu fotosintesis?", "session_id": sid})
    assert "jangan mengarang sitasi" in stream.call_args.kwargs["messages"][0]["content"]


def test_follow_up_retrieves_previous_question(api_session):
    client, sid, state = api_session
    state.messages = [{"role": "user", "content": "Apa itu fotosintesis?"}, {"role": "assistant", "content": "Jawaban sebelumnya"}]
    with patch("api.retrieve", return_value=[]) as retrieval, patch("api.stream_chat", return_value=iter(["Jawaban"])):
        client.post("/api/chat", json={"message": "lanjut", "session_id": sid})
    assert "fotosintesis" in retrieval.call_args.args[0]


def test_mode_switch_drops_quiz_state_and_summary_has_instructions(api_session):
    client, sid, state = api_session
    state.current_context = "quiz"
    state.last_question = "Soal lama"
    with patch("api.retrieve", return_value=[]), patch("api.stream_chat", return_value=iter(["Ringkasan"])) as stream:
        client.post("/api/chat", json={"message": "Ringkas dokumen", "session_id": sid, "mode": "rangkuman"})
    assert state.current_context == "summary"
    assert state.last_question == ""
    assert "Buat rangkuman terstruktur" in stream.call_args.kwargs["messages"][0]["content"]


def test_history_budget_keeps_recent_turns(api_session):
    client, sid, state = api_session
    state.doc_chunks = []
    state.messages = [{"role": role, "content": f"{i}:" + "x" * 2000} for i in range(20) for role in ["user", "assistant"]]
    with patch("api.stream_chat", return_value=iter(["Jawaban"])) as stream:
        client.post("/api/chat", json={"message": "Pertanyaan baru", "session_id": sid})
    messages = stream.call_args.kwargs["messages"]
    assert sum(len(m["content"]) for m in messages[1:-1]) <= 16000
    assert messages[1]["role"] == "user"
    assert messages[-2]["content"].startswith("19:")


@pytest.mark.parametrize("path,payload", [
    ("/api/quiz", None),
    ("/api/mindmap/generate", {"topic": "Fotosintesis"}),
    ("/api/mindmap/expand", {"topic": "Fotosintesis", "node_id": "1", "node_label": "Cahaya", "existing_nodes": [], "existing_edges": []}),
])
@pytest.mark.parametrize("failure", ["provider", "invalid_json"])
def test_generation_failure_returns_error_not_fabricated_content(path, payload, failure):
    with patch("api.persist_session"), patch("api.chat", side_effect=RuntimeError("offline") if failure == "provider" else None, return_value="not json"):
        client = TestClient(app)
        response = client.get(path) if payload is None else client.post(path, json=payload)
    assert response.status_code == 503
    assert "detail" in response.json()
    assert "question" not in response.json()
    assert "nodes" not in response.json()


def test_in_chat_quiz_followup_preserves_question(api_session):
    client, sid, state = api_session
    state.doc_chunks = []
    with patch("api.stream_chat", side_effect=[iter(["Soal fotosintesis"]), iter(["Petunjuk"])]) as stream:
        client.post("/api/chat", json={"message": "Buat kuis fotosintesis", "session_id": sid, "mode": "belajar"})
        question = state.last_question
        assert state.current_context == "quiz"
        client.post("/api/chat", json={"message": "hint", "session_id": sid, "mode": "belajar"})
    assert question in stream.call_args.kwargs["messages"][-1]["content"]


def test_explicit_return_to_learning_clears_quiz_followup(api_session):
    client, sid, state = api_session
    state.active_mode = "latihan"
    state.current_context = "quiz"
    state.last_question = "Soal sebelumnya"
    with patch("api.retrieve", return_value=[]), patch("api.stream_chat", return_value=iter(["Penjelasan"])) as stream:
        client.post("/api/chat", json={"message": "jelaskan", "session_id": sid, "mode": "belajar"})
    assert state.current_context == ""
    assert stream.call_args.kwargs["messages"][-1]["content"] == "jelaskan"
