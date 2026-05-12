"""Services module — business logic services for specialized AI features.

Phase v3: RAG pipeline (document_loader, chunker, retriever).
No heavy frameworks — lightweight, educational RAG implementation.
"""

from .document_loader import (
    extract_txt,
    extract_pdf,
    extract_document,
    get_document_info,
)
from .chunker import (
    Chunk,
    chunk_by_paragraph,
    chunk_by_size,
    chunk_text,
    get_chunk_preview,
)
from .retriever import (
    RetrievedChunk,
    retrieve,
    compute_relevance_score,
    format_retrieved_context,
    has_relevant_content,
)

__all__ = [
    # Document loader
    "extract_txt", "extract_pdf", "extract_document", "get_document_info",
    # Chunker
    "Chunk", "chunk_by_paragraph", "chunk_by_size", "chunk_text", "get_chunk_preview",
    # Retriever
    "RetrievedChunk", "retrieve", "compute_relevance_score",
    "format_retrieved_context", "has_relevant_content",
]
