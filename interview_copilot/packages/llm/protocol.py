"""LLMProvider Protocol."""

from __future__ import annotations

from typing import Any, Generator, Iterable, Optional, Protocol, runtime_checkable

from interview_copilot.packages.llm.result import StreamStats
from interview_copilot.shared.types import AnswerMode


@runtime_checkable
class LLMProvider(Protocol):
    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.4,
    ) -> Generator[str, None, StreamStats]:
        """Yield content deltas; generator return value is StreamStats."""
        ...

    def complete_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.4,
    ) -> str:
        ...

    def cancel(self) -> None:
        ...
