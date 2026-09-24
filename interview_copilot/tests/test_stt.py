"""Phase 1 Milestone 3 — STT (Whisper + retries) tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from interview_copilot.packages.audio.wav_io import write_wav_int16
from interview_copilot.packages.stt.protocol import STTProvider
from interview_copilot.packages.stt.result import STTError, TranscriptionResult
from interview_copilot.packages.stt.whisper_openai import OpenAIWhisperSTT, create_stt_provider
from interview_copilot.shared.config.settings import STTSettings, build_settings


def _settings_with_stt(**kwargs):
    base = build_settings()
    stt = replace(base.stt, **kwargs)
    return replace(base, openai_api_key="sk-test", stt=stt)


def _wav(tmp_path: Path) -> Path:
    sr = 16000
    audio = (np.random.randn(sr).astype(np.float32) * 0.01)
    return write_wav_int16(tmp_path / "t.wav", audio, sample_rate=sr)


def test_whisper_stt_success(tmp_path: Path):
    client = MagicMock()
    client.audio.transcriptions.create.return_value = SimpleNamespace(text="  Hello world  ")
    stt = OpenAIWhisperSTT(_settings_with_stt(), client=client)
    wav = _wav(tmp_path)

    result = stt.transcribe(wav)
    assert isinstance(result, TranscriptionResult)
    assert result.text == "Hello world"
    assert result.attempts == 1
    assert result.stt_ms >= 0
    assert result.ok
    assert isinstance(stt, STTProvider)
    client.audio.transcriptions.create.assert_called_once()


def test_whisper_stt_retries_then_succeeds(tmp_path: Path):
    client = MagicMock()
    client.audio.transcriptions.create.side_effect = [
        RuntimeError("temp fail"),
        SimpleNamespace(text="recovered"),
    ]
    settings = _settings_with_stt(max_retries=3, retry_backoff_secs=0.01)
    stt = OpenAIWhisperSTT(settings, client=client)
    result = stt.transcribe(_wav(tmp_path))
    assert result.text == "recovered"
    assert result.attempts == 2
    assert client.audio.transcriptions.create.call_count == 2


def test_whisper_stt_raises_after_retries(tmp_path: Path):
    client = MagicMock()
    client.audio.transcriptions.create.side_effect = RuntimeError("down")
    settings = _settings_with_stt(max_retries=2, retry_backoff_secs=0.01)
    stt = OpenAIWhisperSTT(settings, client=client, raise_on_error=True)
    with pytest.raises(STTError) as ei:
        stt.transcribe(_wav(tmp_path))
    assert ei.value.attempts == 2
    assert client.audio.transcriptions.create.call_count == 2


def test_whisper_stt_soft_mode_returns_empty(tmp_path: Path):
    client = MagicMock()
    client.audio.transcriptions.create.side_effect = RuntimeError("down")
    settings = _settings_with_stt(max_retries=1, retry_backoff_secs=0.01)
    stt = OpenAIWhisperSTT(settings, client=client, raise_on_error=False)
    result = stt.transcribe(_wav(tmp_path))
    assert result.text == ""
    assert not result.ok


def test_soft_transcribe_text_error_prefix(tmp_path: Path):
    client = MagicMock()
    client.audio.transcriptions.create.side_effect = RuntimeError("boom")
    settings = _settings_with_stt(max_retries=1, retry_backoff_secs=0.01)
    stt = OpenAIWhisperSTT(settings, client=client)
    msg = stt.soft_transcribe_text(_wav(tmp_path))
    assert msg.startswith("❌ Transcription error")


def test_missing_file_raises():
    stt = OpenAIWhisperSTT(_settings_with_stt(), client=MagicMock())
    with pytest.raises(STTError, match="not found"):
        stt.transcribe("/no/such/file.wav")


def test_prompt_and_language_passed(tmp_path: Path):
    client = MagicMock()
    client.audio.transcriptions.create.return_value = SimpleNamespace(text="q")
    settings = _settings_with_stt(language="")
    stt = OpenAIWhisperSTT(settings, client=client)
    stt.transcribe(_wav(tmp_path), prompt="live hint", language="en")
    kwargs = client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["prompt"] == "live hint"
    assert kwargs["language"] == "en"
    assert kwargs["model"] == settings.stt.model


def test_create_stt_provider_factory():
    provider = create_stt_provider(_settings_with_stt(), client=MagicMock())
    assert isinstance(provider, OpenAIWhisperSTT)


def test_stt_settings_loaded_from_env(monkeypatch):
    monkeypatch.setenv("WHISPER_MODEL", "whisper-1")
    monkeypatch.setenv("WHISPER_MAX_RETRIES", "5")
    monkeypatch.setenv("WHISPER_LANGUAGE", "hi")
    from interview_copilot.shared.config.settings import build_settings

    s = build_settings()
    assert s.stt.model == "whisper-1"
    assert s.stt.max_retries == 5
    assert s.stt.language == "hi"


def test_file_stt_falls_back_when_model_missing(tmp_path: Path):
    client = MagicMock()

    def _create(**kwargs):
        if kwargs["model"] != "whisper-1":
            raise RuntimeError(f"The model `{kwargs['model']}` does not exist")
        return SimpleNamespace(text="ok whisper")

    client.audio.transcriptions.create.side_effect = _create
    stt = OpenAIWhisperSTT(
        _settings_with_stt(model="gpt-4o-mini-transcribe", max_retries=1),
        client=client,
    )
    result = stt.transcribe(_wav(tmp_path))
    assert result.text == "ok whisper"
    assert result.model == "whisper-1"


def test_live_session_payload_is_streaming_transcription():
    from interview_copilot.packages.stt.live_session import (
        model_chain,
        openai_realtime_urls,
        session_update_event,
    )

    ev = session_update_event("gpt-4o-mini-transcribe", language="en", silence_ms=2000)
    session = ev["session"]
    audio_in = session["audio"]["input"]
    assert session["type"] == "transcription"
    assert audio_in["format"]["rate"] == 24000
    assert audio_in["transcription"]["model"] == "gpt-4o-mini-transcribe"
    assert audio_in["turn_detection"]["silence_duration_ms"] == 2000
    assert "intent=transcription" in openai_realtime_urls("gpt-4o-mini-transcribe")[0]
    assert model_chain("gpt-4o-mini-transcribe")[-1] == "whisper-1"


def test_assistant_engine_transcribe_delegates(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    # Reload legacy config bridge after env change
    from interview_copilot.shared.config.settings import reload_settings

    reload_settings()

    client = MagicMock()
    client.audio.transcriptions.create.return_value = SimpleNamespace(text="delegated")

    # Import after reload
    import importlib

    import interview_copilot.core.config as cfg
    importlib.reload(cfg)

    from interview_copilot.core.llm import AssistantEngine

    engine = AssistantEngine(model="gpt-4o-mini", language="en")
    engine.client = client
    text = engine.transcribe(str(_wav(tmp_path)))
    assert text == "delegated"
