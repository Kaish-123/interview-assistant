"""Simple energy VAD — detect end of an interviewer utterance."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class VADGate:
    speech_rms: float = 0.012
    silence_secs: float = 1.5
    min_record_secs: float = 1.0
    onset_chunks: int = 3

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.in_speech = False
        self._onset = 0
        self._speech_started: float | None = None
        self._silence_started: float | None = None

    def feed(self, rms: float, now: float | None = None) -> str:
        """Return '' | 'onset' | 'utterance' given a 0..1 RMS sample."""
        now = time.time() if now is None else now
        if rms >= self.speech_rms:
            self._onset += 1
            self._silence_started = None
            if not self.in_speech and self._onset >= self.onset_chunks:
                self.in_speech = True
                self._speech_started = now
                return "onset"
            return ""
        self._onset = 0
        if not self.in_speech:
            return ""
        if self._silence_started is None:
            self._silence_started = now
            return ""
        held = now - self._silence_started
        spoken = now - (self._speech_started or now)
        if held >= self.silence_secs and spoken >= self.min_record_secs:
            self.reset()
            return "utterance"
        return ""
