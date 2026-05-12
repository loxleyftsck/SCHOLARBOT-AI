"""Session state manager — pure logic, no Streamlit UI.

Extracted from app.py Phase 4 refactor.
Responsibility: schema definition, init, reset, state transitions.
"""

from datetime import datetime

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
    "current_context": "",    # Current active context ("quiz", "tutor", "mindmap", "")
    "awaiting_followup": False,  # Is user expected to respond with command?
}

# Memory display wants a capped view of topics
TOPICS_DISPLAY_LIMIT = 3

# How many topic strings to keep in memory (FIFO cap)
TOPICS_MEMORY_CAP = 20

# How many conversation turns to keep (FIFO cap)
CONVERSATION_CAP = 50  # ~25 user + 25 assistant pairs


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
    Returns a shallow copy of state with the updated list.
    """
    new_messages = state["messages"] + [make_message(role, content, session_start())]
    if len(new_messages) > CONVERSATION_CAP:
        # Keep only the last CONVERSATION_CAP messages
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

    Returns a shallow copy of state with messages cleared.
    """
    return {
        **state,
        "messages": [],
        "topics_discussed": [],
        "msg_count": 0,
        "active_mode": None,
        # Clear context on chat reset
        "last_question": "",
        "last_answer": "",
        "current_context": "",
        "awaiting_followup": False,
    }


# ─── Memory Display (pure HTML builder) ───────────────────────────────────────

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
            '<span style="color:#4a5568">Belum ada topik</span>'
            '</div>'
        )

    # Show active context if any
    ctx = state.get("current_context", "")
    if ctx:
        ctx_labels = {"quiz": "Kuis", "tutor": "Tutor", "mindmap": "Mind Map", "summary": "Rangkuman"}
        ctx_label = ctx_labels.get(ctx, ctx)
        html += (
            f'<div class="memory-item">'
            f'<div class="memory-dot" style="background:#f6e05e"></div>'
            f'<span>Mode: <b>{ctx_label}</b></span>'
            f'</div>'
        )

    html += "</div>"
    return html