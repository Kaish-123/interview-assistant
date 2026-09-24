"""Speech-to-text package — OpenAI Whisper with retries (local STT later)."""

from interview_copilot.packages.stt.errors import STTError
from interview_copilot.packages.stt.protocol import STTProvider
from interview_copilot.packages.stt.result import TranscriptionResult
from interview_copilot.packages.stt.whisper_openai import OpenAIWhisperSTT, create_stt_provider

__all__ = [
    "OpenAIWhisperSTT",
    "STTError",
    "STTProvider",
    "TranscriptionResult",
    "create_stt_provider",
]
