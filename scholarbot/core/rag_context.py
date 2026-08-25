"""RAG context integration — inject retrieved documents into prompts.

Bridges document retrieval with LLM prompt building.
Maintains conversation continuity while adding document context.

No external dependencies — pure prompt orchestration.
"""

import re
from typing import Any, Dict, List, Optional
from services.retriever import RetrievedChunk


RAG_INSTRUCTION = """
## DOKUMEN TERAKHAT
Berikut adalah materi yang di-upload oleh user:

{retrieved_context}

INSTRUKSI:
- Jawab pertanyaan user berdasarkan materi di atas
- Jika materi tidak cukup, gunakan pengetahuan umumu
- Jika user bertanya di luar materi, arahkan ke materi
- Prioritaskan isi dokumen di atas, bukan pengetahuan eksternal
- Tetap gunakan bahasa yang natural dan conversational

ATURAN SITASI (WAJIB):
- Setiap kalimat yang isinya berasal dari materi di atas WAJIB diakhiri penanda sumbernya, contoh: "Elastisitas mengukur kepekaan permintaan. [1]"
- Gunakan HANYA nomor yang tersedia di atas ({valid_citations}). Jangan pernah mengarang nomor lain.
- Satu kalimat boleh mengutip lebih dari satu sumber: "... seperti dijelaskan di materi. [1][3]"
- Kalimat yang berasal dari pengetahuan umum (bukan dari materi) JANGAN diberi penanda sama sekali.
- Jangan membuat daftar "Sumber:" di akhir jawaban — penanda inline sudah cukup.

TANGGAPI PERTANYAAN USER:
"""[1:]  # Strip leading newline

# Matches inline citation markers such as [1] or [12]
CITATION_PATTERN = re.compile(r"\[(\d{1,2})\]")


def build_rag_system_prompt(base_prompt: str, retrieved_chunks: List[RetrievedChunk],
                             current_context: str = "") -> str:
    """Build system prompt with RAG context injection.

    Injects retrieved document chunks at appropriate position:
    - Before CONVERSATION_RULES for LLM to have document context first
    - After personality but before general instructions

    Args:
        base_prompt: Original system prompt (personality + memory + rules)
        retrieved_chunks: List of RetrievedChunk objects
        current_context: Current mode ("quiz", "tutor", etc.)

    Returns:
        System prompt with RAG context injected
    """
    if not retrieved_chunks:
        # No documents loaded → use original prompt
        return base_prompt

    # Format retrieved chunks
    from services.retriever import format_retrieved_context
    retrieved_text = format_retrieved_context(retrieved_chunks)
    valid_citations = ", ".join(f"[{i}]" for i in range(1, len(retrieved_chunks) + 1))

    rag_block = RAG_INSTRUCTION.format(
        retrieved_context=retrieved_text,
        valid_citations=valid_citations
    )

    # Find injection point: before CONVERSATION_RULES
    if "## CONVERSATION CONTINUITY" in base_prompt:
        # Inject before the rules section
        parts = base_prompt.split("## CONVERSATION CONTINUITY")
        if len(parts) == 2:
            return (
                parts[0] +
                rag_block +
                "\n\n## CONVERSATION CONTINUITY" +
                parts[1]
            )

    # Fallback: append at end
    return base_prompt + rag_block


def build_rag_user_message(user_msg: str, retrieved_chunks: List[RetrievedChunk]) -> str:
    """Optionally prepend context to user message.

    Some LLMs respond better when document context is in user message
    rather than system prompt. Use this if base_prompt injection fails.

    Args:
        user_msg: Original user message
        retrieved_chunks: Retrieved chunks for context

    Returns:
        Expanded user message with optional context
    """
    if not retrieved_chunks:
        return user_msg

    from services.retriever import format_retrieved_context
    context = format_retrieved_context(retrieved_chunks)

    return (
        f"Berdasarkan materi berikut:\n\n"
        f"{context}\n\n"
        f"Jawab: {user_msg}"
    )


