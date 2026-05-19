"""Session state manager — pure logic, no Streamlit UI.

Extracted from app.py Phase 4 refactor.
Responsibility: schema definition, init, reset, state transitions.
"""

from datetime import datetime

# Token guard: if conversation exceeds this many tokens, aggressively trim oldest pairs
TOKEN_TRIM_THRESHOLD = 6000


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ~= 4 chars (Llama/OpenAI approximation)."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)

# ─── Schema ───────────────────────────────────────────────────────────────────

SESSION_DEFAULTS = {
    "messages": [],
    "user_name": "",
    "personality": "😊 Santai & Friendly",
    "topics_discussed": [],
    "session_start": "",
    "msg_count": 0,
    "active_mode": None,
    # Conversation context tracking
    "last_question": "",      # Last question generated (for quiz mode)
    "last_answer": "",        # Last answer provided
    "current_context": "",    # Current active context ("quiz", "tutor", "")
    "awaiting_followup": False,  # Is user expected to respond with command?
    # v3 RAG fields
    "uploaded_docs": [],      # List of {"filename": str, "size": int, "type": str}
    "doc_texts": [],         # List of raw extracted text per doc
    "doc_chunks": [],         # List of {"content": str, "source": str, "index": int}
    "last_retrieved": [],     # Last retrieved RetrievedChunk list (for UI feedback)
}

# Memory display wants a capped view of topics
TOPICS_DISPLAY_LIMIT = 3

# How many topic strings to keep in memory (FIFO cap)
TOPICS_MEMORY_CAP = 20

# How many conversation turns to keep (FIFO cap)
CONVERSATION_CAP = 40  # ~20 user + 20 assistant pairs (strict cap)


# ─── Factory ───────────────────────────────────────────────────────────────────

def make_message(role: str, content: str, time_str: str) -> dict:
    """Create a message dict with consistent shape."""
    return {"role": role, "content": content, "time": time_str}


def session_start() -> str:
    """Current time as display string."""
    return datetime.now().strftime("%H:%M")


# ─── Session Init ──────────────────────────────────────────────────────────────

def init_defaults():
    """Return dict of (key → default_value) pairs.

    Caller (app.py) iterates this and sets st.session_state for keys
    that don't already exist. This keeps Streamlit coupling in app.py
    but keeps the schema definition here.
    """
    return SESSION_DEFAULTS.copy()


# ─── State Mutations (pure, return new values) ────────────────────────────────

def append_message(state: dict, role: str, content: str) -> dict:
    """Append a message to state['messages'] and increment count.

    Also enforces CONVERSATION_CAP — drops oldest messages when limit exceeded.
    Removes duplicate consecutive assistant messages if found.
    Returns a shallow copy of state with the updated list.
    """
    new_messages = state["messages"] + [make_message(role, content, session_start())]

    # Remove duplicate consecutive assistant messages
    # (can happen if API returns twice or UI double-posts)
    while (len(new_messages) >= 2
           and new_messages[-1]["role"] == "assistant"
           and new_messages[-2]["role"] == "assistant"):
        new_messages.pop(-2)

    if len(new_messages) > CONVERSATION_CAP:
        new_messages = new_messages[-CONVERSATION_CAP:]

    return {
        **state,
        "messages": new_messages,
        "msg_count": state["msg_count"] + 1,
    }


def add_topic(state: dict, topic: str) -> dict:
    """Append topic to state['topics_discussed'] with FIFO cap.

    Only adds if topic is not already in the list.
    Returns a shallow copy of state.
    """
    if not topic or topic in state["topics_discussed"]:
        return state

    new_topics = state["topics_discussed"] + [topic]
    if len(new_topics) > TOPICS_MEMORY_CAP:
        new_topics = new_topics[-TOPICS_MEMORY_CAP:]

    return {**state, "topics_discussed": new_topics}


