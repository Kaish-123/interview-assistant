"""Message history + payload builder for the model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from interview_copilot.packages.llm.answer_modes import answer_mode_instruction
from interview_copilot.shared.config.settings import AppSettings, get_settings
from interview_copilot.shared.types import AnswerMode


def estimate_tokens_for_messages(messages: list[dict], optimization_mode: bool = True) -> int:
    tokens = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            tokens += len(content) // 4
        elif isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "text":
                    tokens += len(item.get("text", "")) // 4
                elif item.get("type") == "image_url":
                    tokens += 85 if optimization_mode else 765
    return tokens


def build_messages_for_model(
    messages: list[dict[str, Any]],
    *,
    answer_mode: AnswerMode | str = "default",
    optimization_mode: bool = False,
    max_rounds: int = 4,
    settings: AppSettings | None = None,
) -> list[dict[str, Any]]:
    """
    Assemble API payload.

    - Always keeps system messages
    - Full mode: all user/assistant messages
    - Fast mode: last N rounds only (+ answer-mode instruction)
    """
    settings = settings or get_settings()
    system_msgs: list[dict] = []
    other_msgs: list[dict] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        if role == "system":
            system_msgs.append(m)
        elif role in ("user", "assistant"):
            other_msgs.append(m)

    if not optimization_mode:
        payload = list(system_msgs) + list(other_msgs)
    else:
        keep = max(2, max_rounds * 2)
        recent = other_msgs[-keep:] if len(other_msgs) > keep else other_msgs
        payload = list(system_msgs) + list(recent)

    instruction = answer_mode_instruction(answer_mode)
    if instruction:
        payload.append({"role": "system", "content": instruction.strip()})
    return payload


class MessageStore:
    """In-memory chat history used by Studio / Live engines."""

    def __init__(self, system_prompt: str):
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        self.answer_mode: AnswerMode = "default"

    def reset(self, system_prompt: str) -> None:
        self.messages = [{"role": "system", "content": system_prompt}]

    def set_system_context(
        self,
        base_prompt: str,
        *,
        resume: str = "",
        job_description: str = "",
        extra: str = "",
    ) -> None:
        parts = [base_prompt]
        if resume.strip():
            parts.append(f"\n\nCANDIDATE RESUME:\n{resume.strip()[:12000]}")
        if job_description.strip():
            parts.append(f"\n\nJOB DESCRIPTION:\n{job_description.strip()[:8000]}")
        if extra.strip():
            parts.append(f"\n\nEXTRA CONTEXT / INSTRUCTIONS:\n{extra.strip()[:8000]}")
        self.messages = [{"role": "system", "content": "".join(parts)}]

    def append_user(self, content: Any) -> None:
        self.messages.append({"role": "user", "content": content})

    def append_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def append_system_document(self, name: str, text: str, *, max_chars: int = 50000) -> None:
        self.messages.append(
            {
                "role": "system",
                "content": f"Attached document '{name}':\n{text[:max_chars]}",
            }
        )

    def for_model(
        self,
        *,
        settings: AppSettings | None = None,
        optimization_mode: bool | None = None,
    ) -> list[dict[str, Any]]:
        settings = settings or get_settings()
        opt = (
            settings.llm.optimization_mode
            if optimization_mode is None
            else optimization_mode
        )
        return build_messages_for_model(
            self.messages,
            answer_mode=self.answer_mode,
            optimization_mode=opt,
            max_rounds=settings.llm.max_rounds_for_model,
            settings=settings,
        )

    def copy_messages(self) -> list[dict[str, Any]]:
        return deepcopy(self.messages)
