"""Session persistence — chats.json contracts + Live session files."""

from interview_copilot.packages.session.call_sessions import (
    CallSessionStore,
    compose_session_extra,
    public_session,
)
from interview_copilot.packages.session.chats import (
    AUTO_SAVE_TITLE,
    ChatHistoryStore,
    prune_sessions,
)
from interview_copilot.packages.session.library import LibraryStore
from interview_copilot.packages.session.live_files import (
    new_session_id,
    notes_path,
    save_notes,
    save_session,
    session_path,
)
from interview_copilot.packages.session.protocol import SessionStore
from interview_copilot.packages.session.ui_prefs import UIPreferencesStore

__all__ = [
    "AUTO_SAVE_TITLE",
    "CallSessionStore",
    "ChatHistoryStore",
    "LibraryStore",
    "SessionStore",
    "UIPreferencesStore",
    "compose_session_extra",
    "new_session_id",
    "notes_path",
    "prune_sessions",
    "public_session",
    "save_notes",
    "save_session",
    "session_path",
]
