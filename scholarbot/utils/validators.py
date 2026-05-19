"""Input validation utilities — sanitization, format checking, and security.

Engineering Decision:
- Keep validation lightweight and declarative
- No external dependencies (pure Python stdlib)
- Return structured ValidationResult for easy error handling
- Focus on security: prevent prompt injection, sanitize HTML

Phase 4 refactor addition.
"""

import re
import html
from dataclasses import dataclass
from typing import Optional


# ─── Validation Result ─────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    """Structured result for validation operations."""
    is_valid: bool
    message: str
    sanitized_value: Optional[str] = None
    errors: Optional[list[str]] = None

    def __bool__(self) -> bool:
        return self.is_valid

    @classmethod
    def ok(cls, value: str, msg: str = "OK"):
        return cls(is_valid=True, message=msg, sanitized_value=value)

    @classmethod
    def fail(cls, msg: str, errors: Optional[list[str]] = None):
        return cls(is_valid=False, message=msg, errors=errors or [msg])


# ─── API Key Validation ────────────────────────────────────────────────────────

# Groq API key format: gsk_ followed by 52 alphanumeric chars
GROQ_KEY_PATTERN = re.compile(r'^gsk_[A-Za-z0-9]{52}$')

# Gemini API key format: AIza followed by 30+ chars
GEMINI_KEY_PATTERN = re.compile(r'^AIza[A-Za-z0-9_-]{30,}$')

# Generic API key pattern (fallback)
GENERIC_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]{20,}$')


def validate_api_key_format(key: str) -> ValidationResult:
    """Validate API key format for Groq or Gemini.

    Accepts:
    - Groq keys: gsk_ + 52 alphanumeric chars
    - Gemini keys: AIza + 30+ alphanumeric chars
    - Generic: 20+ alphanumeric chars (fallback)

    Does NOT validate key authenticity — only format.

    Args:
        key: API key string to validate

    Returns:
        ValidationResult with is_valid flag and sanitized value
    """
    if not key:
        return ValidationResult.fail("API key tidak boleh kosong.")

    key = key.strip()

    if GROQ_KEY_PATTERN.match(key):
        return ValidationResult.ok(key, "Format Groq API key valid.")

    if GEMINI_KEY_PATTERN.match(key):
        return ValidationResult.ok(key, "Format Gemini API key valid.")

    if GENERIC_KEY_PATTERN.match(key):
        return ValidationResult.ok(key, "Format API key valid (generic).")

    return ValidationResult.fail(
        "Format API key tidak valid. Pastikan key benar (20+ karakter alphanumeric)."
    )


# ─── Message Validation ─────────────────────────────────────────────────────────

# Max lengths
MAX_MESSAGE_LENGTH = 8_000      # Single message
MAX_TOPIC_LENGTH = 200          # Topic string
MAX_USER_NAME_LENGTH = 100      # Display name


def validate_message(content: str) -> ValidationResult:
    """Validate user message for safety and length.

    Checks:
    - Not empty
    - Not too long
    - No obvious prompt injection attempts
    - No control characters

    Args:
        content: User message content

    Returns:
        ValidationResult with validation status
    """
    if not content:
        return ValidationResult.fail("Pesan tidak boleh kosong.")

    # Strip and check length
    content = content.strip()

    if len(content) < 1:
        return ValidationResult.fail("Pesan tidak boleh kosong.")

    if len(content) > MAX_MESSAGE_LENGTH:
        return ValidationResult.fail(
            f"Pesan terlalu panjang ({len(content)} chars). "
            f"Maksimal {MAX_MESSAGE_LENGTH} karakter."
        )

    # Check for control characters (exclude newlines, tabs)
    control_pattern = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]')
    if control_pattern.search(content):
        return ValidationResult.fail("Pesan mengandung karakter kontrol tidak valid.")

    # Check for obvious prompt injection patterns
    injection_patterns = [
        (r'ignore\s+(previous|above|all)', "Percobaan manipulasi terdeteksi."),
        (r'system\s*:\s*', "Percobaan injection terdeteksi."),
        (r'you\s+are\s+now\s+', "Percobaan role-playing bypass terdeteksi."),
        (r'\[\s*SYSTEM\s*\]', "Percobaan prompt injection terdeteksi."),
    ]

    for pattern, msg in injection_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return ValidationResult.fail(msg)

    return ValidationResult.ok(content, "Pesan valid.")


