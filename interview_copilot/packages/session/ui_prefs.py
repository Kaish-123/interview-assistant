"""ui_prefs.json — geometry / sashes / default interview (contract compatible)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from interview_copilot.shared.config.paths import get_paths
from interview_copilot.shared.logging import get_logger

logger = get_logger("session.ui_prefs")


class UIPreferencesStore:
    def __init__(self, file_path: str | Path | None = None):
        self.file_path = Path(file_path) if file_path else get_paths().ui_prefs_json

    def load(self) -> dict[str, Any]:
        if not self.file_path.is_file():
            return {}
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning(f"ui_prefs load error: {e}")
            return {}

    def save(self, data: dict[str, Any]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.load()
        existing.update(data)
        self.file_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self.load().get(key, default)

    def set_default_interview_subtabs(self, subtab_ids: list[str]) -> None:
        self.save({"default_interview_subtabs": list(subtab_ids)})
