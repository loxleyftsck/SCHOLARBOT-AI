"""JSON-based storage layer for persistent chat history and user profiles.

Engineering Decision:
- JSON files (not SQLite) — simple, human-readable, zero dependencies
- One JSON file per session — easy to inspect, backup, delete
- Auto-create directories on first access
- Graceful degradation — if storage fails, app continues in memory-only mode
- No locks or async — simple synchronous file I/O sufficient for single-user app

Phase 5 refactor addition.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


# ─── Storage Paths ─────────────────────────────────────────────────────────────

# Base storage directory (relative to this file's location)
_BASE_DIR = Path(__file__).parent
_DATA_DIR = _BASE_DIR / "data"
_SESSIONS_DIR = _DATA_DIR / "sessions"
_PROFILES_DIR = _DATA_DIR / "profiles"


def _ensure_dirs() -> None:
    """Ensure all storage directories exist. Called on first access."""
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    _PROFILES_DIR.mkdir(parents=True, exist_ok=True)


# ─── Storage Report ─────────────────────────────────────────────────────────────

@dataclass
class StorageStats:
    """Statistics about storage usage."""
    sessions_count: int
    profiles_count: int
    total_size_bytes: int
    sessions_dir: str
    profiles_dir: str


# ─── Session Storage ───────────────────────────────────────────────────────────

def _session_path(session_id: str) -> Path:
    """Get file path for a session."""
    # Sanitize session_id to valid filename
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
    return _SESSIONS_DIR / f"{safe_id}.json"


def save_session(session_id: str, state: dict) -> bool:
    """Save session state to JSON file.

    Saves: messages, topics_discussed, msg_count, personality, user_name, session_start.

    Args:
        session_id: Unique session identifier (e.g. browser session hash)
        state: Session state dict

    Returns:
        True on success, False on failure (non-blocking)
    """
    try:
        _ensure_dirs()

        payload = {
            "session_id": session_id,
            "saved_at": datetime.now().isoformat(),
            "messages": state.get("messages", []),
            "user_name": state.get("user_name", ""),
            "personality": state.get("personality", "😊 Santai & Friendly"),
            "topics_discussed": state.get("topics_discussed", []),
            "msg_count": state.get("msg_count", 0),
            "session_start": state.get("session_start", ""),
        }

        path = _session_path(session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        # Non-blocking: storage failure should not crash the app
        return False


def load_session(session_id: str) -> Optional[dict]:
    """Load session state from JSON file.

    Args:
        session_id: Session identifier

    Returns:
        Session state dict or None if not found/error
    """
    try:
        path = _session_path(session_id)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Map saved fields back to session state format
        return {
            "messages": data.get("messages", []),
            "user_name": data.get("user_name", ""),
            "personality": data.get("personality", "😊 Santai & Friendly"),
            "topics_discussed": data.get("topics_discussed", []),
            "msg_count": data.get("msg_count", 0),
            "session_start": data.get("session_start", ""),
        }
    except Exception:
        return None


def delete_session(session_id: str) -> bool:
    """Delete a session file.

    Args:
        session_id: Session identifier

    Returns:
        True on success, False on failure
    """
    try:
        path = _session_path(session_id)
        if path.exists():
            path.unlink()
        return True
    except Exception:
        return False


def list_sessions() -> list[dict]:
    """List all saved sessions with metadata.

    Returns:
        List of dicts with session_id, saved_at, msg_count, user_name
    """
    try:
        _ensure_dirs()
        sessions = []
        for path in _SESSIONS_DIR.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id", path.stem),
                    "saved_at": data.get("saved_at", "unknown"),
                    "msg_count": data.get("msg_count", 0),
                    "user_name": data.get("user_name", ""),
                    "personality": data.get("personality", ""),
                })
            except Exception:
                continue
        # Sort by most recent
        sessions.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        return sessions
    except Exception:
        return []


# ─── Profile Storage ───────────────────────────────────────────────────────────

def _profile_path(user_name: str) -> Path:
    """Get file path for a user profile."""
    # Sanitize user name to valid filename
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in user_name)
    if not safe_name:
        safe_name = "anonymous"
    return _PROFILES_DIR / f"{safe_name}.json"


def save_profile(user_name: str, state: dict) -> bool:
    """Save user profile preferences to JSON file.

    Saves: preferred personality, display name, recent topics.

    Args:
        user_name: User's display name (used as profile key)
        state: Session state dict

    Returns:
        True on success, False on failure (non-blocking)
    """
    if not user_name:
        return False

    try:
        _ensure_dirs()

        payload = {
            "user_name": user_name,
            "saved_at": datetime.now().isoformat(),
            "preferred_personality": state.get("personality", "😊 Santai & Friendly"),
            "recent_topics": state.get("topics_discussed", [])[-10:],  # Last 10 topics
        }

        path = _profile_path(user_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_profile(user_name: str) -> Optional[dict]:
    """Load user profile preferences.

    Args:
        user_name: User's display name

    Returns:
        Profile dict or None if not found/error
    """
    if not user_name:
        return None

    try:
        path = _profile_path(user_name)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "preferred_personality": data.get("preferred_personality", "😊 Santai & Friendly"),
            "recent_topics": data.get("recent_topics", []),
            "saved_at": data.get("saved_at", ""),
        }
    except Exception:
        return None


# ─── Storage Statistics ─────────────────────────────────────────────────────────

def get_storage_stats() -> StorageStats:
    """Get storage usage statistics.

    Returns:
        StorageStats dataclass with usage metrics
    """
    try:
        _ensure_dirs()

        sessions = list(_SESSIONS_DIR.glob("*.json"))
        profiles = list(_PROFILES_DIR.glob("*.json"))

        total_size = 0
        for path in sessions + profiles:
            try:
                total_size += path.stat().st_size
            except Exception:
                pass

        return StorageStats(
            sessions_count=len(sessions),
            profiles_count=len(profiles),
            total_size_bytes=total_size,
            sessions_dir=str(_SESSIONS_DIR),
            profiles_dir=str(_PROFILES_DIR),
        )
    except Exception:
        return StorageStats(
            sessions_count=0,
            profiles_count=0,
            total_size_bytes=0,
            sessions_dir="unavailable",
            profiles_dir="unavailable",
        )


# ─── Cleanup Utilities ─────────────────────────────────────────────────────────

def delete_old_sessions(days_old: int = 30) -> int:
    """Delete session files older than N days.

    Args:
        days_old: Delete sessions not modified in this many days

    Returns:
        Number of sessions deleted
    """
    try:
        _ensure_dirs()
        cutoff = datetime.now().timestamp() - (days_old * 86400)
        deleted = 0

        for path in _SESSIONS_DIR.glob("*.json"):
            if path.stat().st_mtime < cutoff:
                path.unlink()
                deleted += 1

        return deleted
    except Exception:
        return 0
