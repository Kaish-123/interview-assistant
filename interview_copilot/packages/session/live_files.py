"""Live overlay session files under sessions/ (session_*.json, notes_*.md)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from interview_copilot.shared.config.paths import get_paths


def new_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def session_path(session_id: str, *, sessions_dir: Path | None = None) -> Path:
    root = sessions_dir or get_paths().sessions_dir
    return root / f"session_{session_id}.json"


def notes_path(session_id: str, *, sessions_dir: Path | None = None) -> Path:
    root = sessions_dir or get_paths().sessions_dir
    return root / f"notes_{session_id}.md"


def save_session(
    session_id: str,
    payload: dict[str, Any],
    *,
    sessions_dir: Path | None = None,
) -> Path:
    path = session_path(session_id, sessions_dir=sessions_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "id": session_id,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        **payload,
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def save_notes(
    session_id: str,
    notes_md: str,
    *,
    sessions_dir: Path | None = None,
) -> Path:
    path = notes_path(session_id, sessions_dir=sessions_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(notes_md, encoding="utf-8")
    return path
