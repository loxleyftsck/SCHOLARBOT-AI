"""Lightweight Cosine Similarity NumPy Semantic Search Service.

Uses standard NumPy operations for cosine similarity and a free, public Hugging Face
inference embedding API (all-MiniLM-L6-v2) for zero-dependency dense vector generation,
with a robust fallback to keyword-based retrieval if offline or Hugging Face rate limits apply.
"""

import httpx
import numpy as np
from typing import List, Optional
from services.retriever import RetrievedChunk, retrieve as keyword_retrieve
from services.chunker import Chunk

HF_EMBED_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings_batch(texts: List[str]) -> Optional[List[List[float]]]:
    """Fetch embeddings in a single batch from the free Hugging Face API.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding float vectors, or None if error/offline
    """
    if not texts:
        return []
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(
                HF_EMBED_URL,
                json={"inputs": texts, "options": {"wait_for_model": True}}
            )
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result
            print(f"[Semantic Search] HF Inference API Status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Semantic Search Info] Hugging Face offline / timeout: {e}")
    return None


def compute_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two vector lists using NumPy.

    Args:
        v1: First vector float list
        v2: Second vector float list

    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    arr1 = np.array(v1)
    arr2 = np.array(v2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    # Map score range cleanly from [-1, 1] to [0, 1] for relevance indicators
    similarity = float(np.dot(arr1, arr2) / (norm1 * norm2))
    return max(0.0, (similarity + 1.0) / 2.0)


def hybrid_retrieve(query: str, chunks: List[Chunk], top_k: int = 3) -> List[RetrievedChunk]:
    """Perform hybrid retrieval: semantic search (via Cosine Similarity NumPy) with keyword fallback.

    Ensures 100% stability and zero-dependencies while providing dense semantic search power.

    Args:
        query: User query/question
        chunks: List of Chunk objects from session
        top_k: Number of chunks to retrieve

    Returns:
        List of RetrievedChunk objects, balanced across documents via round-robin
    """
    if not query or not chunks:
        return []

    # 1. Check if we need to generate embeddings for any chunks
    chunks_without_embeddings = [c for c in chunks if not getattr(c, "embedding", None)]
    
    if chunks_without_embeddings:
        print(f"[Semantic Search] Menghasilkan embedding untuk {len(chunks_without_embeddings)} potongan teks baru...")
        texts_to_embed = [c.content for c in chunks_without_embeddings]
        
        # Batch get embeddings
        embeddings = get_embeddings_batch(texts_to_embed)
        if embeddings and len(embeddings) == len(chunks_without_embeddings):
            for i, chunk in enumerate(chunks_without_embeddings):
                chunk.embedding = embeddings[i]
            print("[Semantic Search] Caching embedding berhasil!")
        else:
            print("[Semantic Search Fallback] Peringatan: API embedding offline. Beralih ke Keyword Search.")
            return keyword_retrieve(query, chunks, top_k=top_k)

    # 2. Get Query Embedding
    query_emb_list = get_embeddings_batch([query])
    if not query_emb_list or len(query_emb_list) == 0:
        print("[Semantic Search Fallback] Gagal mengambil embedding kueri. Beralih ke Keyword Search.")
        return keyword_retrieve(query, chunks, top_k=top_k)
    
    query_emb = query_emb_list[0]

    # 3. Calculate Cosine Similarity & group by document source
    scored_by_doc = {}
    for chunk in chunks:
        if not getattr(chunk, "embedding", None):
            continue
        
        score = compute_cosine_similarity(query_emb, chunk.embedding)
        retrieved = RetrievedChunk(
            content=chunk.content,
            score=score,
            source_filename=chunk.source_filename,
            chunk_index=chunk.chunk_index,
        )
        
        doc_name = retrieved.source_filename
        if doc_name not in scored_by_doc:
            scored_by_doc[doc_name] = []
        scored_by_doc[doc_name].append(retrieved)

    # 4. Sort chunks in each document by score descending
    for doc in scored_by_doc:
        scored_by_doc[doc].sort(key=lambda r: r.score, reverse=True)

    # 5. Diversified Round-Robin Merging across documents to prevent source starvation
    diversified_results = []
    
    # Sort docs by their single best matching chunk score
    doc_keys_sorted = sorted(
        scored_by_doc.keys(),
        key=lambda d: scored_by_doc[d][0].score if scored_by_doc[d] else 0.0,
        reverse=True
    )

    chunk_index_pointers = {doc: 0 for doc in doc_keys_sorted}
    
    while len(diversified_results) < top_k:
        added_in_round = False
        for doc in doc_keys_sorted:
            ptr = chunk_index_pointers[doc]
            if ptr < len(scored_by_doc[doc]):
                diversified_results.append(scored_by_doc[doc][ptr])
                chunk_index_pointers[doc] += 1
                added_in_round = True
                if len(diversified_results) >= top_k:
                    break
        if not added_in_round:
            break

    return diversified_results
