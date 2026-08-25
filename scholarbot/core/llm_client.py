"""Groq LLM client — pure API abstraction, no Streamlit deps.

Extracted from app.py Phase 3 refactor.
Responsibility: API calls only.
Supports both streaming and non-streaming modes.
"""

import os
import time
import httpx
from groq import Groq
from typing import Iterator, Optional

API_KEY = os.getenv("GROQ_API_KEY", "")

_client = None


def get_client() -> Groq | None:
    """Lazily initialize and return Groq client."""
    global _client
    if _client is None and API_KEY:
        _client = Groq(api_key=API_KEY)
    return _client


def set_api_key(key: str) -> None:
    """Allow runtime key injection from UI."""
    global _client, API_KEY
    API_KEY = key
    _client = Groq(api_key=key)


def _classify_error(exc: Exception) -> tuple[str, bool]:
    """Classify exception to determine if it's retryable.

    Returns:
        (user_message, is_retryable)
    """
    err_str = str(exc).lower()
    exc_type = type(exc).__name__

    # Connection / network errors — retryable
    if exc_type in ("ConnectError", "ReadTimeout", "ConnectTimeout",
                    "RemoteDisconnected", "HTTPStatusError",
                    "httpx.ConnectError", "httpx.ReadTimeout",
                    "httpx.PoolTimeout", "httpx.ConnectRetry",
                    "TimeoutException", "ConnectionError"):
        return ("Koneksi terputus. Mencoba ulang...", True)

    # Rate limit — retryable with backoff
    if "429" in err_str or "rate_limit" in err_str or "rate limit" in err_str:
        return ("Server sedang sibuk. Mencoba ulang...", True)

    # 400 bad request — NOT retryable
    if "400" in err_str or "invalid_request" in err_str:
        return ("Permintaan tidak valid. Coba lagi.", False)

    # 401 auth — NOT retryable
    if "401" in err_str or "unauthorized" in err_str:
        return ("API Key tidak valid. Periksa GROQ_API_KEY di file .env.", False)

    # 500/502/503 server errors — retryable
    if any(code in err_str for code in ("500", "502", "503", "504",
                                        "internal server error",
                                        "service unavailable",
                                        "bad gateway")):
        return ("Server Groq sedang gangguan. Mencoba ulang...", True)

    # Unknown — don't retry, show generic message
    return (f"Terjadi error: `{exc}`. Pastikan API key valid dan koneksi aktif.", False)


MAX_RETRIES = 2
BASE_DELAY = 1.5  # seconds
DEFAULT_MODEL = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")


def chat(messages: list[dict],
         model: str = DEFAULT_MODEL,
         temperature: float = 0.7,
         max_tokens: int = 2048,
         stream: bool = False,
         json_mode: bool = False) -> str | Iterator[str]:
    """Send a chat request to Groq and return the assistant's response text.

    Supports both streaming and non-streaming modes.

    Args:
        model: Model identifier (e.g. "openai/gpt-oss-120b")
        messages: List of {"role": ..., "content": ...} dicts
        temperature: Sampling temperature (0.0–2.0)
        max_tokens: Hard cap on response tokens
        stream: If True, returns an iterator of text chunks

    Returns:
        Non-streaming: Assistant message content as string
        Streaming: Iterator yielding text chunks as they arrive
    """
    client = get_client()
    if not client:
        return (
            "API Key belum dikonfigurasi. "
            "Pastikan GROQ_API_KEY ada di file .env, lihat .env.example, lalu restart."
        )

    last_error_msg = ""

    for attempt in range(MAX_RETRIES + 1):
        try:
            if stream:
                if json_mode:
                    raise ValueError("Streaming is not supported with json_mode")
                return _stream_chat(client, model, messages, temperature, max_tokens)
            else:
                return _non_stream_chat(client, model, messages, temperature, max_tokens, json_mode)

        except httpx.TimeoutException as e:
            user_msg, is_retryable = _classify_error(e)
            last_error_msg = user_msg
            if not is_retryable or attempt >= MAX_RETRIES:
                return user_msg
            delay = BASE_DELAY * (2 ** attempt)
            time.sleep(delay)

        except Exception as e:
            user_msg, is_retryable = _classify_error(e)
            last_error_msg = user_msg
            if not is_retryable or attempt >= MAX_RETRIES:
                return user_msg
            delay = BASE_DELAY * (2 ** attempt)
            time.sleep(delay)

    # All retries exhausted
    return last_error_msg


def _non_stream_chat(client: Groq,
                      model: str,
                      messages: list[dict],
                      temperature: float,
                      max_tokens: int,
                      json_mode: bool = False) -> str:
    """Non-streaming chat completion."""
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": httpx.Timeout(30.0, connect=10.0),
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)

    if not response.choices:
        return "API tidak mengembalikan response. Coba kirim pesan lagi."

    content = response.choices[0].message.content

    if content is None or content.strip() == "":
        return "Bot tidak dapat generate response. Coba reformulasi pertanyaan."

    return content


def _stream_chat(client: Groq,
                  model: str,
                  messages: list[dict],
                  temperature: float,
                  max_tokens: int) -> Iterator[str]:
    """Streaming chat completion - yields text chunks as they arrive."""
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
        timeout=httpx.Timeout(60.0, connect=10.0),
    )

    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def stream_chat(messages: list[dict],
                model: str = DEFAULT_MODEL,
                temperature: float = 0.7,
                max_tokens: int = 2048) -> Iterator[str]:
    """Convenience function for streaming chat.

    Alias for chat() with stream=True.

    Args:
        model: Model identifier
        messages: List of {"role": ..., "content": ...} dicts
        temperature: Sampling temperature
        max_tokens: Hard cap on response tokens

    Yields:
        Text chunks as they arrive from the model.
    """
    return chat(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )