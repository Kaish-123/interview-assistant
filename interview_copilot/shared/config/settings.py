"""Typed settings loaded from environment / .env (macOS-first defaults)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, replace
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv

from interview_copilot.shared.config.paths import get_paths

PlatformName = Literal["macos", "windows", "linux", "unknown"]
AudioInputMode = Literal["internal", "external"]
AnswerMode = Literal["default", "quick", "detailed", "code"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


def detect_platform() -> PlatformName:
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    return "unknown"


@dataclass(frozen=True)
class AudioSettings:
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "int16"
    chunk: int = 1024
    # macOS primary; Windows adapters use vb_cable_device / voicemeeter later
    blackhole_device: str = "BlackHole"
    vb_cable_device: str = "CABLE Output"
    default_input_mode: AudioInputMode = "internal"


@dataclass(frozen=True)
class VADSettings:
    speech_rms: float = 0.012
    silence_secs: float = 1.8
    min_record_secs: float = 1.2
    onset_chunks: int = 3


@dataclass(frozen=True)
class LLMSettings:
    default_model: str = "gpt-4o-mini"
    available_models: tuple[str, ...] = (
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4-turbo",
    )
    max_retries: int = 3
    max_output_tokens: int = 1600
    default_answer_mode: AnswerMode = "default"
    optimization_mode: bool = False
    max_rounds_for_model: int = 4
    summary_threshold_rounds: int = 5
    image_detail_level: Literal["low", "high"] = "low"


@dataclass(frozen=True)
class STTSettings:
    """OpenAI cloud STT. File commits use gpt-4o-mini-transcribe; live uses Realtime."""

    model: str = "gpt-4o-mini-transcribe"
    live_model: str = "gpt-4o-mini-transcribe"
    max_retries: int = 3
    # Backoff base seconds: attempt 1 wait 2s, then 4s, … (matches prototype)
    retry_backoff_secs: float = 2.0
    # Empty string = let Whisper auto-detect; otherwise ISO code e.g. "en"
    language: str = ""


@dataclass(frozen=True)
class AppSettings:
    """Immutable snapshot of runtime configuration."""

    openai_api_key: str
    platform: PlatformName
    log_level: LogLevel
    log_json: bool
    audio: AudioSettings = field(default_factory=AudioSettings)
    vad: VADSettings = field(default_factory=VADSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    stt: STTSettings = field(default_factory=STTSettings)
    default_language: str = "en"
    languages: tuple[str, ...] = (
        "en",
        "es",
        "fr",
        "de",
        "hi",
        "zh",
        "ja",
        "pt",
        "it",
        "ko",
    )
    system_prompt: str = (
        "You are a real-time interview copilot. "
        "Help the candidate answer clearly and concisely in first person, "
        "as talking points they can say out loud. "
        "Match answers to their resume and job description when provided. "
        "For coding questions: clarifying questions, approach, complexity, clean code, edge cases. "
        "For behavioral questions: STAR (Situation, Task, Action, Result). "
        "For system design: requirements, high-level design, components, scalability. "
        "Keep spoken answers interview-length unless asked for code or detail. "
        "Respond in the same language as the question."
    )
    coding_screen_prompt: str = (
        "Analyze this coding-interview screenshot (LeetCode / HackerRank / CoderPad style). "
        "Provide: 1) Problem restatement 2) Clarifying questions "
        "3) Approach + time/space complexity 4) Clean solution code "
        "5) Edge cases and test ideas. Keep it practical for a live interview."
    )

    @property
    def has_api_key(self) -> bool:
        return bool(self.openai_api_key.strip())

    def require_api_key(self) -> str:
        if not self.has_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Copy env.example to .env and set the key."
            )
        return self.openai_api_key

    def model_label(self, model: str | None = None) -> str:
        mid = model or self.llm.default_model
        labels = {
            "gpt-4o": "GPT-4o — best quality",
            "gpt-4o-mini": "GPT-4o-mini — faster / cheaper",
            "gpt-4.1": "GPT-4.1 — strong reasoning",
            "gpt-4.1-mini": "GPT-4.1-mini — fast reasoning",
            "gpt-4-turbo": "GPT-4-Turbo — balanced",
        }
        return labels.get(mid, mid)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _load_dotenv_files() -> list[str]:
    loaded: list[str] = []
    for path in get_paths().env_candidates:
        if path.is_file():
            load_dotenv(path, override=False)
            loaded.append(str(path))
    # Also allow process env already set (CI / shell export)
    return loaded


def build_settings() -> AppSettings:
    """Build a fresh settings object from current environment."""
    _load_dotenv_files()

    log_level_raw = os.getenv("LOG_LEVEL", "INFO").upper()
    if log_level_raw not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
        log_level_raw = "INFO"

    input_mode = os.getenv("AUDIO_INPUT_MODE", "internal").lower()
    if input_mode not in {"internal", "external"}:
        input_mode = "internal"

    answer_mode = os.getenv("ANSWER_MODE", "default").lower()
    if answer_mode not in {"default", "quick", "detailed", "code"}:
        answer_mode = "default"

    image_detail = os.getenv("IMAGE_DETAIL_LEVEL", "low").lower()
    if image_detail not in {"low", "high"}:
        image_detail = "low"

    default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

    audio = AudioSettings(
        sample_rate=_env_int("AUDIO_SAMPLE_RATE", 16000),
        channels=_env_int("AUDIO_CHANNELS", 1),
        chunk=_env_int("AUDIO_CHUNK", 1024),
        blackhole_device=os.getenv("BLACKHOLE_DEVICE", "BlackHole"),
        vb_cable_device=os.getenv("VB_CABLE_DEVICE", "CABLE Output"),
        default_input_mode=input_mode,  # type: ignore[arg-type]
    )
    vad = VADSettings(
        speech_rms=_env_float("VAD_SPEECH_RMS", 0.012),
        silence_secs=_env_float("VAD_SILENCE_SECS", 1.8),
        min_record_secs=_env_float("VAD_MIN_RECORD_SECS", 1.2),
        onset_chunks=_env_int("VAD_ONSET_CHUNKS", 3),
    )
    llm = LLMSettings(
        default_model=default_model,
        max_retries=_env_int("OPENAI_MAX_RETRIES", 3),
        max_output_tokens=_env_int("OPENAI_MAX_OUTPUT_TOKENS", 1600),
        default_answer_mode=answer_mode,  # type: ignore[arg-type]
        optimization_mode=_env_bool("OPTIMIZATION_MODE", False),
        max_rounds_for_model=_env_int("MAX_ROUNDS_FOR_MODEL", 4),
        summary_threshold_rounds=_env_int("SUMMARY_THRESHOLD_ROUNDS", 5),
        image_detail_level=image_detail,  # type: ignore[arg-type]
    )
    default_language = os.getenv("DEFAULT_LANGUAGE", "en")
    stt_language = os.getenv("WHISPER_LANGUAGE", "").strip()
    stt_model = (
        os.getenv("WHISPER_MODEL", "gpt-4o-mini-transcribe").strip()
        or "gpt-4o-mini-transcribe"
    )
    stt = STTSettings(
        model=stt_model,
        live_model=os.getenv("STT_LIVE_MODEL", stt_model).strip() or stt_model,
        max_retries=_env_int("WHISPER_MAX_RETRIES", _env_int("OPENAI_MAX_RETRIES", 3)),
        retry_backoff_secs=_env_float("WHISPER_RETRY_BACKOFF_SECS", 2.0),
        language=stt_language,
    )

    return AppSettings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        platform=detect_platform(),
        log_level=log_level_raw,  # type: ignore[arg-type]
        log_json=_env_bool("LOG_JSON", False),
        audio=audio,
        vad=vad,
        llm=llm,
        stt=stt,
        default_language=default_language,
    )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return build_settings()


def reload_settings() -> AppSettings:
    """Clear cache and rebuild (useful in tests)."""
    get_settings.cache_clear()
    get_paths.cache_clear()
    return get_settings()


def with_overrides(base: AppSettings, **kwargs) -> AppSettings:
    """Return a copy with top-level field overrides (tests / session setup)."""
    return replace(base, **kwargs)