def should_use_rag(user_msg: str, has_documents: bool) -> bool:
    """Determine if RAG should be used for this message.

    RAG is useful when:
    - Documents are loaded
    - User asks questions (not just short commands)

    Skip RAG for:
    - Upload/control requests
    - Reset commands that include document-related words

    Args:
        user_msg: User message to analyze
        has_documents: Whether documents are loaded in session

    Returns:
        True if RAG context should be injected
    """
    if not has_documents:
        return False

    msg_lower = user_msg.lower().strip()

    # Skip for short follow-up commands (these have their own expansion logic)
    short_commands = ["gas", "lanjut", "next", "jawab", "bahas",
                     "buat lagi", "hint", "oke", "ya", "tidak"]
    if msg_lower in short_commands:
        return False

    # Skip for control messages about documents
    control_kws = ["upload", "file", "dokumen", "clear", "hapus",
                   "reset"]
    if any(kw in msg_lower for kw in control_kws):
        return False

    return True


def build_citation_map(retrieved_chunks: List[RetrievedChunk],
                       snippet_chars: int = 400) -> List[Dict[str, Any]]:
    """Turn retrieved chunks into numbered citation entries for the frontend.

    The `id` here is the exact number the LLM is told to use inline ([1], [2], ...),
    so the UI can match a marker in the answer to its source card.

    Args:
        retrieved_chunks: Retrieved chunks, in the same order given to the prompt
        snippet_chars: Max characters of chunk content sent to the UI

    Returns:
        List of dicts: id, source, chunk_index, score, content
    """
    citations: List[Dict[str, Any]] = []

    for i, chunk in enumerate(retrieved_chunks, 1):
        # Chunks may arrive as dataclasses (live retrieval) or dicts (restored from disk)
        if hasattr(chunk, "content"):
            content = chunk.content
            source = chunk.source_filename
            chunk_index = getattr(chunk, "chunk_index", 0)
            score = getattr(chunk, "score", 0.0)
        else:
            content = chunk.get("content", "")
            source = chunk.get("source_filename", chunk.get("source", ""))
            chunk_index = chunk.get("chunk_index", chunk.get("index", 0))
            score = chunk.get("score", 0.0)

        citations.append({
            "id": i,
            "source": source,
            "chunk_index": chunk_index,
            "score": round(float(score), 4),
            "content": content[:snippet_chars],
        })

    return citations


def extract_citation_ids(text: str, max_id: Optional[int] = None) -> List[int]:
    """Collect the citation markers actually used in an answer.

    Args:
        text: LLM answer possibly containing markers like "[1]" or "[2][3]"
        max_id: Highest valid citation id; markers above it are ignored
                (the model occasionally invents numbers)

    Returns:
        Sorted list of unique citation ids, in ascending order
    """
    if not text:
        return []

    found = set()
    for match in CITATION_PATTERN.findall(text):
        cid = int(match)
        if cid < 1:
            continue
        if max_id is not None and cid > max_id:
            continue
        found.add(cid)

    return sorted(found)


def strip_invalid_citations(text: str, max_id: int) -> str:
    """Remove citation markers that point to sources the user never received.

    Keeps the answer honest when the model cites [7] while only 3 chunks exist.

    Args:
        text: LLM answer
        max_id: Highest valid citation id (0 means no sources at all)

    Returns:
        Answer with out-of-range markers removed
    """
    if not text:
        return text

    def _replace(match: "re.Match[str]") -> str:
        cid = int(match.group(1))
        return match.group(0) if 1 <= cid <= max_id else ""

    cleaned = CITATION_PATTERN.sub(_replace, text)
    # Collapse whitespace left behind by removed markers
    return re.sub(r"[ \t]{2,}", " ", cleaned)


def get_rag_context_summary(retrieved_chunks: List[RetrievedChunk]) -> str:
    """Generate a one-line summary of what's available in documents.

    Useful for UI feedback and user expectation management.

    Args:
        retrieved_chunks: Retrieved chunks

    Returns:
        Summary string like "Menemukan 3 bagian dari materi.pdf"
    """
    if not retrieved_chunks:
        return ""

    sources = set(chunk.source_filename for chunk in retrieved_chunks)
    sources_str = ", ".join(sources)

    return f"📄 Menemukan {len(retrieved_chunks)} bagian dari {sources_str}"
