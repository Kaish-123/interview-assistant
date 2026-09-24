"""Phase 1 Milestone 1 — logging + stage timings."""

from __future__ import annotations

import time

from interview_copilot.shared.config.settings import build_settings
from interview_copilot.shared.logging.setup import get_logger, setup_logging
from interview_copilot.shared.logging.timing import StageTimer, log_stage, timed_stage


def test_setup_logging_idempotent():
    settings = build_settings()
    log_a = setup_logging(settings, force=True)
    log_b = setup_logging(settings, force=False)
    assert log_a is log_b
    assert log_a.name == "interview_copilot"


def test_stage_timer_records_ms():
    timer = StageTimer(stage="turn", meta={"model": "gpt-4o-mini"})
    t0 = time.perf_counter()
    time.sleep(0.01)
    timer.mark_stt(t0)
    t1 = time.perf_counter()
    time.sleep(0.01)
    timer.mark_llm_ttft(t1)
    timer.mark_llm_total(t1)

    extra = timer.as_extra()
    assert extra["stage"] == "turn"
    assert extra["model"] == "gpt-4o-mini"
    assert extra["stt_ms"] >= 10
    assert extra["llm_ttft_ms"] >= 10
    assert extra["llm_total_ms"] >= 10
    assert extra["total_ms"] >= 20
    timer.log("test timing")


def test_log_stage_and_context_manager():
    # Logger has propagate=False (file+stderr handlers); just ensure no crashes.
    setup_logging(build_settings(), force=True)
    log_stage("stt", "whisper done", stt_ms=123.4, model="whisper-1")
    t0 = time.perf_counter()
    with timed_stage("llm", model="gpt-4o-mini") as timer:
        time.sleep(0.005)
        timer.mark_llm_total(t0)
    assert timer.llm_total_ms is not None and timer.llm_total_ms >= 5
    assert get_logger("timing").name == "interview_copilot.timing"
