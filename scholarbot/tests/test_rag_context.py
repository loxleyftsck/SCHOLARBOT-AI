"""Tests for core/rag_context.py — RAG prompt injection & citation system (v4.0)."""

import pytest

from core.rag_context import (
    build_rag_system_prompt,
    build_citation_map,
    extract_citation_ids,
    strip_invalid_citations,
)
from services.retriever import RetrievedChunk, format_retrieved_context


def make_chunk(idx: int, score: float = 0.5, source: str = "materi.pdf") -> RetrievedChunk:
    """Helper: build a RetrievedChunk with predictable content."""
    return RetrievedChunk(
        content=f"Isi potongan nomor {idx} tentang elastisitas permintaan.",
        score=score,
        source_filename=source,
        chunk_index=idx,
    )


class TestCitationFormatting:
    """Context handed to the LLM must carry the same markers the UI shows."""

    def test_context_uses_numbered_markers(self):
        context = format_retrieved_context([make_chunk(0), make_chunk(1)])
        assert "[1] Sumber: materi.pdf (bagian 1)" in context
        assert "[2] Sumber: materi.pdf (bagian 2)" in context

    def test_system_prompt_lists_valid_citation_numbers(self):
        prompt = build_rag_system_prompt("PROMPT DASAR", [make_chunk(0), make_chunk(1)])
        assert "ATURAN SITASI" in prompt
        assert "[1], [2]" in prompt

    def test_system_prompt_untouched_without_chunks(self):
        assert build_rag_system_prompt("PROMPT DASAR", []) == "PROMPT DASAR"

    def test_system_prompt_injected_before_continuity_section(self):
        base = "PERSONALITY\n\n## CONVERSATION CONTINUITY\nAturan lanjutan"
        prompt = build_rag_system_prompt(base, [make_chunk(0)])
        assert prompt.index("ATURAN SITASI") < prompt.index("## CONVERSATION CONTINUITY")


class TestBuildCitationMap:
    """Citation ids must match the [n] markers injected into the prompt."""

    def test_ids_are_one_based_and_sequential(self):
        citations = build_citation_map([make_chunk(0), make_chunk(3), make_chunk(7)])
        assert [c["id"] for c in citations] == [1, 2, 3]
        assert [c["chunk_index"] for c in citations] == [0, 3, 7]

    def test_keeps_source_and_rounded_score(self):
        citations = build_citation_map([make_chunk(0, score=0.123456, source="bio.txt")])
        assert citations[0]["source"] == "bio.txt"
        assert citations[0]["score"] == 0.1235

    def test_truncates_long_content(self):
        long_chunk = RetrievedChunk(
            content="x" * 900, score=0.4, source_filename="a.txt", chunk_index=0
        )
        citations = build_citation_map([long_chunk], snippet_chars=100)
        assert len(citations[0]["content"]) == 100

    def test_accepts_dict_chunks_restored_from_disk(self):
        restored = {"content": "isi", "source": "disk.pdf", "index": 4, "score": 0.9}
        citations = build_citation_map([restored])
        assert citations[0] == {
            "id": 1,
            "source": "disk.pdf",
            "chunk_index": 4,
            "score": 0.9,
            "content": "isi",
        }

    def test_empty_input(self):
        assert build_citation_map([]) == []


class TestExtractCitationIds:
    """Parsing which sources the answer actually used."""

    def test_collects_unique_sorted_ids(self):
        text = "Elastisitas itu kepekaan. [2] Contohnya harga naik. [1][2]"
        assert extract_citation_ids(text, max_id=3) == [1, 2]

    def test_ignores_ids_beyond_available_sources(self):
        assert extract_citation_ids("Klaim tanpa dasar. [7]", max_id=3) == []

    def test_ignores_zero_and_no_markers(self):
        assert extract_citation_ids("Tidak ada sitasi di sini.", max_id=3) == []
        assert extract_citation_ids("Nol tidak valid. [0]", max_id=3) == []

    def test_empty_text(self):
        assert extract_citation_ids("", max_id=3) == []


class TestStripInvalidCitations:
    """Answers must never point at sources the user cannot open."""

    def test_removes_out_of_range_markers_only(self):
        cleaned = strip_invalid_citations("Benar. [1] Karangan. [9]", max_id=1)
        assert "[1]" in cleaned
        assert "[9]" not in cleaned

    def test_removes_everything_when_no_sources(self):
        assert "[1]" not in strip_invalid_citations("Klaim. [1]", max_id=0)

    def test_leaves_clean_text_alone(self):
        text = "Jawaban biasa tanpa penanda."
        assert strip_invalid_citations(text, max_id=2) == text
