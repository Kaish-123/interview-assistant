"""
tabs.json store — contract compatible with chatgpt_toggle_listener.PromptManager.

Schema:
  {
    "tabs": [
      {
        "name": str,
        "subTabs": [
          { "name": str, "prompt": str, "text_input": str },
          ...
        ]
      }
    ]
  }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from interview_copilot.shared.config.paths import get_paths
from interview_copilot.shared.logging import get_logger

logger = get_logger("prompts.tabs")


class PromptTabsStore:
    def __init__(self, tabs_file_path: str | Path | None = None):
        self.tabs_file_path = (
            Path(tabs_file_path) if tabs_file_path else get_paths().tabs_json
        )
        self.data: dict[str, Any] = {"tabs": []}
        self.load_tabs()

    def load_tabs(self) -> None:
        if self.tabs_file_path.is_file():
            try:
                raw = json.loads(self.tabs_file_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and isinstance(raw.get("tabs"), list):
                    self.data = raw
                else:
                    self.data = {"tabs": []}
            except Exception as e:
                logger.warning(f"tabs.json load failed: {e}")
                self.data = {"tabs": []}
        else:
            self.data = {"tabs": []}

    def save_tabs(self) -> None:
        self.tabs_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.tabs_file_path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_tab(self, name: str) -> int:
        self.data["tabs"].append({"name": name, "subTabs": []})
        self.save_tabs()
        return len(self.data["tabs"]) - 1

    def add_subtab(
        self,
        tab_index: int,
        name: str,
        prompt: str = "",
        text_input: str = "",
    ) -> int:
        if not (0 <= tab_index < len(self.data["tabs"])):
            return -1
        self.data["tabs"][tab_index]["subTabs"].append(
            {"name": name, "prompt": prompt, "text_input": text_input}
        )
        self.save_tabs()
        return len(self.data["tabs"][tab_index]["subTabs"]) - 1

    def get_tab_count(self) -> int:
        return len(self.data["tabs"])

    def get_tab_name(self, index: int) -> str:
        if 0 <= index < len(self.data["tabs"]):
            return str(self.data["tabs"][index].get("name", ""))
        return ""

    def get_subtab_count(self, tab_index: int) -> int:
        if 0 <= tab_index < len(self.data["tabs"]):
            return len(self.data["tabs"][tab_index].get("subTabs", []))
        return 0

    def get_subtab_text_input(self, tab_index: int, subtab_index: int) -> str:
        sub = self._subtab(tab_index, subtab_index)
        return str(sub.get("text_input", "")) if sub else ""

    def get_subtab_name(self, tab_index: int, subtab_index: int) -> str:
        sub = self._subtab(tab_index, subtab_index)
        return str(sub.get("name", "")) if sub else ""

    def get_subtab_prompt(self, tab_index: int, subtab_index: int) -> str:
        sub = self._subtab(tab_index, subtab_index)
        return str(sub.get("prompt", "")) if sub else ""

    def update_subtab_prompt(
        self,
        tab_index: int,
        subtab_index: int,
        prompt: str,
        text_input: str = "",
    ) -> bool:
        sub = self._subtab(tab_index, subtab_index)
        if sub is None:
            return False
        sub["prompt"] = prompt
        sub["text_input"] = text_input
        self.save_tabs()
        return True

    def get_subtab_body(self, tab_index: int, subtab_index: int) -> str:
        """Prefer text_input, then prompt, then name (Studio click-to-send behavior)."""
        text = self.get_subtab_text_input(tab_index, subtab_index)
        if text.strip():
            return text
        prompt = self.get_subtab_prompt(tab_index, subtab_index)
        if prompt.strip():
            return prompt
        return self.get_subtab_name(tab_index, subtab_index)

    def subtab_id(self, tab_index: int, subtab_index: int) -> str:
        return f"sub_{tab_index}_{subtab_index}"

    def resolve_subtab_id(self, subtab_id: str) -> tuple[int, int] | None:
        if not isinstance(subtab_id, str) or not subtab_id.startswith("sub_"):
            return None
        parts = subtab_id.split("_")
        if len(parts) != 3:
            return None
        try:
            t, s = int(parts[1]), int(parts[2])
        except ValueError:
            return None
        if self._subtab(t, s) is None:
            return None
        return t, s

    def combined_prompt_for_ids(self, subtab_ids: list[str]) -> tuple[str, list[str]]:
        texts: list[str] = []
        names: list[str] = []
        for sid in subtab_ids:
            resolved = self.resolve_subtab_id(sid)
            if not resolved:
                continue
            t, s = resolved
            body = self.get_subtab_body(t, s).strip()
            name = self.get_subtab_name(t, s) or sid
            if body:
                texts.append(body)
                names.append(name)
        combined = "\n\n---\n\n".join(texts) if texts else ""
        return combined, names

    def _subtab(self, tab_index: int, subtab_index: int) -> dict | None:
        if not (0 <= tab_index < len(self.data["tabs"])):
            return None
        subs = self.data["tabs"][tab_index].get("subTabs", [])
        if not (0 <= subtab_index < len(subs)):
            return None
        return subs[subtab_index]
