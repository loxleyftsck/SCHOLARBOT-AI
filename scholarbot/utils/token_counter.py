"""Token counting utilities — estimate and manage token usage.

Engineering Decision:
- No external library dependency (tiktoken, transformers)
  to keep installation simple for a student project
- Uses character-based estimation as baseline approximation
- 1 token ~= 4 characters for Llama/OpenAI models
- For production: replace with tiktoken or transformer tokenizer

Phase 3 refactor addition.
"""

import re
from dataclasses import dataclass


# ─── Model Context Limits ────────────────────────────────────────────────────────

# Groq Llama 3.3 70B Versatile: 128k tokens context window
MODEL_CONTEXT_LIMITS = {
    "llama-3.3-70b-versatile": 128_000,
    "llama-3.1-70b-versatile": 128_000,
    "llama-3.1-8b-instant":    128_000,
    "mixtral-8x7b-32768":       32_768,
    "llama3-70b-8192":           8_192,
}

DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Safety margin: reserve 5% of context for response
TOKEN_SAFETY_MARGIN = 0.05


# ─── Token Estimation ───────────────────────────────────────────────────────────

def get_model_context_limit(model: str = DEFAULT_MODEL) -> int:
    """Return max context tokens for a model, defaulting to 128k."""
    return MODEL_CONTEXT_LIMITS.get(model, 128_000)


def estimate_tokens(text: str) -> int:
    """Estimate token count from text.

    Uses character-based approximation: 1 token ~= 4 characters.
    This is a rough estimate suitable for pre-flight checks.

    Args:
        text: Input string

    Returns:
        Estimated token count (rounded up)
    """
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def count_message_tokens(role: str, content: str) -> int:
    """Estimate tokens for a single message including role overhead.

    Groq/OpenAI format: role + content + formatting tokens.
    Approximate overhead: ~4 tokens for role marker + newline.

    Args:
        role: "system", "user", or "assistant"
        content: Message content string

    Returns:
        Estimated token count for this message
    """
    base = estimate_tokens(content)
    overhead = 4  # role tag + newlines
    return base + overhead


def count_conversation_tokens(messages: list[dict]) -> int:
    """Count total estimated tokens for a conversation history.

    Args:
        messages: List of {"role": ..., "content": ...} dicts

    Returns:
        Total estimated token count
    """
    total = 0
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        total += count_message_tokens(role, content)
    return total


# ─── Token Limit Checking ───────────────────────────────────────────────────────

def is_within_limit(messages: list[dict], model: str = DEFAULT_MODEL,
                    safety_margin: float = TOKEN_SAFETY_MARGIN) -> bool:
    """Check if conversation fits within model's context limit.

    Args:
        messages: Conversation history
        model: Model name for context limit lookup
        safety_margin: Fraction of limit to reserve for response (default 5%)

    Returns:
        True if within limit, False if would overflow
    """
    total = count_conversation_tokens(messages)
    limit = get_model_context_limit(model)
    safe_limit = int(limit * (1 - safety_margin))
    return total <= safe_limit


def get_safe_input_limit(model: str = DEFAULT_MODEL,
                         safety_margin: float = TOKEN_SAFETY_MARGIN) -> int:
    """Return max safe input tokens for a given model.

    Accounts for safety margin reserved for response generation.

    Args:
        model: Model name
        safety_margin: Fraction to reserve

    Returns:
        Max tokens safe to use for input (including system prompt)
    """
    limit = get_model_context_limit(model)
    return int(limit * (1 - safety_margin))


# ─── Truncation Strategy ───────────────────────────────────────────────────────

def truncate_messages(messages: list[dict], max_tokens: int,
                      model: str = DEFAULT_MODEL) -> list[dict]:
    """Truncate conversation to fit within token limit.

    Strategy: Keep system prompt intact, remove oldest messages
    from the middle of conversation until within limit.

    Engineering Decision:
    - System messages are kept (first in list)
    - Older messages removed first (FIFO)
    - Preserves turn structure as much as possible
    - Adds a [Previous conversation truncated] marker

    Args:
        messages: Full conversation including system message
        max_tokens: Target max tokens
        model: Model name for token estimation

    Returns:
        Truncated message list that fits within limit
    """
    if not messages:
        return []

    # Always keep system message if present
    result = []
    system_msg = None
    working = []

    if messages and messages[0].get("role") == "system":
        system_msg = messages[0]
        working = list(messages[1:])
    else:
        working = list(messages)

    # Build up from most recent messages (keep newest)
    truncated = []
    current_tokens = 0
    limit = get_model_context_limit(model)
    safe_limit = int(limit * (1 - TOKEN_SAFETY_MARGIN))

    # Count backwards from newest
    for msg in reversed(working):
        msg_tokens = count_message_tokens(msg.get("role", "user"), msg.get("content", ""))
        if current_tokens + msg_tokens <= safe_limit:
            truncated.insert(0, msg)
            current_tokens += msg_tokens
        else:
            break  # reached limit

    # Build final list
    final = []
    if system_msg:
        final.append(system_msg)

    if truncated != working and working:
        # Truncation happened — add marker
        final.append({
            "role": "system",
            "content": "[Percakapan sebelumnya telah dipangkas karena melebihi batas konteks. Info penting mungkin hilang.]"
        })

    final.extend(truncated)
    return final


# ─── Token Report ───────────────────────────────────────────────────────────────

@dataclass
class TokenReport:
    """Summary of token usage for a conversation."""
    model: str
    total_tokens: int
    context_limit: int
    safe_limit: int
    usage_percent: float
    is_safe: bool
    messages_count: int
    truncation_needed: bool


def generate_token_report(messages: list[dict], model: str = DEFAULT_MODEL) -> TokenReport:
    """Generate a detailed token usage report.

    Useful for debugging and monitoring.

    Args:
        messages: Conversation history
        model: Model name

    Returns:
        TokenReport dataclass with usage statistics
    """
    total = count_conversation_tokens(messages)
    limit = get_model_context_limit(model)
    safe_limit = int(limit * (1 - TOKEN_SAFETY_MARGIN))
    usage_pct = (total / safe_limit * 100) if safe_limit > 0 else 0
    is_safe = total <= safe_limit

    return TokenReport(
        model=model,
        total_tokens=total,
        context_limit=limit,
        safe_limit=safe_limit,
        usage_percent=round(usage_pct, 1),
        is_safe=is_safe,
        messages_count=len(messages),
        truncation_needed=not is_safe,
    )
