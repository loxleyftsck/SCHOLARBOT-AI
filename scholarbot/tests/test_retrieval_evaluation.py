"""Ranking, vector validation, cache invalidation and API fallback contracts."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
from fastapi.testclient import TestClient
from services.chunker import Chunk
from services.ranking import bm25_retrieve, reciprocal_rank_fusion
from services.retriever import RetrievedChunk
from services import semantic_search as semantic
from api import app, SESSIONS, SessionState

@pytest.mark.parametrize("vectors", [None, [], [[1,2],[1]], [[[1,2]]], [[0,0]], [[float("nan"),1]], [[float("inf"),1]], ["bad"]])
def test_invalid_provider_vectors_rejected(vectors):
    assert semantic.validate_embeddings(vectors, 1) is None

def test_dimension_and_batch_count_validation():
    assert semantic.validate_embeddings([[1,2]], 2) is None
    assert semantic.validate_embeddings([[1,2]], 1, 384) is None
    assert semantic.validate_embeddings([[1,2]], 1, 2) == [[1,2]]

def test_bm25_ignores_question_stopwords_and_irrelevant_documents():
    chunks = [Chunk("materi biologi tentang klorofil",0,"bio"),Chunk("TCP mengirim ulang paket hilang",0,"tcp")]
    results = bm25_retrieve("Apa yang dilakukan TCP?",chunks)
    assert [c.source_filename for c in results] == ["tcp"]
    assert bm25_retrieve("apa itu",chunks) == []

def test_dense_filters_before_ranking_and_rejects_incompatible_dimensions():
    chunks = [Chunk("a",0,"a"),Chunk("b",0,"b")]
    assert [c.source_filename for c in semantic.dense_rank([1,0],chunks,[[1,0],[-1,0]],min_cosine=0.2)] == ["a"]
    with pytest.raises(ValueError): semantic.dense_rank([1,0,0],chunks,[[1,0],[0,1]])

def test_rrf_deduplicates_and_combines_ranks_not_raw_scores():
    a = RetrievedChunk("A",1000,"a",0); b = RetrievedChunk("B",0.001,"b",0)
    out = reciprocal_rank_fusion([[a,a,b],[b,a]])
    assert len(out)==2
    assert all(c.score < 1 for c in out)
    assert reciprocal_rank_fusion([[a]],top_k=0)==[]

def test_dense_cache_is_invalidated_by_content_or_model(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_METHOD","dense")
    chunk=Chunk("TCP paket",0,"tcp")
    with patch.object(semantic,"get_embeddings_batch",return_value=[[1,0]]) as provider:
        semantic.hybrid_retrieve("TCP",[chunk]); assert provider.call_count==2
        provider.reset_mock(); semantic.hybrid_retrieve("TCP",[chunk]); assert provider.call_count==1
        chunk.content="UDP paket"; provider.reset_mock();semantic.hybrid_retrieve("UDP",[chunk]); assert provider.call_count==2
        monkeypatch.setattr(semantic,"EMBEDDING_MODEL","another-model");provider.reset_mock();semantic.hybrid_retrieve("UDP",[chunk]);assert provider.call_count==2

def test_dense_unknown_cache_and_invalid_query_use_explicit_fallback(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_METHOD","dense")
    chunk=Chunk("TCP paket",0,"tcp",embedding=[1,0])
    with patch.object(semantic,"get_embeddings_batch",side_effect=[[[1,0]],[[1,2,3]]]):
        results=semantic.hybrid_retrieve("TCP",[chunk])
    assert results
    assert semantic.get_retrieval_status()=={"method":"keyword","fallback":True,"reason":"embedding_dimension_mismatch"}

def test_default_bm25_has_no_embedding_provider_calls(monkeypatch):
    monkeypatch.delenv("RETRIEVAL_METHOD",raising=False)
    with patch.object(semantic,"get_embeddings_batch") as provider:
        assert semantic.hybrid_retrieve("TCP",[Chunk("TCP paket",0,"tcp")])
    provider.assert_not_called()
    assert semantic.get_retrieval_status()=={"method":"bm25","fallback":False}

def test_search_document_fallback_returns_consistent_object(monkeypatch):
    import uuid
    monkeypatch.setenv("RETRIEVAL_METHOD","dense")
    sid=str(uuid.uuid4());state=SessionState();state.doc_chunks=[Chunk("TCP mengirim ulang paket hilang",0,"tcp.txt")];SESSIONS[sid]=state
    try:
        with patch("api.persist_session"),patch.object(semantic,"get_embeddings_batch",return_value=None):
            response=TestClient(app).get(f"/api/session/{sid}/search-doc",params={"query":"TCP paket","filename":"tcp.txt"})
        payload=response.json();assert payload["results"]
        assert payload["retrieval_status"]["fallback"] is True
    finally:SESSIONS.pop(sid,None)

def test_chat_records_and_exposes_fallback_then_clears_on_control(monkeypatch):
    import uuid
    monkeypatch.setenv("RETRIEVAL_METHOD","dense")
    sid=str(uuid.uuid4());state=SessionState();state.doc_chunks=[Chunk("TCP mengirim ulang paket hilang",0,"tcp.txt")];SESSIONS[sid]=state
    try:
        with patch("api.persist_session"),patch.object(semantic,"get_embeddings_batch",return_value=None),patch("api.stream_chat",side_effect=lambda **kw:iter(["Jawaban [1]"])):
            client=TestClient(app); response=client.post("/api/chat",json={"session_id":sid,"message":"Bagaimana TCP bekerja?"})
            assert json.loads(response.headers["X-Retrieval-Status"])["fallback"] is True
            assert state.messages[-1]["retrieval_status"]["fallback"] is True
            response=client.post("/api/chat",json={"session_id":sid,"message":"hapus dokumen ini"})
            assert json.loads(response.headers["X-Retrieval-Status"])["method"]=="not_run"
    finally:SESSIONS.pop(sid,None)

def test_pilot_has_fifty_labels_and_no_group_leakage():
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location("evaluation",root/"scripts/evaluate_retrieval.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data=json.loads((root/"docs/evaluation/dataset.json").read_text(encoding="utf-8"));module.validate_dataset(data)
    assert len(data["questions"])==50
    assert {c:sum(q["category"]==c for q in data["questions"]) for c in ["direct","paraphrase","multi_document","follow_up","no_answer"]}=={"direct":15,"paraphrase":10,"multi_document":10,"follow_up":5,"no_answer":10}
    bad=json.loads(json.dumps(data));bad["questions"][-1]["group"]=bad["questions"][0]["group"]
    with pytest.raises(ValueError):module.validate_dataset(bad)


def test_model_key_survives_save_load(monkeypatch,tmp_path):
    from storage import json_store
    monkeypatch.setattr(json_store,"_SESSIONS_DIR",tmp_path/"sessions")
    monkeypatch.setattr(json_store,"_PROFILES_DIR",tmp_path/"profiles")
    chunk=Chunk("TCP paket",0,"tcp",[1,0],semantic.embedding_cache_key("TCP paket"))
    assert json_store.save_session("cache-test",{"doc_chunks":[chunk]})
    restored=json_store.load_session("cache-test")["doc_chunks"][0]
    assert restored.embedding_cache_key==chunk.embedding_cache_key
    assert restored.embedding==[1,0]


def test_provider_prefix_and_fixed_model_dimension(monkeypatch):
    monkeypatch.setenv("HF_TOKEN","synthetic-test-token")
    monkeypatch.setattr(semantic,"EMBEDDING_MODEL","intfloat/multilingual-e5-small")
    with patch.object(semantic.httpx,"Client") as client:
        response=client.return_value.__enter__.return_value.post.return_value
        response.status_code=200;response.json.return_value=[[1.0]*384]
        assert semantic.get_embeddings_batch(["materi"],purpose="query")
        assert client.return_value.__enter__.return_value.post.call_args.kwargs["json"]["inputs"]==["query: materi"]
        response.json.return_value=[[1.0,2.0]]
        assert semantic.get_embeddings_batch(["materi"]) is None
