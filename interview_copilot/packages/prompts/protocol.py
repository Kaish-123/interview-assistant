"""PromptStore Protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PromptStore(Protocol):
    def get_tab_count(self) -> int: ...

    def get_tab_name(self, index: int) -> str: ...

    def get_subtab_count(self, tab_index: int) -> int: ...

    def get_subtab_name(self, tab_index: int, subtab_index: int) -> str: ...

    def get_subtab_prompt(self, tab_index: int, subtab_index: int) -> str: ...

    def get_subtab_text_input(self, tab_index: int, subtab_index: int) -> str: ...
