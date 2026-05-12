"""Core module — pure logic, no Streamlit.

Phase 3: llm_client, session_helpers
Phase 4: memory_manager
"""

from .llm_client import get_client, set_api_key, chat, API_KEY
from .session_helpers import (
    build_system_prompt,
    build_messages,
    extract_topic,
    call_llama,
    detect_intent,
    expand_short_command,
    is_quiz_request,
    extract_answer_from_response,
    extract_question_from_response,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
)
from .memory_manager import (
    SESSION_DEFAULTS,
    init_defaults,
    append_message,
    add_topic,
    reset_chat,
    build_memory_card_html,
    TOPICS_MEMORY_CAP,
    CONVERSATION_CAP,
)

__all__ = [
    # LLM client
    "get_client", "set_api_key", "chat", "API_KEY",
    # Prompt builder
    "build_system_prompt", "build_messages", "extract_topic", "call_llama",
    "detect_intent", "expand_short_command", "is_quiz_request",
    "extract_answer_from_response", "extract_question_from_response",
    "DEFAULT_MODEL", "DEFAULT_TEMPERATURE", "DEFAULT_MAX_TOKENS",
    # Memory manager
    "SESSION_DEFAULTS",
    "init_defaults",
    "append_message",
    "add_topic",
    "reset_chat",
    "build_memory_card_html",
    "TOPICS_MEMORY_CAP",
    "CONVERSATION_CAP",
]