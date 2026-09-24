"""STTProvider Protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from interview_copilot.packages.stt.result import TranscriptionResult


@runtime_checkable
class STTProvider(Protocol):
    def transcribe(
        self,
        wav_path: str | Path,
        *,
        prompt: str | None = None,
        language: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe a WAV/audio file. Raises STTError if strict and all retries fail."""
        ...

    def transcribe_text(
        self,
        wav_path: str | Path,
        *,
        prompt: str | None = None,
        language: str | None = None,
    ) -> str:
        """Convenience: return plain text (empty string on soft failure if configured)."""
        ...
