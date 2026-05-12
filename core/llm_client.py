"""Groq LLM client — pure API abstraction, no Streamlit deps.

Extracted from app.py Phase 3 refactor.
Responsibility: API calls only.
"""

import os
from groq import Groq

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

def chat(model: str, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """Send a chat request to Groq and return the assistant's response text.

    Args:
        model: Model identifier (e.g. "llama-3.3-70b-versatile")
        messages: List of {"role": ..., "content": ...} dicts
        temperature: Sampling temperature (0.0–2.0)
        max_tokens: Hard cap on response tokens

    Returns:
        Assistant message content as string, or error string on failure.
    """
    client = get_client()
    if not client:
        return (
            "⚠️ **API Key belum dikonfigurasi.**\n\n"
            "Pastikan `GROQ_API_KEY` sudah ada di file `.env`, "
            "lalu restart aplikasi."
        )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Terjadi error: `{e}`\n\nPastikan API key valid dan koneksi internet aktif."