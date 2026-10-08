"""Serverless regressions: cold instances, conflicts, and unavailable shared quota."""
import copy
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
import api
from storage import shared_store


@pytest.fixture
def shared_client(monkeypatch):
    rows = {}
    def load(sid):
        return copy.deepcopy(rows.get(sid))
    def save(sid, payload, revision):
        existing = rows.get(sid)
        if (existing and existing["revision"] != revision) or (not existing and revision != 0):
            raise HTTPException(409, "Sesi berubah di permintaan lain.")
        rows[sid] = {"payload": copy.deepcopy(payload), "revision": revision + 1}
        return revision + 1
    monkeypatch.setattr(api, "SHARED_STORAGE", True)
    monkeypatch.setattr(api, "DEMO_REQUESTS_PER_MINUTE", 10)
    monkeypatch.setattr(api, "DEMO_REQUESTS_PER_DAY", 100)
    monkeypatch.setattr(api.shared_store, "load", load)
    monkeypatch.setattr(api.shared_store, "save", save)
    monkeypatch.setattr(api.shared_store, "quota", lambda *args: 0)
    return TestClient(api.app), rows


def test_document_survives_cold_instance_and_search(shared_client):
    client, rows = shared_client
    response = client.post("/api/upload", data={"session_id": "serverless-test"},
        files={"file": ("materi.txt", b"Fotosintesis menggunakan energi cahaya untuk menghasilkan glukosa.", "text/plain")})
    assert response.status_code == 200
    api.SESSIONS.clear()
    details = client.get("/api/session/serverless-test").json()
    assert details["doc_chunks_count"] > 0
    assert details["uploaded_docs"][0]["filename"] == "materi.txt"
    found = client.get("/api/session/serverless-test/search-doc",
        params={"query": "fotosintesis", "filename": "materi.txt"})
    assert found.status_code == 200 and found.json()["results"]
    assert len(rows) == 1


def test_mode_and_followup_memory_survive_instance_change(shared_client):
    _, _ = shared_client
    sid, state = api.get_or_create_session("followup-test")
    state.active_mode = "latihan"
    state.current_context = "quiz"
    state.last_question = "Apa itu fotosintesis?"
    state.last_answer = "Konversi energi cahaya."
    api.persist_session(sid, state)
    _, restored = api.get_or_create_session(sid)
    assert restored is not state
    assert (restored.active_mode, restored.current_context, restored.last_answer) == (
        "latihan", "quiz", "Konversi energi cahaya.")


def test_concurrent_save_never_overwrites_newer_revision(shared_client):
    _, rows = shared_client
    sid, first = api.get_or_create_session("conflict-test")
    _, stale = api.get_or_create_session(sid)
    first.topics_discussed.append("biologi")
    api.persist_session(sid, first)
    stale.topics_discussed.append("fisika")
    with pytest.raises(HTTPException) as error:
        api.persist_session(sid, stale)
    assert error.value.status_code == 409
    assert rows[sid]["payload"]["topics_discussed"] == ["biologi"]


def test_shared_quota_blocks_even_with_empty_local_counters(shared_client, monkeypatch):
    client, _ = shared_client
    monkeypatch.setattr(api.shared_store, "quota", lambda *args: 90)
    api.DEMO_REQUEST_TIMES.clear()
    response = client.get("/api/quiz", headers={"Origin": api.allowed_origins[0]})
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "90"
    assert response.headers["Access-Control-Allow-Origin"] == api.allowed_origins[0]
    assert client.get("/api/health").status_code == 200


def test_storage_outage_does_not_use_local_quota(shared_client, monkeypatch):
    client, _ = shared_client
    def fail(*args):
        raise HTTPException(503, "Penyimpanan demo sedang tidak tersedia.")
    monkeypatch.setattr(api.shared_store, "quota", fail)
    response = client.post("/api/upload", headers={"Origin": api.allowed_origins[0]})
    assert response.status_code == 503
    assert response.headers["Access-Control-Allow-Origin"] == api.allowed_origins[0]


def test_rpc_conflict_is_explicit(monkeypatch):
    monkeypatch.setattr(shared_store, "rpc", lambda *args: None)
    with pytest.raises(HTTPException) as error:
        shared_store.save("test", {}, 1)
    assert error.value.status_code == 409
