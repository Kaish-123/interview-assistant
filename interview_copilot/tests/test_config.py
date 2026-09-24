"""Phase 1 Milestone 1 — config + paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from interview_copilot.shared.config.paths import get_paths
from interview_copilot.shared.config.settings import (
    build_settings,
    detect_platform,
    reload_settings,
)


def test_detect_platform_is_known():
    assert detect_platform() in {"macos", "windows", "linux", "unknown"}


def test_get_paths_creates_dirs():
    paths = get_paths()
    assert paths.package_root.name == "interview_copilot"
    assert paths.sessions_dir.is_dir()
    assert paths.data_dir.is_dir()
    assert paths.logs_dir.is_dir()
    assert paths.chats_json.name == "chats.json"
    assert paths.tabs_json.name == "tabs.json"


def test_build_settings_reads_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("AUDIO_INPUT_MODE", "external")
    monkeypatch.setenv("OPTIMIZATION_MODE", "true")
    monkeypatch.setenv("BLACKHOLE_DEVICE", "BlackHole 2ch")

    settings = build_settings()
    assert settings.openai_api_key == "sk-test-key"
    assert settings.has_api_key is True
    assert settings.llm.default_model == "gpt-4o"
    assert settings.log_level == "DEBUG"
    assert settings.audio.default_input_mode == "external"
    assert settings.llm.optimization_mode is True
    assert settings.audio.blackhole_device == "BlackHole 2ch"
    assert settings.require_api_key() == "sk-test-key"


def test_require_api_key_raises_when_missing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    settings = build_settings()
    assert settings.has_api_key is False
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        settings.require_api_key()


def test_reload_settings_clears_cache(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "first")
    a = reload_settings()
    assert a.openai_api_key == "first"
    monkeypatch.setenv("OPENAI_API_KEY", "second")
    b = reload_settings()
    assert b.openai_api_key == "second"


def test_env_example_exists():
    example = Path(__file__).resolve().parents[1] / "env.example"
    assert example.is_file()
    text = example.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" in text
    assert "BLACKHOLE_DEVICE" in text
    assert "gpt-4o-mini-transcribe" in text
    assert "STT_LIVE_MODEL" in text
