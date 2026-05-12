"""RAG context integration — inject retrieved documents into prompts.

Bridges document retrieval with LLM prompt building.
Maintains conversation continuity while adding document context.

No external dependencies — pure prompt orchestration.
"""

from typing import List, Optional
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

TANGGAPI PERTANYAAN USER:
"""[1:]  # Strip leading newline


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

    # Find injection point: before CONVERSATION_RULES
    if "## CONVERSATION CONTINUITY" in base_prompt:
        # Inject before the rules section
        parts = base_prompt.split("## CONVERSATION CONTINUITY")
        if len(parts) == 2:
            return (
                parts[0] +
                RAG_INSTRUCTION.format(retrieved_context=retrieved_text) +
                "\n\n## CONVERSATION CONTINUITY" +
                parts[1]
            )

    # Fallback: append at end
    return base_prompt + RAG_INSTRUCTION.format(retrieved_context=retrieved_text)


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
