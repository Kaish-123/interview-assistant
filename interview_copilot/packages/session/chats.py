"""
chats.json store — contract compatible with chatgpt_toggle_listener.ChatHistoryManager.

Schema (list):
  [
    {
      "title": str,
      "messages": [ {role, content}, ... ],
      "bookmarks": [ [line_index, preview], ... ]   # optional
    },
    ...
  ]

AutoSave is keyed by title \"AutoSave - Last Session\" (never by index 0).
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

from interview_copilot.shared.config.paths import get_paths
from interview_copilot.shared.logging import get_logger

logger = get_logger("session.chats")

AUTO_SAVE_TITLE = "AutoSave - Last Session"


class ChatHistoryStore:
    """Studio chat history persistence (chats.json)."""

    def __init__(self, file_path: str | Path | None = None):
        self.file_path = Path(file_path) if file_path else get_paths().chats_json
        self.sessions: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if self.file_path.is_file():
            try:
                raw = json.loads(self.file_path.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    self.sessions = raw
                else:
                    logger.warning("chats.json root is not a list; resetting")
                    self.sessions = []
            except Exception as e:
                logger.warning(f"chats.json load failed: {e}")
                self.sessions = []
        else:
            self.sessions = []
        self._deduplicate_autosave(persist=True)

    def save(self, force: bool = False) -> None:  # force kept for prototype API compat
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(
            json.dumps(self.sessions, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _deduplicate_autosave(self, *, persist: bool = False) -> int:
        auto_entries = [
            (i, s)
            for i, s in enumerate(self.sessions)
            if s.get("title") == AUTO_SAVE_TITLE
        ]
        if len(auto_entries) <= 1:
            return 0
        best_idx, _best = max(
            auto_entries, key=lambda t: len(t[1].get("messages", []) or [])
        )
        remove = {i for i, _ in auto_entries if i != best_idx}
        self.sessions = [s for i, s in enumerate(self.sessions) if i not in remove]
        if persist:
            self.save()
        logger.info(
            f"removed {len(remove)} duplicate AutoSave entries",
            extra={"stage": "session"},
        )
        return len(remove)

    def save_current_session(
        self,
        messages: list[dict[str, Any]],
        title: str = AUTO_SAVE_TITLE,
        bookmarks: list | None = None,
    ) -> None:
        auto_idx = next(
            (i for i, s in enumerate(self.sessions) if s.get("title") == title),
            None,
        )
        if bookmarks is None and auto_idx is not None:
            bookmarks = self.sessions[auto_idx].get("bookmarks", [])

        working = {
            "title": title,
            "messages": deepcopy(messages),
            "bookmarks": list(bookmarks or []),
        }
        if auto_idx is not None:
            self.sessions[auto_idx] = working
        else:
            self.sessions.insert(0, working)
        self.save()

    def add_session(
        self,
        title: str,
        messages: list[dict[str, Any]],
        bookmarks: list | None = None,
    ) -> int:
        self.sessions.append(
            {
                "title": title,
                "messages": deepcopy(messages),
                "bookmarks": list(bookmarks or []),
            }
        )
        self.save()
        return len(self.sessions) - 1

    def get_titles(self) -> list[str]:
        return [s.get("title", "Untitled") for s in self.sessions]

    def get_session(self, index: int) -> list[dict[str, Any]]:
        if 0 <= index < len(self.sessions):
            return deepcopy(self.sessions[index].get("messages", []))
        return []

    def get_session_bookmarks(self, index: int) -> list:
        if 0 <= index < len(self.sessions):
            return list(self.sessions[index].get("bookmarks", []) or [])
        return []

    def update_session_bookmarks(self, index: int, bookmarks: list) -> None:
        if 0 <= index < len(self.sessions):
            self.sessions[index]["bookmarks"] = list(bookmarks)
            self.save()

    def rename_session(self, index: int, new_title: str) -> bool:
        if 0 <= index < len(self.sessions) and new_title.strip():
            self.sessions[index]["title"] = new_title.strip()
            self.save()
            return True
        return False

    def find_autosave(self) -> Optional[dict[str, Any]]:
        return next(
            (s for s in self.sessions if s.get("title") == AUTO_SAVE_TITLE),
            None,
        )

    def reorder(self, from_index: int, to_index: int) -> bool:
        if not (
            0 <= from_index < len(self.sessions) and 0 <= to_index < len(self.sessions)
        ):
            return False
        item = self.sessions.pop(from_index)
        self.sessions.insert(to_index, item)
        self.save()
        return True


def prune_sessions(
    store: ChatHistoryStore,
    *,
    max_chats: int = 10,
    keep_index: int | None = None,
) -> int:
    """
    Keep ≤ max_chats real sessions + exactly one AutoSave.

    If keep_index is set (e.g. currently selected), that real chat is preferred;
    otherwise the most recently appended real chat is kept when over limit
    (prototype auto_prune behavior: keep last real + AutoSave).
    """
    real_indices = [
        i
        for i, s in enumerate(store.sessions)
        if s.get("title") != AUTO_SAVE_TITLE
    ]
    if len(real_indices) <= max_chats and keep_index is None:
        # Still collapse duplicate autosaves
        return store._deduplicate_autosave(persist=True)

    if keep_index is not None and 0 <= keep_index < len(store.sessions):
        keep_real = keep_index
    elif real_indices:
        keep_real = real_indices[-1]
    else:
        keep_real = None

    new_sessions: list[dict[str, Any]] = []
    auto_kept = False
    for i, s in enumerate(store.sessions):
        title = s.get("title", "Untitled")
        if keep_real is not None and i == keep_real and title != AUTO_SAVE_TITLE:
            new_sessions.append(s)
        elif title == AUTO_SAVE_TITLE and not auto_kept:
            new_sessions.append(s)
            auto_kept = True

    # If over max_chats with keep_index path for delete-all-but-one, already handled.
    # For auto-prune when many reals: keep only last real + autosave (prototype).
    if keep_index is None and len(real_indices) > max_chats:
        last_real = real_indices[-1]
        new_sessions = []
        auto_kept = False
        for i, s in enumerate(store.sessions):
            title = s.get("title", "")
            if i == last_real:
                new_sessions.append(s)
            elif title == AUTO_SAVE_TITLE and not auto_kept:
                new_sessions.append(s)
                auto_kept = True

    removed = len(store.sessions) - len(new_sessions)
    if removed > 0:
        store.sessions = new_sessions
        store.save()
        logger.info(f"pruned {removed} chat(s)", extra={"stage": "session"})
    return removed
