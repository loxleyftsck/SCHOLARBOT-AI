"""UI module — Streamlit components and styling.

Extracted from app.py Phase 2 refactor.
Contains all custom CSS and sidebar configuration.
"""

from .styles import CSS
from .sidebar import (
    HEADER_HTML,
    SECTION_LABELS,
    GROQ_KEY_HELP,
    GROQ_KEY_PH,
    NAME_PLACEHOLDER,
    CHAT_PLACEHOLDER_DEFAULT,
    memory_card_html,
)
from .react_bridge import render_custom_chat, render_welcome_screen
from .streaming_manager import (
    StreamingManager,
    create_streaming_manager,
    render_chat_html,
    get_or_create_manager,
    clear_manager,
)

__all__ = [
    "CSS",
    "HEADER_HTML",
    "SECTION_LABELS",
    "GROQ_KEY_HELP",
    "GROQ_KEY_PH",
    "NAME_PLACEHOLDER",
    "CHAT_PLACEHOLDER_DEFAULT",
    "memory_card_html",
    "render_custom_chat",
    "render_welcome_screen",
    "StreamingManager",
    "create_streaming_manager",
    "render_chat_html",
    "get_or_create_manager",
    "clear_manager",
]
