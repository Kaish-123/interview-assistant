"""Backward-compatible re-exports → shared.config (Phase 1 Milestone 1).

Existing Live UI imports from interview_copilot.core.config keep working.
New code should import from interview_copilot.shared.config.
"""

from __future__ import annotations

from interview_copilot.shared.config import get_paths, get_settings
from interview_copilot.shared.logging import setup_logging

_settings = get_settings()
_paths = get_paths()

ROOT = _paths.package_root
REPO_ROOT = _paths.repo_root
SESSIONS_DIR = _paths.sessions_dir

OPENAI_API_KEY = _settings.openai_api_key

MODELS = {m: _settings.model_label(m) for m in _settings.llm.available_models}
DEFAULT_MODEL = _settings.llm.default_model
LANGUAGES = list(_settings.languages)

SAMPLE_RATE = _settings.audio.sample_rate
CHANNELS = _settings.audio.channels
DTYPE = _settings.audio.dtype
CHUNK = _settings.audio.chunk
BLACKHOLE_DEVICE = _settings.audio.blackhole_device

SPEECH_RMS = _settings.vad.speech_rms
SILENCE_SECS = _settings.vad.silence_secs
MIN_RECORD_SECS = _settings.vad.min_record_secs
ONSET_CHUNKS = _settings.vad.onset_chunks

SYSTEM_PROMPT = _settings.system_prompt
CODING_SCREEN_PROMPT = _settings.coding_screen_prompt

# Ensure logging is ready when legacy config is imported
setup_logging(_settings)
