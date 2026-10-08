"""Simple text chunking — paragraph-based and fixed-size.

Lightweight approach: NO embeddings, NO vector DB.
Uses keyword overlap scoring for relevance ranking.

Chunking strategies:
1. paragraph: split by double newlines (best for structured docs)
2. fixed-size: split by character count with overlap (best for long dense text)

No external dependencies beyond Python stdlib.
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    """A single text chunk with metadata."""
    content: str
    chunk_index: int
    source_filename: str
    embedding: list[float] = None
    embedding_cache_key: str | None = None

    def __getitem__(self, key):
        if key == "source" or key == "source_filename":
            return self.source_filename
        elif key == "content":
            return self.content
        elif key == "index" or key == "chunk_index":
            return self.chunk_index
        elif key == "embedding":
            return self.embedding
        raise KeyError(key)

    def __repr__(self) -> str:
        preview = self.content[:80].replace('\n', ' ').strip()
        return f"Chunk {self.chunk_index}: {preview}..."


def chunk_by_paragraph(text: str, min_chars: int = 100, max_chars: int = 800) -> list[Chunk]:
    """Keep short paragraphs by grouping them; split any overlong group."""
    if not text or not text.strip():
        return []
    chunks = []
    pending = ""
    for paragraph in text.split('\n\n'):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        pending = f"{pending}\n\n{paragraph}" if pending else paragraph
        if len(pending) >= min_chars:
            chunks.extend(chunk_by_size(pending, max_chars))
            pending = ""
    if pending:
        chunks.extend(chunk_by_size(pending, max_chars))
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i
    return chunks

def chunk_by_size(text: str, chunk_size: int = 800, overlap: int = 150) -> list[Chunk]:
    """Bounded overlapping chunks, preserving short documents and trailing text."""
    if chunk_size <= 0 or overlap < 0:
        raise ValueError("chunk_size must be positive and overlap non-negative")
    if not text or not text.strip():
        return []
    text = text.strip()
    overlap = min(overlap, chunk_size // 4)
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            segment = text[start:end]
            boundary = max(segment.rfind('. '), segment.rfind(', '), segment.rfind(';\n'))
            if boundary >= max(len(segment) - 100, len(segment) // 2):
                end = start + boundary + 2
        content = text[start:end].strip()
        if content:
            chunks.append(Chunk(content, len(chunks), ""))
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks

def chunk_semantically(text: str, filename: str = "", max_chunk_chars: int = 1000) -> list[Chunk]:
    """Split text into chunks semantically using adaptive sentence similarity.

    Falls back to paragraph chunking if offline or API error occurs.

    Args:
        text: Full document text
        filename: Source filename
        max_chunk_chars: Hard limit for chunk length

    Returns:
        List of Chunk objects
    """
    import re
    import numpy as np
    from services.semantic_search import get_embeddings_batch, compute_cosine_similarity

    if not text or not text.strip():
        return []

    # 1. Split text into sentences
    sentence_list = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if not sentence_list:
        return []

    if len(sentence_list) <= 3:
        chunks = chunk_by_size(text, max_chunk_chars)
        for chunk in chunks:
            chunk.source_filename = filename
        return chunks

    # Limit units to avoid Hugging Face payload size or rate limits
    if len(sentence_list) > 100:
        grouped_sentences = []
        current_group = []
        for s in sentence_list:
            current_group.append(s)
            if len(current_group) >= 3:
                grouped_sentences.append(" ".join(current_group))
                current_group = []
        if current_group:
            grouped_sentences.append(" ".join(current_group))
        units = grouped_sentences
    else:
        units = sentence_list

    # Oversized sentences must also respect the hard limit before embedding.
    units = [part.content for unit in units for part in chunk_by_size(unit, max_chunk_chars)]

    # 2. Get embeddings in one batch
    embeddings = get_embeddings_batch(units)
    if not embeddings or len(embeddings) != len(units):
        print("[Semantic Chunking Fallback] Gagal mengambil embedding. Menggunakan paragraph chunking.")
        fallback_chunks = chunk_by_paragraph(text, max_chars=max_chunk_chars)
        for c in fallback_chunks:
            c.source_filename = filename
        return fallback_chunks

    # 3. Calculate similarity between consecutive units
    similarities = []
    for i in range(len(units) - 1):
        sim = compute_cosine_similarity(embeddings[i], embeddings[i+1])
        similarities.append(sim)

    # 4. Adaptive thresholding using the 25th percentile (bottom 25% similar transitions split)
    threshold = float(np.percentile(similarities, 25)) if similarities else 0.65
    threshold = max(0.55, min(0.75, threshold))  # Clamp to reasonable bounds

    # 5. Group into chunks based on semantic split decisions
    chunks = []
    current_chunk_units = [units[0]]
    current_chunk_emb = [embeddings[0]]
    chunk_index = 0

    for i in range(1, len(units)):
        sim = similarities[i-1]
        current_len = len(" ".join(current_chunk_units)) + 1

        # Split condition: similarity drops below threshold or max character limit is breached
        if sim < threshold or current_len + len(units[i]) > max_chunk_chars:
            chunk_content = " ".join(current_chunk_units)
            avg_emb = np.mean(current_chunk_emb, axis=0).tolist() if current_chunk_emb else None
            
            chunks.append(Chunk(
                content=chunk_content,
                chunk_index=chunk_index,
                source_filename=filename,
                embedding=avg_emb
            ))
            chunk_index += 1
            current_chunk_units = [units[i]]
            current_chunk_emb = [embeddings[i]]
        else:
            current_chunk_units.append(units[i])
            current_chunk_emb.append(embeddings[i])

    # Append trailing chunk
    if current_chunk_units:
        chunk_content = " ".join(current_chunk_units)
        avg_emb = np.mean(current_chunk_emb, axis=0).tolist() if current_chunk_emb else None
        chunks.append(Chunk(
            content=chunk_content,
            chunk_index=chunk_index,
            source_filename=filename,
            embedding=avg_emb
        ))

    return chunks


def chunk_text(text: str, strategy: str = "auto", filename: str = "", max_chars: int = 800) -> list[Chunk]:
    """Unified chunking interface with auto strategy selection.

    Strategy selection:
    - "paragraph": for text with clear paragraph breaks
    - "size": for dense long-form text
    - "semantic": for semantic boundary-based chunking
    - "auto": automatically detect best strategy based on content size

    Args:
        text: Full document text
        strategy: "paragraph" | "size" | "semantic" | "auto"
        filename: Source filename (stored in Chunk metadata)
        max_chars: Maximum characters per chunk (used by size strategy)

    Returns:
        List of Chunk objects with source_filename set
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if not text:
        return []

    paragraph_count = text.count('\n\n')
    has_clear_structure = paragraph_count >= 3

    if strategy == "auto":
        # Moderate size documents default to high-quality semantic chunking
        if len(text) < 50000:
            strategy = "semantic"
        elif len(text) < 1000 or has_clear_structure:
            strategy = "paragraph"
        else:
            strategy = "size"

    if strategy == "semantic":
        raw_chunks = chunk_semantically(text, filename, max_chunk_chars=max_chars)
        if not raw_chunks and text.strip():
            raw_chunks = [Chunk(content=text.strip(), chunk_index=0, source_filename="")]
    elif strategy == "paragraph":
        raw_chunks = chunk_by_paragraph(text, max_chars=max_chars)
        if not raw_chunks and text.strip():
            raw_chunks = [Chunk(content=text.strip(), chunk_index=0, source_filename="")]
    else:
        raw_chunks = chunk_by_size(text, chunk_size=max_chars)
        if not raw_chunks and text.strip():
            raw_chunks = [Chunk(content=text.strip(), chunk_index=0, source_filename="")]

    # Enforce the limit on every path, including emergency fallbacks.
    bounded = []
    for chunk in raw_chunks:
        if len(chunk.content) <= max_chars:
            bounded.append(chunk)
        else:
            bounded.extend(chunk_by_size(chunk.content, max_chars))
    raw_chunks = bounded
    for i, chunk in enumerate(raw_chunks):
        chunk.chunk_index = i

    # Attach filename to all chunks
    for chunk in raw_chunks:
        chunk.source_filename = filename

    return raw_chunks


def get_chunk_preview(chunks: list[Chunk], max_chars: int = 150) -> str:
    """Build a preview string from first few chunks.

    Args:
        chunks: List of Chunk objects
        max_chars: Max characters per chunk in preview

    Returns:
        Concatenated preview string
    """
    if not chunks:
        return ""

    previews = []
    total = 0
    for chunk in chunks[:5]:  # Max 5 chunks in preview
        if total >= 400:
            break
        text = chunk.content[:max_chars].replace('\n', ' ')
        previews.append(text)
        total += len(text)

    return " | ".join(previews)
