"""Utilities module — helper functions for token counting, validation, and formatting.

Phase 3-4 refactor additions.
"""

from .token_counter import (
    estimate_tokens,
    count_message_tokens,
    count_conversation_tokens,
    is_within_limit,
    truncate_messages,
    get_model_context_limit,
)
from .validators import (
    validate_api_key_format,
    validate_message,
    validate_topic,
    sanitize_input,
    ValidationResult,
)

__all__ = [
    # Token counter
    "estimate_tokens",
    "count_message_tokens",
    "count_conversation_tokens",
    "is_within_limit",
    "truncate_messages",
    "get_model_context_limit",
    # Validators
    "validate_api_key_format",
    "validate_message",
    "validate_topic",
    "sanitize_input",
    "ValidationResult",
]
