"""OpenAI Whisper-1 STT adapter with exponential backoff retries."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

from openai import OpenAI

from interview_copilot.packages.stt.live_session import is_model_unavailable, model_chain
from interview_copilot.packages.stt.result import STTError, TranscriptionResult
from interview_copilot.shared.config.settings import AppSettings, get_settings
from interview_copilot.shared.logging import StageTimer, get_logger

logger = get_logger("stt.whisper")


class OpenAIWhisperSTT:
    """
    Cloud Whisper via OpenAI Audio Transcriptions API.

    Matches chatgpt_toggle_listener retry behavior:
    max_retries attempts, backoff (attempt+1)*retry_backoff_secs.
    """

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        client: Any | None = None,
        raise_on_error: bool = True,
    ):
        self._settings = settings or get_settings()
        self._raise_on_error = raise_on_error
        if client is not None:
            self._client = client
        else:
            api_key = self._settings.require_api_key()
            self._client = OpenAI(api_key=api_key, timeout=45.0)

    @property
    def model(self) -> str:
        return self._settings.stt.model

    def _resolve_language(self, language: str | None) -> Optional[str]:
        if language is not None:
            lang = language.strip()
        else:
            lang = (self._settings.stt.language or self._settings.default_language or "").strip()
        if not lang or lang.lower() in {"auto", "detect", ""}:
            return None
        return lang

    def transcribe(
        self,
        wav_path: str | Path,
        *,
        prompt: str | None = None,
        language: str | None = None,
    ) -> TranscriptionResult:
        path = Path(wav_path)
        if not path.is_file():
            raise STTError(f"Audio file not found: {path}", attempts=0)

        timer = StageTimer(stage="stt", meta={"model": self.model})
        max_retries = max(1, self._settings.stt.max_retries)
        backoff = self._settings.stt.retry_backoff_secs
        lang = self._resolve_language(language)
        last_error: Exception | None = None
        t0 = time.perf_counter()
        models = model_chain(self.model)

        for attempt in range(1, max_retries + 1):
            for model in models:
                try:
                    with path.open("rb") as audio_file:
                        kwargs: dict[str, Any] = {
                            "model": model,
                            "file": audio_file,
                        }
                        if prompt:
                            kwargs["prompt"] = prompt
                        if lang:
                            kwargs["language"] = lang

                        result = self._client.audio.transcriptions.create(**kwargs)

                    text = (getattr(result, "text", None) or "").strip()
                    stt_ms = timer.mark_stt(t0)
                    out = TranscriptionResult(
                        text=text,
                        model=model,
                        language=lang,
                        stt_ms=stt_ms,
                        attempts=attempt,
                        prompt_used=bool(prompt),
                    )
                    logger.info(
                        f"transcription ok ({len(text)} chars)",
                        extra={
                            "stage": "stt",
                            "stt_ms": stt_ms,
                            "model": model,
                        },
                    )
                    return out
                except STTError:
                    raise
                except Exception as e:
                    last_error = e
                    if is_model_unavailable(e) and model != models[-1]:
                        logger.warning(
                            f"stt model {model} unavailable; trying next",
                            extra={"stage": "stt", "model": model},
                        )
                        continue
                    if attempt < max_retries:
                        wait = backoff * attempt
                        logger.warning(
                            f"transcription failed attempt {attempt}/{max_retries}: {e}; "
                            f"retry in {wait:.1f}s",
                            extra={"stage": "stt", "model": model},
                        )
                        time.sleep(wait)
                    break
            else:
                continue
            if attempt >= max_retries:
                break

        stt_ms = timer.mark_stt(t0)
        msg = f"Transcription failed after {max_retries} retries: {last_error}"
        logger.error(msg, extra={"stage": "stt", "stt_ms": stt_ms, "model": self.model})
        if self._raise_on_error:
            raise STTError(msg, attempts=max_retries, cause=last_error)
        return TranscriptionResult(
            text="",
            model=self.model,
            language=lang,
            stt_ms=stt_ms,
            attempts=max_retries,
            prompt_used=bool(prompt),
        )

    def transcribe_text(
        self,
        wav_path: str | Path,
        *,
        prompt: str | None = None,
        language: str | None = None,
    ) -> str:
        """
        Return transcript text.

        On failure with raise_on_error=False → empty string.
        On failure with raise_on_error=True → raises STTError.
        Soft error string mode (prototype ❌ prefix) available via soft_transcribe_text.
        """
        return self.transcribe(wav_path, prompt=prompt, language=language).text

    def soft_transcribe_text(
        self,
        wav_path: str | Path,
        *,
        prompt: str | None = None,
        language: str | None = None,
    ) -> str:
        """Prototype-compatible: return ❌ message instead of raising."""
        try:
            previous = self._raise_on_error
            self._raise_on_error = True
            try:
                return self.transcribe(wav_path, prompt=prompt, language=language).text
            finally:
                self._raise_on_error = previous
        except STTError as e:
            return f"❌ Transcription error after {e.attempts} retries: {e.cause or e}"


def create_stt_provider(
    settings: AppSettings | None = None,
    *,
    client: Any | None = None,
    raise_on_error: bool = True,
) -> OpenAIWhisperSTT:
    """Factory for the default STT provider (OpenAI Whisper)."""
    return OpenAIWhisperSTT(settings, client=client, raise_on_error=raise_on_error)
