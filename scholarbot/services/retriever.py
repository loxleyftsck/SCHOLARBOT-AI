"""Lightweight keyword-based retrieval — NO embeddings, NO vector DB.

Uses simple keyword overlap scoring + TF-based ranking.
Fast, deterministic, explainable — perfect for educational RAG.

Scoring logic:
1. Token overlap: count query words in chunk
2. TF boost: chunks with repeated query terms score higher
3. Length penalty: prefer concise chunks with high density
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class RetrievedChunk:
    """A retrieved chunk with relevance score."""
    content: str
    score: float
    source_filename: str
    chunk_index: int

    def __repr__(self) -> str:
        preview = self.content[:80].replace('\n', ' ').strip()
        return f"[score={self.score:.2f}] {preview}..."


def tokenize(text: str) -> set[str]:
    """Simple tokenizer: lowercase + remove punctuation + split.

    Args:
        text: Input string

    Returns:
        Set of unique tokens
    """
    # Remove punctuation, lowercase, split
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    tokens = text.split()
    # Remove very short tokens (noise)
    return {t for t in tokens if len(t) >= 3}


def compute_relevance_score(query: str, chunk_content: str) -> float:
    """Compute relevance score using keyword overlap.

    Simple but effective:
    - More query words in chunk = higher score
    - Repeated query words = higher score (TF boost)
    - Concise chunks with high density = higher score

    Args:
        query: User query string
        chunk_content: Chunk text to score

    Returns:
        Relevance score (0.0 to 1.0+)
    """
    query_tokens = tokenize(query)
    chunk_tokens = tokenize(chunk_content)

    if not query_tokens:
        return 0.0

    # Token overlap (query words in chunk)
    overlap = query_tokens.intersection(chunk_tokens)
    overlap_score = len(overlap) / len(query_tokens)

    # TF boost: count term frequency in chunk
    chunk_text_lower = chunk_content.lower()
    tf_sum = sum(chunk_text_lower.count(t) for t in query_tokens)
    tf_score = tf_sum / len(chunk_tokens) if chunk_tokens else 0

    # Length penalty: prefer concise chunks (higher density)
    length_factor = min(1.0, 500 / len(chunk_content)) if chunk_content else 0

    # Combined score with TF boost
    score = (overlap_score * 2.0) + (tf_score * 0.5) + (length_factor * 0.2)

    return score


def retrieve(query: str, chunks: List, top_k: int = 3, min_score: float = 0.1) -> List[RetrievedChunk]:
    """Retrieve top-k most relevant chunks for query with cross-document round-robin balancing.

    Prevents source starvation by ensuring diverse context is selected from multiple
    different documents if available.

    Args:
        query: User query/question
        chunks: List of Chunk objects (from chunker)
        top_k: Number of chunks to retrieve
        min_score: Minimum relevance threshold

    Returns:
        List of RetrievedChunk objects, diversified across sources
    """
    if not query or not chunks:
        return []

    # 1. Score and collect all matching chunks
    scored_by_doc = {}
    for chunk in chunks:
        score = compute_relevance_score(query, chunk.content)
        if score >= min_score:
            retrieved = RetrievedChunk(
                content=chunk.content,
                score=score,
                source_filename=chunk.source_filename,
                chunk_index=chunk.chunk_index,
            )
            # Group by document source filename
            doc_name = retrieved.source_filename
            if doc_name not in scored_by_doc:
                scored_by_doc[doc_name] = []
            scored_by_doc[doc_name].append(retrieved)

    # 2. Sort chunks within each document by score descending
    for doc_name in scored_by_doc:
        scored_by_doc[doc_name].sort(key=lambda r: r.score, reverse=True)

    # 3. Diversified Round-Robin Merging across documents
    diversified_results = []
    
    # Sort docs by their single best-matching chunk score so the most relevant document goes first
    doc_keys_sorted = sorted(
        scored_by_doc.keys(),
        key=lambda d: scored_by_doc[d][0].score if scored_by_doc[d] else 0.0,
        reverse=True
    )

    # Keep popping chunks from documents in a round-robin fashion
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
            break  # No more chunks left in any document

    return diversified_results


def format_retrieved_context(retrieved: List[RetrievedChunk], max_chars: int = 1200) -> str:
    """Format retrieved chunks into a single context string for prompt injection.

    Args:
        retrieved: List of RetrievedChunk objects
        max_chars: Maximum total characters in context

    Returns:
        Formatted context string with citations
    """
    if not retrieved:
        return ""

    parts = []
    total = 0

    for i, chunk in enumerate(retrieved, 1):
        # Truncate chunk if needed
        chunk_text = chunk.content[:max_chars] if max_chars > 0 else chunk.content
        citation = f"[Dokumen {i}: {chunk.source_filename}]"

        parts.append(f"{citation}\n{chunk_text}")
        total += len(chunk_text) + len(citation)

        if max_chars and total >= max_chars:
            break

    return "\n\n---\n\n".join(parts)


def has_relevant_content(query: str, chunks: List, threshold: float = 0.2) -> bool:
    """Quick check if any chunk meets relevance threshold.

    Args:
        query: User query
        chunks: List of Chunk objects
        threshold: Minimum score to consider "relevant"

    Returns:
        True if any chunk meets threshold
    """
    for chunk in chunks:
        if compute_relevance_score(query, chunk.content) >= threshold:
            return True
    return False
