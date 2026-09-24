"""AudioSource Protocol — UI and use-cases depend on this, not sounddevice."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

import numpy as np

from interview_copilot.shared.types import AudioInputMode


@runtime_checkable
class AudioSource(Protocol):
    """Capture interface for Studio / Live."""

    input_mode: AudioInputMode
    is_recording: bool

    def find_device(self) -> Optional[int]:
        """Resolve sounddevice input device index, or None for system default."""
        ...

    def start_recording(self) -> None:
        ...

    def stop_recording(self, filename: str | Path) -> Optional[str]:
        """Stop capture and write WAV. Returns path or None if too short / empty."""
        ...

    def get_snapshot(self) -> Optional[np.ndarray]:
        """Copy of audio recorded so far (int16 samples), or None."""
        ...
