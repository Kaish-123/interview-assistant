"""Stage timing helpers (stt_ms, llm_ttft_ms, total_ms, …)."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional

from interview_copilot.shared.logging.setup import get_logger


@dataclass
class StageTimer:
    """Accumulate millisecond timings for one request / turn."""

    stage: str = "turn"
    meta: Dict[str, Any] = field(default_factory=dict)
    _t0: float = field(default_factory=time.perf_counter)
    stt_ms: Optional[float] = None
    vad_ms: Optional[float] = None
    llm_ttft_ms: Optional[float] = None
    llm_total_ms: Optional[float] = None

    def mark_stt(self, started_at: float) -> float:
        self.stt_ms = round((time.perf_counter() - started_at) * 1000, 1)
        return self.stt_ms

    def mark_vad(self, started_at: float) -> float:
        self.vad_ms = round((time.perf_counter() - started_at) * 1000, 1)
        return self.vad_ms

    def mark_llm_ttft(self, api_started_at: float) -> float:
        self.llm_ttft_ms = round((time.perf_counter() - api_started_at) * 1000, 1)
        return self.llm_ttft_ms

    def mark_llm_total(self, api_started_at: float) -> float:
        self.llm_total_ms = round((time.perf_counter() - api_started_at) * 1000, 1)
        return self.llm_total_ms

    @property
    def total_ms(self) -> float:
        return round((time.perf_counter() - self._t0) * 1000, 1)

    def as_extra(self) -> Dict[str, Any]:
        extra: Dict[str, Any] = {"stage": self.stage, "total_ms": self.total_ms}
        extra.update(self.meta)
        if self.stt_ms is not None:
            extra["stt_ms"] = self.stt_ms
        if self.vad_ms is not None:
            extra["vad_ms"] = self.vad_ms
        if self.llm_ttft_ms is not None:
            extra["llm_ttft_ms"] = self.llm_ttft_ms
        if self.llm_total_ms is not None:
            extra["llm_total_ms"] = self.llm_total_ms
        return extra

    def log(self, message: str = "stage complete", *, level: str = "info") -> None:
        logger = get_logger("timing")
        log_fn = getattr(logger, level, logger.info)
        log_fn(message, extra=self.as_extra())


def log_stage(
    stage: str,
    message: str,
    *,
    stt_ms: float | None = None,
    llm_ttft_ms: float | None = None,
    llm_total_ms: float | None = None,
    total_ms: float | None = None,
    vad_ms: float | None = None,
    **meta: Any,
) -> None:
    """One-shot structured stage log."""
    extra: Dict[str, Any] = {"stage": stage, **meta}
    if stt_ms is not None:
        extra["stt_ms"] = stt_ms
    if llm_ttft_ms is not None:
        extra["llm_ttft_ms"] = llm_ttft_ms
    if llm_total_ms is not None:
        extra["llm_total_ms"] = llm_total_ms
    if total_ms is not None:
        extra["total_ms"] = total_ms
    if vad_ms is not None:
        extra["vad_ms"] = vad_ms
    get_logger("timing").info(message, extra=extra)


@contextmanager
def timed_stage(stage: str, **meta: Any) -> Iterator[StageTimer]:
    timer = StageTimer(stage=stage, meta=dict(meta))
    try:
        yield timer
    finally:
        timer.log(f"{stage} finished")
