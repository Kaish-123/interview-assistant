"""Local CV / document library for the web dashboard."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from interview_copilot.shared.config.paths import get_paths
from interview_copilot.shared.logging import get_logger

logger = get_logger("session.library")

KINDS = ("resume", "document", "instructions")


class LibraryStore:
    def __init__(self, file_path: str | Path | None = None):
        self.file_path = Path(file_path) if file_path else get_paths().library_json
        self.items: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if self.file_path.is_file():
            try:
                raw = json.loads(self.file_path.read_text(encoding="utf-8"))
                self.items = raw if isinstance(raw, list) else []
            except Exception as e:
                logger.warning(f"library.json load failed: {e}")
                self.items = []
        else:
            self.items = []

    def save(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(
            json.dumps(self.items, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list_public(self, kind: str | None = None) -> list[dict[str, Any]]:
        items = []
        for item in self.items:
            if kind and item.get("kind") != kind:
                continue
            text = str(item.get("text") or "")
            items.append(
                {
                    "id": item.get("id"),
                    "kind": item.get("kind"),
                    "name": item.get("name"),
                    "chars": len(text),
                    "created_at": item.get("created_at"),
                }
            )
        return items

    def get(self, item_id: str) -> dict[str, Any] | None:
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None

    def add(self, *, kind: str, name: str, text: str) -> dict[str, Any]:
        item = {
            "id": uuid.uuid4().hex[:12],
            "kind": kind if kind in KINDS else "document",
            "name": name or "Untitled",
            "text": text,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.items.insert(0, item)
        self.save()
        return item

    def delete(self, item_id: str) -> bool:
        before = len(self.items)
        self.items = [i for i in self.items if i.get("id") != item_id]
        if len(self.items) == before:
            return False
        self.save()
        return True
