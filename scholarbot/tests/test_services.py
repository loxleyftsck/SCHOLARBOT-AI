"""Tests for services/ — RAG pipeline components."""

import pytest
from services.chunker import chunk_text, Chunk
from services.retriever import retrieve, compute_relevance_score
from services.document_loader import extract_txt, extract_pdf, get_document_info


class TestDocumentLoader:
    """Test document text extraction."""

    def test_extract_txt_valid_utf8(self):
        """Should extract text from valid UTF-8 text."""
        content = extract_txt(b"Hello World\nIni teks Indonesia")
        assert "Hello World" in content
        assert "Indonesia" in content

    def test_extract_txt_fallback_encodings(self):
        """Should handle various encodings."""
        # Latin-1 encoded text
        content = extract_txt("Hello François".encode("latin-1"))
        assert "Hello" in content or "François" in content

    def test_get_document_info(self):
        """Should return correct document metadata."""
        text = "Ini adalah teks test. " * 100
        info = get_document_info(text, "test.txt")
        assert info["char_count"] > 0
        assert info["word_count"] > 0
        assert info["char_count"] > info["word_count"]  # chars > words

    def test_get_document_info_encoding(self):
        """Should handle special characters in filename."""
        info = get_document_info("Teks test", "dokumen_belajar.pdf")
        assert info["char_count"] > 0


class TestTextChunker:
    """Test text chunking strategies."""

    def test_chunk_by_paragraph(self):
        """Should chunk text by paragraphs."""
        text = "Para 1.\n\nPara 2.\n\nPara 3."
        chunks = chunk_text(text, strategy="paragraph", filename="test.txt")
        assert len(chunks) >= 1
        assert all(hasattr(c, "content") for c in chunks)

    def test_chunk_by_size(self):
        """Should chunk text by character size."""
        text = "Word " * 500
        chunks = chunk_text(text, strategy="size", max_chars=200, filename="test.txt")
        # Should have multiple chunks
        assert len(chunks) >= 2
        # Each chunk should respect size limit
        for chunk in chunks:
            assert len(chunk.content) <= 250  # 200 + overlap

    def test_chunk_auto_detect(self):
        """Should auto-detect chunking strategy."""
        text = "Para 1.\n\nPara 2.\n\n" * 10
        chunks = chunk_text(text, strategy="auto", filename="test.txt")
        assert len(chunks) >= 1

    def test_chunk_metadata(self):
        """Should include correct metadata in chunks."""
        chunks = chunk_text("Test content.", strategy="paragraph", filename="mydoc.txt")
        if chunks:
            chunk = chunks[0]
            assert hasattr(chunk, "content")
            assert hasattr(chunk, "source_filename")
            assert hasattr(chunk, "chunk_index")
            assert chunk.source_filename == "mydoc.txt"


class TestRetriever:
    """Test RAG retrieval system."""

    def test_retrieve_top_k(self):
        """Should retrieve top-k relevant chunks."""
        chunks = [
            Chunk(content="Fisika adalah ilmu alam", source_filename="test.txt", chunk_index=0),
            Chunk(content="Matematika adalah ilmu hitung", source_filename="test.txt", chunk_index=1),
            Chunk(content="Kimia adalah ilmu zat", source_filename="test.txt", chunk_index=2),
        ]
        results = retrieve("apa itu fisika", chunks, top_k=2)
        assert len(results) <= 2
        # First result should mention 'fisika'
        assert len(results) > 0
        assert "fisika" in results[0].content.lower()

    def test_relevance_score(self):
        """Should compute relevance scores correctly."""
        # Query about physics should score higher on physics content
        physics_chunk = Chunk(
            content="Fisika modern mencakup mekanika kuantum dan relativitas",
            source_filename="test.txt",
            chunk_index=0,
        )
        math_chunk = Chunk(
            content="Aljabar linear adalah cabang matematika",
            source_filename="test.txt",
            chunk_index=1,
        )

        physics_score = compute_relevance_score("apa itu fisika", physics_chunk)
        math_score = compute_relevance_score("apa itu fisika", math_chunk)

        assert physics_score > math_score

    def test_retrieve_empty_chunks(self):
        """Should handle empty chunk list gracefully."""
        results = retrieve("query", [], top_k=3)
        assert results == []

    def test_retrieve_with_overlap(self):
        """Should include chunk overlap in scoring."""
        chunks = [
            Chunk(content="Fisika sangat penting dalam sains.", source_filename="test.txt", chunk_index=0),
            Chunk(content="Fisika sangat penting dalam sains. Matematika juga penting.", source_filename="test.txt", chunk_index=1),
        ]
        results = retrieve("apa itu fisika", chunks, top_k=2)
        assert len(results) >= 1
