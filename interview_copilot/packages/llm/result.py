"""Stream statistics for LLM calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StreamStats:
    model: str
    llm_ttft_ms: Optional[float]
    llm_total_ms: float
    attempts: int
    output_chars: int
    cancelled: bool = False
