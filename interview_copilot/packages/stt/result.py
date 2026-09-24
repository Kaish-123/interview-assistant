"""STT result and error types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    model: str
    language: Optional[str]
    stt_ms: float
    attempts: int
    prompt_used: bool = False

    @property
    def ok(self) -> bool:
        return bool(self.text.strip())


class STTError(RuntimeError):
    """Raised when transcription fails after all retries (strict mode)."""

    def __init__(self, message: str, *, attempts: int = 0, cause: Exception | None = None):
        super().__init__(message)
        self.attempts = attempts
        self.cause = cause
