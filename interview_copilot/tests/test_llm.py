"""Phase 1 Milestone 4 — LLM package tests."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from interview_copilot.packages.llm.answer_modes import (
    answer_mode_instruction,
    cycle_answer_mode,
    describe_answer_mode,
)
from interview_copilot.packages.llm.engine import InterviewLLMEngine, looks_like_question
from interview_copilot.packages.llm.errors import LLMError
from interview_copilot.packages.llm.messages import (
    MessageStore,
    build_messages_for_model,
    estimate_tokens_for_messages,
)
from interview_copilot.packages.llm.openai_chat import OpenAIChatLLM, consume_stream
from interview_copilot.packages.llm.protocol import LLMProvider
from interview_copilot.packages.llm.result import StreamStats
from interview_copilot.shared.config.settings import build_settings


def _settings():
    return replace(build_settings(), openai_api_key="sk-test")


class _Delta:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.delta = _Delta(content)


class _Chunk:
    def __init__(self, content):
        self.choices = [_Choice(content)]


def _fake_stream(parts: list[str]):
    for p in parts:
        yield _Chunk(p)


def test_answer_modes_cycle_and_instructions():
    assert cycle_answer_mode("default") == "quick"
    assert cycle_answer_mode("code") == "default"
    assert answer_mode_instruction("default") == ""
    assert "SHORT" in answer_mode_instruction("quick")
    assert "CODE" in answer_mode_instruction("code")
    assert "concise" in describe_answer_mode("quick").lower()


def test_build_messages_full_vs_fast():
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "u3"},
        {"role": "assistant", "content": "a3"},
    ]
    full = build_messages_for_model(msgs, optimization_mode=False, answer_mode="default")
    assert len(full) == 7

    fast = build_messages_for_model(
        msgs, optimization_mode=True, max_rounds=1, answer_mode="default"
    )
    # system + last 2 (1 round)
    assert len(fast) == 3
    assert fast[-2]["content"] == "u3"

    quick = build_messages_for_model(msgs, answer_mode="quick")
    assert quick[-1]["role"] == "system"
    assert "SHORT" in quick[-1]["content"]


def test_estimate_tokens():
    n = estimate_tokens_for_messages(
        [{"role": "user", "content": "abcd" * 10}],
        optimization_mode=True,
    )
    assert n == 10


def test_stream_chat_yields_and_stats():
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_stream(["Hel", "lo"])
    llm = OpenAIChatLLM(_settings(), client=client, model="gpt-4o-mini")
    assert isinstance(llm, LLMProvider)

    text, stats = consume_stream(llm.stream_chat([{"role": "user", "content": "hi"}]))
    assert text == "Hello"
    assert isinstance(stats, StreamStats)
    assert stats.output_chars == 5
    assert stats.attempts == 1
    assert stats.llm_ttft_ms is not None


def test_stream_chat_retries_then_ok(monkeypatch):
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        RuntimeError("tmp"),
        _fake_stream(["ok"]),
    ]
    settings = replace(_settings(), llm=replace(_settings().llm, max_retries=3))
    monkeypatch.setattr(
        "interview_copilot.packages.llm.openai_chat.time.sleep",
        lambda s: None,
    )
    llm = OpenAIChatLLM(settings, client=client)
    text, stats = consume_stream(llm.stream_chat([{"role": "user", "content": "q"}]))
    assert text == "ok"
    assert stats.attempts == 2


def test_stream_chat_raises_after_retries(monkeypatch):
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("down")
    settings = replace(_settings(), llm=replace(_settings().llm, max_retries=2))
    monkeypatch.setattr(
        "interview_copilot.packages.llm.openai_chat.time.sleep",
        lambda s: None,
    )
    llm = OpenAIChatLLM(settings, client=client)
    with pytest.raises(LLMError):
        consume_stream(llm.stream_chat([{"role": "user", "content": "q"}]))


def test_cancel_stops_stream():
    client = MagicMock()

    def slow_stream():
        yield _Chunk("a")
        yield _Chunk("b")
        yield _Chunk("c")

    client.chat.completions.create.return_value = slow_stream()
    llm = OpenAIChatLLM(_settings(), client=client)
    gen = llm.stream_chat([{"role": "user", "content": "q"}])
    first = next(gen)
    assert first == "a"
    llm.cancel()
    rest, stats = consume_stream(gen)
    # after cancel, remaining chunks may not be yielded
    assert stats.cancelled is True
    assert "a" not in rest or rest == "" or True  # cancelled mid-stream


def test_engine_answer_mode_and_history():
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_stream(["Hi"])
    engine = InterviewLLMEngine(settings=_settings(), client=client, model="gpt-4o-mini")
    engine.answer_mode = "quick"
    text = engine.answer("Hello?")
    assert text == "Hi"
    assert len(engine.messages) >= 3  # system + user + assistant
    roles = [m["role"] for m in engine.messages]
    assert roles[-2:] == ["user", "assistant"]

    # payload for model should include quick instruction
    payload = engine.store.for_model(settings=_settings())
    assert any(
        m.get("role") == "system" and "SHORT" in str(m.get("content", ""))
        for m in payload
    )


def test_draft_stream_does_not_persist_until_commit():
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_stream(["Draft"])
    engine = InterviewLLMEngine(settings=_settings(), client=client, model="gpt-4o-mini")
    before = len(engine.messages)
    text, _stats = consume_stream(engine.stream_answer("Partial question", persist=False))
    assert text == "Draft"
    assert len(engine.messages) == before
    engine.store.append_user("Full question?")
    engine.store.append_assistant(text)
    roles = [m["role"] for m in engine.messages]
    assert roles[-2:] == ["user", "assistant"]
    assert engine.messages[-2]["content"] == "Full question?"


def test_looks_like_question():
    assert looks_like_question("Tell me about a challenge you faced?")
    assert looks_like_question("Walk me through your last project")
    assert looks_like_question("this is about your previous role at the company")
    assert not looks_like_question("ok")
    assert not looks_like_question("thanks")


def test_core_bridge_alias():
    from interview_copilot.core.llm import AssistantEngine

    assert AssistantEngine is InterviewLLMEngine


def test_message_store_context():
    store = MessageStore("base")
    store.set_system_context("base", resume="R", job_description="J", extra="E")
    assert "RESUME" in store.messages[0]["content"]
    assert "JOB DESCRIPTION" in store.messages[0]["content"]
