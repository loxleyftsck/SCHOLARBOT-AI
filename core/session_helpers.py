"""Prompt builder and conversation utilities — no Streamlit deps.

Extracted from app.py Phase 3 refactor.
Responsibility: build LLM inputs (messages, system prompt, topic extraction).
"""

from prompts import PERSONALITIES

# Default model (can be overridden via set_model in llm_client, or here)
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048


def build_system_prompt(personality_key: str, user_name: str = "", topics: list[str] = None) -> str:
    """Build system prompt by injecting personality + session memory.

    Args:
        personality_key: One of PERSONALITIES.keys()
        user_name: User's display name (optional)
        topics: List of recently discussed topic strings (optional)

    Returns:
        Complete system prompt string.
    """
    base = PERSONALITIES[personality_key]["system"]
    memory_parts = []
    if user_name:
        memory_parts.append(f"Nama user adalah {user_name}, sapa dengan namanya bila relevan.")
    if topics:
        recent = ", ".join(topics[-3:])
        memory_parts.append(f"Topik yang sudah dibahas sebelumnya: {recent}.")
    if memory_parts:
        base += " " + " ".join(memory_parts)
    base += (
        " Kamu fokus pada bidang edukasi dan pembelajaran. "
        "Saat user menanyakan hal di luar topik belajar, arahkan kembali dengan sopan. "
        "Selalu berikan jawaban yang akurat, bermanfaat, dan mendidik."
    )
    return base


def build_messages(personality_key: str, user_name: str, topics: list[str],
                    conversation_history: list[dict]) -> list[dict]:
    """Assemble the full messages list: system + history.

    Args:
        personality_key: Personality mode key
        user_name: User's name
        topics: Topics list from session state
        conversation_history: List of {"role": ..., "content": ..., "time": ...}

    Returns:
        Messages list ready for Groq API.
    """
    system_content = build_system_prompt(personality_key, user_name, topics)
    messages = [{"role": "system", "content": system_content}]
    for m in conversation_history:
        role = "user" if m["role"] == "user" else "assistant"
        messages.append({"role": role, "content": m["content"]})
    return messages


def extract_topic(text: str) -> str | None:
    """Extract a short topic label from user input.

    Looks for trigger keywords and returns the 1–4 word phrase that follows.
    Falls back to full short input. Returns None for long inputs without triggers.

    Args:
        text: Raw user message

    Returns:
        Topic string or None.
    """
    keywords = ["tentang", "mengenai", "soal", "materi", "belajar", "pelajaran", "konsep", "jelaskan"]
    lower = text.lower()
    for kw in keywords:
        if kw in lower:
            idx = lower.find(kw) + len(kw)
            snippet = text[idx:idx+40].strip().split()[0:4]
            if snippet:
                return " ".join(snippet)
    if len(text) < 50:
        return text.strip()
    return None


def call_llama(user_msg: str, personality_key: str, user_name: str,
               topics: list[str], conversation_history: list[dict]) -> str:
    """High-level convenience function: build messages + call Groq.

    Equivalent to:
        messages = build_messages(...)
        return llm_client.chat(DEFAULT_MODEL, messages, ...)
    """
    from core.llm_client import chat
    messages = build_messages(personality_key, user_name, topics, conversation_history)
    return chat(DEFAULT_MODEL, messages, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS)