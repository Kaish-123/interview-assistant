"""
setup_profiles.json — contract compatible with prototype Quick Setup profiles.

Schema:
  { "ProfileName": ["sub_0_0", "sub_0_1", ...], ... }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from interview_copilot.shared.config.paths import get_paths
from interview_copilot.shared.logging import get_logger

logger = get_logger("prompts.profiles")


class SetupProfilesStore:
    def __init__(self, file_path: str | Path | None = None):
        self.file_path = (
            Path(file_path) if file_path else get_paths().setup_profiles_json
        )

    def load(self) -> dict[str, list[str]]:
        if not self.file_path.is_file():
            return {}
        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return {}
            out: dict[str, list[str]] = {}
            for name, ids in raw.items():
                if isinstance(ids, list):
                    out[str(name)] = [str(x) for x in ids]
            return out
        except Exception as e:
            logger.warning(f"setup_profiles load failed: {e}")
            return {}

    def save(self, profiles: dict[str, list[str]]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(
            json.dumps(profiles, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def upsert(self, name: str, subtab_ids: list[str]) -> None:
        profiles = self.load()
        profiles[name] = list(subtab_ids)
        self.save(profiles)

    def delete(self, name: str) -> bool:
        profiles = self.load()
        if name not in profiles:
            return False
        del profiles[name]
        self.save(profiles)
        return True

    def reorder(self, name: str, subtab_ids: list[str]) -> bool:
        profiles = self.load()
        if name not in profiles:
            return False
        profiles[name] = list(subtab_ids)
        self.save(profiles)
        return True

    def list_names(self) -> list[str]:
        return sorted(self.load().keys())
