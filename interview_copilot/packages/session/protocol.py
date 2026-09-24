"""SessionStore Protocol (Studio chat history)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SessionStore(Protocol):
    sessions: list[dict[str, Any]]

    def load(self) -> None: ...

    def save(self) -> None: ...

    def save_current_session(
        self,
        messages: list[dict[str, Any]],
        title: str = "AutoSave - Last Session",
        bookmarks: list | None = None,
    ) -> None: ...

    def add_session(
        self,
        title: str,
        messages: list[dict[str, Any]],
        bookmarks: list | None = None,
    ) -> None: ...

    def get_titles(self) -> list[str]: ...

    def get_session(self, index: int) -> list[dict[str, Any]]: ...
