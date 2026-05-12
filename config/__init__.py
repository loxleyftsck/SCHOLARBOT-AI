"""Configuration module — app settings and environment variables.

Extracted from app.py Phase 2 refactor.
Single source of truth for all tunables.
"""

from .settings import (
    GROQ_API_KEY,
    MODEL_NAME,
    MODEL_TEMPERATURE,
    MODEL_MAX_TOKENS,
    APP_TITLE,
    APP_ICON,
    APP_LAYOUT,
    APP_SIDEBAR_STATE,
    TOPICS_MEMORY_CAP,
    CONVERSATION_CAP,
    TOPICS_DISPLAY_LIMIT,
)

__all__ = [
    "GROQ_API_KEY",
    "MODEL_NAME",
    "MODEL_TEMPERATURE",
    "MODEL_MAX_TOKENS",
    "APP_TITLE",
    "APP_ICON",
    "APP_LAYOUT",
    "APP_SIDEBAR_STATE",
    "TOPICS_MEMORY_CAP",
    "CONVERSATION_CAP",
    "TOPICS_DISPLAY_LIMIT",
]
