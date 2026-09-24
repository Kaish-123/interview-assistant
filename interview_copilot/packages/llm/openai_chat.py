"""OpenAI streaming chat completions with retries + cancel."""

from __future__ import annotations

import time
from typing import Any, Generator

from openai import OpenAI

from interview_copilot.packages.llm.errors import LLMError
from interview_copilot.packages.llm.result import StreamStats
from interview_copilot.shared.config.settings import AppSettings, get_settings
from interview_copilot.shared.logging import StageTimer, get_logger

logger = get_logger("llm.openai")


class OpenAIChatLLM:
    """Streaming chat provider with retries and cancel."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        client: Any | None = None,
        model: str | None = None,
    ):
        self._settings = settings or get_settings()
        self.model = model or self._settings.llm.default_model
        self._cancel = False
        if client is not None:
            self._client = client
        else:
            self._client = OpenAI(api_key=self._settings.require_api_key())

    def cancel(self) -> None:
        self._cancel = True

    def reset_cancel(self) -> None:
        self._cancel = False

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.4,
    ) -> Generator[str, None, StreamStats]:
        self.reset_cancel()
        use_model = model or self.model
        max_out = (
            max_tokens
            if max_tokens is not None
            else self._settings.llm.max_output_tokens
        )
        max_retries = max(1, self._settings.llm.max_retries)
        timer = StageTimer(stage="llm", meta={"model": use_model})
        api_start = time.perf_counter()
        stream = None
        attempt = 0

        for attempt in range(1, max_retries + 1):
            if self._cancel:
                return StreamStats(
                    model=use_model,
                    llm_ttft_ms=None,
                    llm_total_ms=timer.mark_llm_total(api_start),
                    attempts=attempt,
                    output_chars=0,
                    cancelled=True,
                )
            try:
                stream = self._client.chat.completions.create(
                    model=use_model,
                    messages=messages,
                    stream=True,
                    max_tokens=max_out,
                    temperature=temperature,
                )
                break
            except Exception as e:
                if attempt < max_retries:
                    wait = 2 * attempt
                    logger.warning(
                        f"chat stream failed attempt {attempt}/{max_retries}: {e}; "
                        f"retry in {wait}s",
                        extra={"stage": "llm", "model": use_model},
                    )
                    time.sleep(wait)
                else:
                    raise LLMError(
                        f"Chat failed after {max_retries} retries: {e}",
                        attempts=max_retries,
                        cause=e,
                    ) from e

        assert stream is not None
        output_chars = 0
        ttft: float | None = None

        for chunk in stream:
            if self._cancel:
                break
            try:
                delta = chunk.choices[0].delta.content if chunk.choices else None
            except Exception:
                delta = None
            if not delta:
                continue
            if ttft is None:
                ttft = timer.mark_llm_ttft(api_start)
                logger.info(
                    "time to first token",
                    extra={
                        "stage": "llm",
                        "llm_ttft_ms": ttft,
                        "model": use_model,
                    },
                )
            output_chars += len(delta)
            yield delta

        total = timer.mark_llm_total(api_start)
        stats = StreamStats(
            model=use_model,
            llm_ttft_ms=ttft,
            llm_total_ms=total,
            attempts=attempt or 1,
            output_chars=output_chars,
            cancelled=self._cancel,
        )
        logger.info(
            "stream complete",
            extra={
                "stage": "llm",
                "llm_ttft_ms": ttft,
                "llm_total_ms": total,
                "model": use_model,
            },
        )
        return stats

    def complete_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.4,
    ) -> str:
        text, _stats = consume_stream(
            self.stream_chat(
                messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        )
        return text.strip()


def create_llm_provider(
    settings: AppSettings | None = None,
    *,
    client: Any | None = None,
    model: str | None = None,
) -> OpenAIChatLLM:
    return OpenAIChatLLM(settings, client=client, model=model)


def consume_stream(gen: Generator[str, None, StreamStats]) -> tuple[str, StreamStats]:
    """Collect a stream_chat generator into (text, stats)."""
    parts: list[str] = []
    try:
        while True:
            parts.append(next(gen))
    except StopIteration as stop:
        stats = stop.value
        if not isinstance(stats, StreamStats):
            stats = StreamStats(
                model="",
                llm_ttft_ms=None,
                llm_total_ms=0,
                attempts=1,
                output_chars=sum(len(p) for p in parts),
            )
        return "".join(parts), stats
