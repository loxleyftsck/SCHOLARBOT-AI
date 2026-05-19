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


def chunk_text(text: str, strategy: str = "auto", filename: str = "") -> list[Chunk]:
    """Unified chunking interface with auto strategy selection.

    Strategy selection:
    - "paragraph": for text with clear paragraph breaks
    - "size": for dense long-form text
    - "auto": automatically detect best strategy based on content

    Args:
        text: Full document text
        strategy: "paragraph" | "size" | "auto"
        filename: Source filename (stored in Chunk metadata)

    Returns:
        List of Chunk objects with source_filename set
    """
    if not text:
        return []

    # Auto-detect: text with many double newlines → paragraph mode
    paragraph_count = text.count('\n\n')
    has_clear_structure = paragraph_count >= 3

    if strategy == "auto":
        # If text is short or has clear paragraphs, use paragraph mode
        if len(text) < 1000 or has_clear_structure:
            strategy = "paragraph"
        else:
            strategy = "size"

    if strategy == "paragraph":
        raw_chunks = chunk_by_paragraph(text)
        # If paragraph mode returned nothing (text too short), return full text as single chunk
        if not raw_chunks and text.strip():
            raw_chunks = [Chunk(content=text.strip(), chunk_index=0, source_filename="")]
    else:
        raw_chunks = chunk_by_size(text)
        # If size mode returns tiny fragments, return full text as single chunk
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
