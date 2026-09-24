"""Backward-compatible session helpers → packages.session."""

from interview_copilot.packages.session import (
    AUTO_SAVE_TITLE,
    ChatHistoryStore,
    new_session_id,
    notes_path,
    prune_sessions,
    save_notes,
    save_session,
    session_path,
)

# Legacy alias
ChatHistoryManager = ChatHistoryStore

__all__ = [
    "AUTO_SAVE_TITLE",
    "ChatHistoryManager",
    "ChatHistoryStore",
    "new_session_id",
    "notes_path",
    "prune_sessions",
    "save_notes",
    "save_session",
    "session_path",
]
