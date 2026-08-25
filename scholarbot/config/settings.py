"""Configuration — constants, environment variables, app defaults.

Extracted from app.py Phase 6 refactor.
Single source of truth for all tunables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Configuration ─────────────────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ─── Model Configuration ───────────────────────────────────────────────────────

MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")
MODEL_TEMPERATURE = 0.7
MODEL_MAX_TOKENS = 2048

# ─── App Metadata ───────────────────────────────────────────────────────────────

APP_TITLE = "ScholarBot AI"
APP_ICON = "🎓"
APP_LAYOUT = "wide"
APP_SIDEBAR_STATE = "expanded"

# ─── Feature Flags ─────────────────────────────────────────────────────────────

TOPICS_MEMORY_CAP = 20
CONVERSATION_CAP = 50
TOPICS_DISPLAY_LIMIT = 3