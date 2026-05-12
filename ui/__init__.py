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

__all__ = [
    "CSS",
    "HEADER_HTML",
    "SECTION_LABELS",
    "GROQ_KEY_HELP",
    "GROQ_KEY_PH",
    "NAME_PLACEHOLDER",
    "CHAT_PLACEHOLDER_DEFAULT",
    "memory_card_html",
]