def validate_topic(topic: str) -> ValidationResult:
    """Validate topic string extracted from user input.

    Args:
        topic: Topic string

    Returns:
        ValidationResult with validation status
    """
    if not topic:
        return ValidationResult.fail("Topik kosong.")

    topic = topic.strip()

    if len(topic) < 1:
        return ValidationResult.fail("Topik kosong.")

    if len(topic) > MAX_TOPIC_LENGTH:
        return ValidationResult.fail(
            f"Topik terlalu panjang ({len(topic)} chars). "
            f"Maksimal {MAX_TOPIC_LENGTH} karakter."
        )

    # Sanitize: remove extra whitespace
    sanitized = re.sub(r'\s+', ' ', topic).strip()

    return ValidationResult.ok(sanitized, "Topik valid.")


def validate_user_name(name: str) -> ValidationResult:
    """Validate user display name.

    Args:
        name: User input for display name

    Returns:
        ValidationResult with validation status
    """
    if not name:
        return ValidationResult.ok("", "Nama kosong (diperbolehkan).")

    name = name.strip()

    if len(name) > MAX_USER_NAME_LENGTH:
        return ValidationResult.fail(
            f"Nama terlalu panjang ({len(name)} chars). "
            f"Maksimal {MAX_USER_NAME_LENGTH} karakter."
        )

    # Allow letters, numbers, spaces, basic punctuation
    name_pattern = re.compile(r'^[\w\s.,\'"-]+$')
    if not name_pattern.match(name):
        return ValidationResult.fail(
            "Nama mengandung karakter tidak valid. "
            "Gunakan huruf, angka, spasi, dan tanda baca dasar."
        )

    return ValidationResult.ok(name, "Nama valid.")


# ─── Input Sanitization ─────────────────────────────────────────────────────────

def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize user input for safe storage and display.

    Operations:
    - Strip leading/trailing whitespace
    - Normalize multiple spaces/newlines
    - Escape HTML entities (XSS prevention)
    - Truncate if max_length provided

    Args:
        text: Input string to sanitize
        max_length: Optional max length (truncates if exceeded)

    Returns:
        Sanitized string safe for storage and HTML rendering
    """
    if not text:
        return ""

    # Strip whitespace
    text = text.strip()

    # Normalize whitespace (multiple spaces/tabs → single space)
    text = re.sub(r'[ \t]+', ' ', text)
    # Normalize newlines (3+ newlines → 2)
    text = re.sub(r'\n{3,}', '\n\n')

    # Escape HTML entities
    text = html.escape(text)

    # Optionally truncate
    if max_length and len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def sanitize_for_markdown(text: str) -> str:
    """Sanitize text for safe display in markdown/Streamlit.

    Unlike sanitize_input, this preserves line breaks and basic formatting.

    Args:
        text: Input string

    Returns:
        Markdown-safe string
    """
    if not text:
        return ""

    # Strip but preserve newlines
    text = text.strip()

    # Escape potential markdown injection
    # Allow: *, _, `, >, #, - (basic formatting)
    # Block: [link](url), <script>, etc.

    # Remove HTML tags (security)
    text = re.sub(r'<[^>]+>', '', text)

    # Escape square brackets to prevent markdown links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\\\1 (\2)', text)

    return text


# ─── Utility Validators ─────────────────────────────────────────────────────────

def is_safe_message(message: str) -> bool:
    """Quick boolean check: is message safe to send to LLM?

    Convenience wrapper around validate_message for simple if/else usage.

    Args:
        message: Message content

    Returns:
        True if valid and safe, False otherwise
    """
    return validate_message(message).is_valid


def sanitize_topic_input(text: str) -> str:
    """Extract and sanitize a topic from raw user input.

    Specialized version of extract_topic with sanitization.

    Args:
        text: Raw user message

    Returns:
        Sanitized topic string
    """
    result = validate_topic(text)
    return result.sanitized_value if result.is_valid else ""