def reset_chat(state: dict) -> dict:
    """Reset conversation state while keeping user profile.

    If messages exist, applies token guard before clearing — trims to last
    MAX_MESSAGE_PAIRS pairs if estimated tokens exceed TOKEN_TRIM_THRESHOLD.
    Logs a debug marker on reset for easy console filtering.
    """
    messages = state.get("messages", [])
    cleaned = messages

    if messages:
        # Token-level guard: trim oldest pairs if still over threshold
        total = sum(
            _estimate_tokens(m.get("content", ""))
            for m in cleaned
        )
        while total > TOKEN_TRIM_THRESHOLD and len(cleaned) > 3:
            removed = cleaned.pop(1 if cleaned[0].get("role") == "system" else 0)
            total -= _estimate_tokens(removed.get("content", ""))

    print("[RESET] state cleared")

    return {
        **state,
        "messages": cleaned,
        "topics_discussed": [],
        "msg_count": 0,
        "active_mode": None,
        # Clear conversation context
        "last_question": "",
        "last_answer": "",
        "current_context": "",
        "awaiting_followup": False,
        # Keep RAG docs — user may want to ask about same material
        # last_retrieved is cleared per conversation
        "last_retrieved": [],
    }


# ─── Memory Display (pure HTML builder) ───────────────────────────────────────

def reset_rag_docs(state: dict) -> dict:
    """Clear all RAG document state.

    Called when user explicitly clears uploaded documents.
    Returns a shallow copy of state with RAG fields reset.
    """
    print("[RESET] cleared: uploaded_docs, doc_texts, doc_chunks, last_retrieved")
    return {
        **state,
        "uploaded_docs": [],
        "doc_texts": [],
        "doc_chunks": [],
        "last_retrieved": [],
    }


def clear_all_state(state: dict) -> dict:
    """Clear ALL session state, including RAG docs.

    Lists every key cleared explicitly — use for hard reset.
    Returns a fresh copy of state with ONLY profile fields preserved.
    """
    from core import SESSION_DEFAULTS
    preserved = {k: state.get(k, v) for k, v in SESSION_DEFAULTS.items()
                if k in ("user_name", "personality")}
    print("[RESET] cleared: ALL state except user_name and personality")
    return {**SESSION_DEFAULTS, **preserved}


def build_memory_card_html(state: dict) -> str:
    """Build the sidebar memory card HTML from session state dict.

    Args:
        state: dict with keys user_name, session_start, msg_count, topics_discussed

    Returns:
        HTML string for the memory card.
    """
    html = '<div class="memory-card">'

    if state.get("user_name"):
        html += (
            f'<div class="memory-item">'
            f'<div class="memory-dot"></div>'
            f'<span>Nama: <b>{state["user_name"]}</b></span>'
            f'</div>'
        )

    if state.get("session_start"):
        html += (
            f'<div class="memory-item">'
            f'<div class="memory-dot"></div>'
            f'<span>Mulai: {state["session_start"]}</span>'
            f'</div>'
        )

    html += (
        f'<div class="memory-item">'
        f'<div class="memory-dot"></div>'
        f'<span>Pesan: {state["msg_count"]}</span>'
        f'</div>'
    )

    topics = state.get("topics_discussed", [])
    if topics:
        topics_str = ", ".join(topics[-TOPICS_DISPLAY_LIMIT:])
        html += (
            f'<div class="memory-item">'
            f'<div class="memory-dot"></div>'
            f'<span>Topik: {topics_str}</span>'
            f'</div>'
        )
    else:
        html += (
            '<div class="memory-item">'
            '<div class="memory-dot"></div>'
            '<span class="memory-no-topics">Belum ada topik</span>'
            '</div>'
        )

    # Show active context if any
    ctx = state.get("current_context", "")
    if ctx:
        ctx_labels = {"quiz": "Kuis", "tutor": "Tutor", "mindmap": "Mind Map", "summary": "Rangkuman"}
        ctx_label = ctx_labels.get(ctx, ctx)
        html += (
            f'<div class="memory-item">'
            f'<div class="memory-dot memory-dot-warning"></div>'
            f'<span>Mode: <b>{ctx_label}</b></span>'
            f'</div>'
        )

    # v3 RAG: show uploaded document summary
    uploaded_docs = state.get("uploaded_docs", [])
    if uploaded_docs:
        html += (
            f'<div class="memory-item">'
            f'<div class="memory-dot memory-dot-success"></div>'
            f'<span>{len(uploaded_docs)} dokumen dimuat</span>'
            f'</div>'
        )

    html += "</div>"
    return html