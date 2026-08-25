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


def chunk_by_paragraph(text: str, min_chars: int = 100) -> list[Chunk]:
    """Split text into chunks by paragraph (double newline separator).

    Best for: structured documents (notes, summaries, articles)
    Filters out short paragraphs to avoid noise.

    Args:
        text: Full document text
        min_chars: Minimum character count for a chunk to be kept

    Returns:
        List of Chunk objects
    """
    if not text or not text.strip():
        return []

    # Split by paragraph (double newline)
    paragraphs = text.split('\n\n')

    chunks = []
    for idx, para in enumerate(paragraphs):
        para = para.strip()
        # Filter: skip short paragraphs (likely headers, footers, noise)
        if len(para) >= min_chars:
            chunks.append(Chunk(content=para, chunk_index=idx, source_filename=""))

    return chunks


def chunk_by_size(text: str, chunk_size: int = 800, overlap: int = 150) -> list[Chunk]:
    """Split text into fixed-size chunks with overlap.

    Best for: dense long-form text without clear paragraph breaks.
    Overlap helps prevent context loss at chunk boundaries.

    Args:
        text: Full document text
        chunk_size: Target character count per chunk
        overlap: Character overlap between consecutive chunks

    Returns:
        List of Chunk objects
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    chunks = []
    idx = 0
    chunk_num = 0

    while idx < len(text):
        # Extract chunk with overlap padding
        chunk_end = min(idx + chunk_size, len(text))
        chunk_text = text[idx:chunk_end]

        # Try to break at sentence boundary (.) or comma for cleaner splits
        if chunk_end < len(text):
            # Look for sentence break within last 100 chars of chunk
            search_start = max(idx, chunk_end - 100)
            last_period = max(
                chunk_text.rfind('. '),
                chunk_text.rfind(', '),
                chunk_text.rfind(';\n'),
            )
            if last_period > search_start:
                # Break after punctuation
                chunk_text = chunk_text[:last_period + 2]
                chunk_end = idx + len(chunk_text)

        if len(chunk_text.strip()) < 50:
            break  # Skip tiny remnant chunks

        chunks.append(Chunk(content=chunk_text.strip(), chunk_index=chunk_num, source_filename=""))
        # Always advance forward — max ensures idx never stalls or rewinds
        idx = max(chunk_end - overlap, idx + 1)
        chunk_num += 1

        if idx >= len(text):  # Safety: prevent infinite loop
            break

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
        return [Chunk(content=text.strip(), chunk_index=0, source_filename=filename)]

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

    # 2. Get embeddings in one batch
    embeddings = get_embeddings_batch(units)
    if not embeddings or len(embeddings) != len(units):
        print("[Semantic Chunking Fallback] Gagal mengambil embedding. Menggunakan paragraph chunking.")
        fallback_chunks = chunk_by_paragraph(text)
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
        current_len = sum(len(u) for u in current_chunk_units)

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
        raw_chunks = chunk_semantically(text, filename)
        if not raw_chunks and text.strip():
            raw_chunks = [Chunk(content=text.strip(), chunk_index=0, source_filename="")]
    elif strategy == "paragraph":
        raw_chunks = chunk_by_paragraph(text)
        if not raw_chunks and text.strip():
            raw_chunks = [Chunk(content=text.strip(), chunk_index=0, source_filename="")]
    else:
        raw_chunks = chunk_by_size(text, chunk_size=max_chars)
        if not raw_chunks and text.strip():
            raw_chunks = [Chunk(content=text.strip(), chunk_index=0, source_filename="")]

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
