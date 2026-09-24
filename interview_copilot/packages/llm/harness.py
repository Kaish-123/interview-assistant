"""
Phase 1 Milestone 4 — LLM harness.

  python3 -m interview_copilot.packages.llm.harness
  python3 -m interview_copilot.packages.llm.harness --mode quick --question "Tell me about yourself"
  python3 -m interview_copilot.packages.llm.harness --mode code --question "Binary search in Python"
"""

from __future__ import annotations

import argparse

from interview_copilot.packages.llm import InterviewLLMEngine, describe_answer_mode
from interview_copilot.shared.config import get_settings
from interview_copilot.shared.logging import setup_logging
from interview_copilot.shared.types import AnswerMode


def main() -> None:
    parser = argparse.ArgumentParser(description="Interview Copilot LLM harness")
    parser.add_argument(
        "--mode",
        choices=["default", "quick", "detailed", "code"],
        default="default",
    )
    parser.add_argument(
        "--question",
        default="What is a REST API? Answer briefly for an interview.",
    )
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings, force=True)

    print("Interview Copilot — Phase 1 Milestone 4 (LLM)")
    print(f"  platform: {settings.platform}")
    print(f"  has_key:  {settings.has_api_key}")
    print(f"  mode:     {args.mode} — {describe_answer_mode(args.mode)}")

    engine = InterviewLLMEngine(model=args.model, language=settings.default_language)
    engine.answer_mode = args.mode  # type: ignore[assignment]
    print(f"  model:    {engine.model}")
    print(f"  Q:        {args.question}")
    print("  A: ", end="", flush=True)

    stats = None
    gen = engine.stream_answer(args.question)
    try:
        while True:
            delta = next(gen)
            print(delta, end="", flush=True)
    except StopIteration as stop:
        stats = stop.value

    print()
    if stats:
        print(
            f"  stats: ttft={stats.llm_ttft_ms}ms total={stats.llm_total_ms}ms "
            f"chars={stats.output_chars} attempts={stats.attempts}"
        )


if __name__ == "__main__":
    main()
