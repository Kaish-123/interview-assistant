"""LLM errors."""

from __future__ import annotations


class LLMError(RuntimeError):
    def __init__(self, message: str, *, attempts: int = 0, cause: Exception | None = None):
        super().__init__(message)
        self.attempts = attempts
        self.cause = cause
