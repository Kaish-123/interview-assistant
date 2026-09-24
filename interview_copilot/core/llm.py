"""Backward-compatible AssistantEngine → packages.llm.InterviewLLMEngine."""

from __future__ import annotations

from interview_copilot.packages.llm.engine import InterviewLLMEngine, looks_like_question

# Preserve historical name used by Live UI
AssistantEngine = InterviewLLMEngine

__all__ = ["AssistantEngine", "InterviewLLMEngine", "looks_like_question"]
