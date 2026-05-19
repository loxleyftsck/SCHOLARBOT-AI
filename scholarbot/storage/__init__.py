"""Storage module — JSON-based persistence layer.

Phase 5 refactor: persistent chat history and user profiles.
Provides clean abstraction over file I/O with automatic directory management.
"""

from .json_store import (
    save_session,
    load_session,
    save_profile,
    load_profile,
    list_sessions,
    delete_session,
    delete_old_sessions,
    get_storage_stats,
    StorageStats,
)

__all__ = [
    "save_session",
    "load_session",
    "save_profile",
    "load_profile",
    "list_sessions",
    "delete_session",
    "delete_old_sessions",
    "get_storage_stats",
    "StorageStats",
]
