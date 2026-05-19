"""Prompts layer — pure data, no business logic.

This module contains all personality definitions and mode templates
used by ScholarBot AI.
"""

from .personalities import PERSONALITIES
from .templates import MODES, MODE_PLACEHOLDERS

__all__ = ["PERSONALITIES", "MODES", "MODE_PLACEHOLDERS"]
