"""Validated dense retrieval with explicit keyword fallback.

The legacy function name hybrid_retrieve is retained for callers. BM25 is the
pilot-selected default; optional dense uses explicit keyword fallback. This is
not BM25 fusion. Fusion remains an evaluation candidate. No vector is trusted without model and content identity.
"""
import hashlib
import logging
import os
from contextvars import ContextVar
from typing import List, Optional
import httpx
import numpy as np
from services.retriever import RetrievedChunk, retrieve as keyword_retrieve
from services.ranking import bm25_retrieve

logger = logging.getLogger(__name__)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_REVISION = os.getenv("EMBEDDING_REVISION", "provider-managed")
HF_EMBED_URL = os.getenv("EMBEDDING_URL", "https://router.huggingface.co/hf-inference/models/" + EMBEDDING_MODEL)
_status = ContextVar("retrieval_status", default=None)

def embedding_identity():
    return (EMBEDDING_MODEL, EMBEDDING_REVISION, HF_EMBED_URL, "e5-prefix-v1" if "e5" in EMBEDDING_MODEL.lower() else "plain-v1")

def embedding_cache_key(text):
    return hashlib.sha256(repr(embedding_identity()).encode() + text.encode("utf-8")).hexdigest()

def validate_embeddings(result, count, dimension=None):
    try:
        matrix = np.asarray(result, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] != count or matrix.shape[1] == 0:
            return None
        if dimension is not None and matrix.shape[1] != dimension:
            return None
        if not np.isfinite(matrix).all() or np.any(np.linalg.norm(matrix, axis=1) == 0):
            return None
        return matrix.tolist()
    except (TypeError, ValueError, OverflowError):
        return None

def get_embeddings_batch(texts: List[str], purpose="passage") -> Optional[List[List[float]]]:
    if not texts:
        return []
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
    if not token and not os.getenv("EMBEDDING_URL"):
        return None
    inputs = [("query: " if purpose == "query" else "passage: ") + t for t in texts] if "e5" in EMBEDDING_MODEL.lower() else texts
    headers = {"Authorization": "Bearer " + token} if token else {}
    vectors = []
    configured_dimension = os.getenv("EMBEDDING_DIMENSION")
    dimension = int(configured_dimension) if configured_dimension else (384 if EMBEDDING_MODEL in {"sentence-transformers/all-MiniLM-L6-v2", "intfloat/multilingual-e5-small"} else None)
    try:
        with httpx.Client(timeout=8.0) as client:
            for start in range(0, len(inputs), 32):
                batch = inputs[start:start + 32]
                response = client.post(HF_EMBED_URL, headers=headers, json={"inputs": batch, "normalize": True, "truncate": True})
                if response.status_code != 200:
                    logger.warning("Embedding provider returned HTTP %s", response.status_code)
                    return None
                valid = validate_embeddings(response.json(), len(batch), dimension)
                if valid is None:
                    logger.warning("Embedding provider returned invalid vectors")
                    return None
                dimension = len(valid[0])
                vectors.extend(valid)
        return vectors
    except (httpx.HTTPError, ValueError):
        logger.warning("Embedding provider unavailable or invalid response")
        return None

def compute_cosine_similarity(v1, v2):
    """Legacy mapped cosine for semantic chunk boundary thresholds."""
    valid = validate_embeddings([v1, v2], 2)
    if valid is None:
        return 0.0
    a, b = np.asarray(valid)
    cosine = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    return float(np.clip((cosine + 1) / 2, 0, 1))

def dense_rank(query_vector, chunks, vectors, top_k=5, min_cosine=0.0):
    valid = validate_embeddings(vectors, len(chunks))
    q = validate_embeddings([query_vector], 1, len(valid[0]) if valid else None)
    if not valid or not q:
        raise ValueError("Invalid or incompatible dense vectors")
    matrix = np.asarray(valid); query = np.asarray(q[0])
    scores = matrix @ query / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(query))
    results = [RetrievedChunk(c.content, float(s), c.source_filename, c.chunk_index) for c, s in zip(chunks, scores) if s >= min_cosine]
    # Relevance threshold applied before ranking; no forced low-relevance document diversity.
    return sorted(results, key=lambda c: (-c.score, c.source_filename, c.chunk_index))[:max(0, top_k)]

def get_retrieval_status():
    return _status.get() or {"method": "not_run", "fallback": False}

def hybrid_retrieve(query, chunks, top_k=3):
    _status.set({"method": "not_run", "fallback": False})
    if not query or not chunks or top_k <= 0:
        return []
    method = os.getenv("RETRIEVAL_METHOD", "bm25").lower()
    if method in {"keyword", "bm25"}:
        _status.set({"method": method, "fallback": False})
        return (bm25_retrieve if method == "bm25" else keyword_retrieve)(query, chunks, top_k=top_k)
    if method != "dense":
        raise ValueError("RETRIEVAL_METHOD must be bm25, keyword or dense")
    def fallback(reason):
        _status.set({"method": "keyword", "fallback": True, "reason": reason})
        logger.info("Retrieval fallback: %s", reason)
        return keyword_retrieve(query, chunks, top_k=top_k)
    missing = [c for c in chunks if getattr(c, "embedding_cache_key", None) != embedding_cache_key(c.content) or validate_embeddings([getattr(c, "embedding", None)], 1) is None]
    if missing:
        embeddings = get_embeddings_batch([c.content for c in missing])
        valid = validate_embeddings(embeddings, len(missing))
        if valid is None:
            return fallback("passage_embeddings_unavailable_or_invalid")
        for chunk, vector in zip(missing, valid):
            chunk.embedding = vector
            chunk.embedding_cache_key = embedding_cache_key(chunk.content)
    query_vectors = get_embeddings_batch([query], purpose="query")
    if validate_embeddings(query_vectors, 1) is None:
        return fallback("query_embedding_unavailable_or_invalid")
    try:
        results = dense_rank(query_vectors[0], chunks, [c.embedding for c in chunks], top_k)
    except ValueError:
        return fallback("embedding_dimension_mismatch")
    _status.set({"method": "dense", "fallback": False, "model": EMBEDDING_MODEL, "revision": EMBEDDING_REVISION})
    return results
