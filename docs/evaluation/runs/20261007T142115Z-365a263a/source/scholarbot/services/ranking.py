"""Deterministic lexical ranking and reciprocal rank fusion; no provider calls."""
import math
import re
from collections import Counter
from services.retriever import RetrievedChunk

STOP_WORDS = set("apa apakah bagaimana mengapa di dan yang untuk dengan itu ini dari pada ke sebagai adalah berapa saya jelaskan lagi".split())

def terms(text):
    return [t for t in re.findall(r"\w+", text.lower()) if len(t) >= 3 and t not in STOP_WORDS]

def bm25_retrieve(query, chunks, top_k=5, k1=1.5, b=0.75):
    if not chunks or top_k <= 0:
        return []
    counts = [Counter(terms(c.content)) for c in chunks]
    lengths = [sum(c.values()) for c in counts]
    avg = sum(lengths) / len(lengths) or 1
    results = []
    for chunk, tf, length in zip(chunks, counts, lengths):
        score = 0.0
        for word in sorted(set(terms(query))):
            freq = tf[word]
            if not freq:
                continue
            df = sum(word in c for c in counts)
            idf = math.log(1 + (len(chunks) - df + 0.5) / (df + 0.5))
            score += idf * freq * (k1 + 1) / (freq + k1 * (1 - b + b * length / avg))
        if score > 0:
            results.append(RetrievedChunk(chunk.content, score, chunk.source_filename, chunk.chunk_index))
    return sorted(results, key=lambda c: (-c.score, c.source_filename, c.chunk_index))[:top_k]

def reciprocal_rank_fusion(rankings, top_k=5, constant=60):
    if constant <= 0:
        raise ValueError("RRF constant must be positive")
    scores, chunks = {}, {}
    for ranking in rankings:
        seen = set()
        for rank, chunk in enumerate(ranking, 1):
            key = (chunk.source_filename, chunk.chunk_index)
            if key in seen:
                continue
            seen.add(key)
            chunks[key] = chunk
            scores[key] = scores.get(key, 0.0) + 1 / (constant + rank)
    ordered = sorted(scores, key=lambda k: (-scores[k], k))[:max(0, top_k)]
    return [RetrievedChunk(chunks[k].content, scores[k], k[0], k[1]) for k in ordered]
