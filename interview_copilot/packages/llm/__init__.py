"""LLM package — streaming chat, answer modes, message assembly."""

from interview_copilot.packages.llm.answer_modes import (
    ANSWER_MODES,
    answer_mode_instruction,
    cycle_answer_mode,
    describe_answer_mode,
    label_answer_mode,
)
from interview_copilot.packages.llm.answer_prefs import (
    build_preference_instruction,
    describe_prefs,
    normalize_answer_prefs,
    preview_answer,
)
from interview_copilot.packages.llm.engine import InterviewLLMEngine
from interview_copilot.packages.llm.errors import LLMError
from interview_copilot.packages.llm.messages import MessageStore, build_messages_for_model
from interview_copilot.packages.llm.openai_chat import OpenAIChatLLM, create_llm_provider
from interview_copilot.packages.llm.protocol import LLMProvider
from interview_copilot.packages.llm.result import StreamStats

__all__ = [
    "ANSWER_MODES",
    "build_preference_instruction",
    "describe_prefs",
    "normalize_answer_prefs",
    "preview_answer",
    "InterviewLLMEngine",
    "LLMError",
    "LLMProvider",
    "MessageStore",
    "OpenAIChatLLM",
    "StreamStats",
    "answer_mode_instruction",
    "build_messages_for_model",
    "create_llm_provider",
    "cycle_answer_mode",
    "describe_answer_mode",
    "label_answer_mode",
]
