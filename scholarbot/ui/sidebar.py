"""Sidebar configuration and pure UI helpers — no business logic.

Extracted from app.py Phase 5 refactor.
Contains sidebar layout data and memory card rendering.
"""

from pathlib import Path
from prompts import PERSONALITIES, MODES
from core.memory_manager import build_memory_card_html
try:
    from ui.icons import ICONS
except ModuleNotFoundError:
    try:
        from scholarbot.ui.icons import ICONS
    except ModuleNotFoundError:
        try:
            from .icons import ICONS
        except ImportError:
            import importlib
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            importlib.invalidate_caches()
            from icons import ICONS

# ─── Layout Constants ───────────────────────────────────────────────────────────

import base64
import os

def _get_mascot_base64():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mascot_path = os.path.join(os.path.dirname(current_dir), "assets", "mascot.png")
        if os.path.exists(mascot_path):
            with open(mascot_path, "rb") as img_file:
                b64 = base64.b64encode(img_file.read()).decode()
                return f'<img src="data:image/png;base64,{b64}" alt="Mascot" />'
    except Exception:
        pass
    return ICONS["graduation"]

HEADER_HTML = f"""
<div class="scholar-header">
<div class="scholar-logo-wrapper">
{_get_mascot_base64()}
</div>
<div>
<div class="scholar-title">ScholarBot</div>
<div class="scholar-sub">AI Study Assistant</div>
</div>
</div>
"""

SECTION_LABELS = {
    "api_key":   "API Key",
    "profile":   "Profil Kamu",
    "personality": "Personality",
    "modes":     "Belajar Mode",
    "memory":    "Session Memory",
}

# Keys in PERSONALITIES, in display order
PERSONALITY_KEYS = list(PERSONALITIES.keys())

# Keys in MODES, in display order
MODE_KEYS = list(MODES.keys())

# Memory display label (shown in sidebar)
MEMORY_LABEL = SECTION_LABELS["memory"]

# API key caption
GROQ_KEY_HELP = "Gratis di [console.groq.com](https://console.groq.com/keys)"
GROQ_KEY_PH = "gsk_..."

# Name input
NAME_PLACEHOLDER = "Namamu di sini…"

# Chat input placeholder (fallback, when no mode is active)
CHAT_PLACEHOLDER_DEFAULT = "Tanya apa saja tentang pelajaran…"


# ─── Pure UI Helpers (no st.) ─────────────────────────────────────────────────

def render_sidebar(state: dict, api_key_set: bool):
    """Return a dict of sidebar render configuration.

    Caller (app.py) uses this to drive Streamlit widget calls.
    Each key maps to a tuple: (section_label_html, widget_call_kwargs)

    This function itself does NOT call st.* — it only returns config.

    Args:
        state: st.session_state as plain dict
        api_key_set: True if API_KEY env var is already set

    Returns:
        Dict with render metadata (no st. calls).
    """
    personality_keys = PERSONALITY_KEYS
    current_persona = state.get("personality", "😊 Santai & Friendly")
    try:
        persona_index = personality_keys.index(current_persona)
    except ValueError:
        persona_index = 0

    p_info = PERSONALITIES[personality_keys[persona_index]]
    persona_desc_html = (
        f'<div class="persona-desc">'
        f'<b class="persona-desc-name">{p_info["label"]}</b> — {p_info["desc"]}'
        f'</div>'
    )

    return {
        "persona_keys": persona_keys,
        "persona_index": persona_index,
        "persona_desc_html": persona_desc_html,
        "mode_keys": MODE_KEYS,
        "memory_html": build_memory_card_html(state),
        "show_api_key_input": not api_key_set,
    }


# ─── Memory Card (already pure HTML from memory_manager) ──────────────────────

def memory_card_html(state: dict) -> str:
    """Alias for build_memory_card_html from core.memory_manager.

    Convenience wrapper — keeps ui/sidebar.py as the memory card caller.
    """
    return build_memory_card_html(state)