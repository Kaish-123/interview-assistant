"""Session persistence + post-call notes."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import SESSIONS_DIR


def new_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"session_{session_id}.json"


def notes_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"notes_{session_id}.md"


def save_session(session_id: str, payload: dict[str, Any]) -> Path:
    path = session_path(session_id)
    data = {
        "id": session_id,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        **payload,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def save_notes(session_id: str, notes_md: str) -> Path:
    path = notes_path(session_id)
    path.write_text(notes_md, encoding="utf-8")
    return path
