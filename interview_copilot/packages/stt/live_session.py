"""OpenAI realtime transcription session payloads (Parakeet-style streaming STT).

Parakeet AI listens continuously and emits transcript as speech arrives, then
answers once the interviewer pauses. We match that with OpenAI's realtime
transcription session (gpt-4o-mini-transcribe / gpt-live-transcribe), not by
re-uploading the whole WAV to Whisper every few seconds.
"""

from __future__ import annotations

DEFAULT_FILE_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_LIVE_MODEL = "gpt-4o-mini-transcribe"
FILE_FALLBACKS = (
    "gpt-4o-mini-transcribe",
    "gpt-4o-transcribe",
    "whisper-1",
)
INTERVIEW_STT_PROMPT = (
    "Live job interview. Transcribe the interviewer completely, "
    "including every sentence and technical term. Do not skip words."
)


def model_chain(preferred: str | None) -> list[str]:
    """Preferred model first, then known-good OpenAI transcribe fallbacks."""
    out: list[str] = []
    for name in (preferred, *FILE_FALLBACKS):
        n = (name or "").strip()
        if n and n not in out:
            out.append(n)
    return out or [DEFAULT_FILE_MODEL]


def is_model_unavailable(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if "model" not in msg:
        return False
    return any(
        token in msg
        for token in ("not found", "does not exist", "invalid", "unsupported", "unknown")
    )


def session_update_event(
    model: str,
    *,
    language: str = "en",
    silence_ms: int = 2000,
) -> dict:
    """Realtime `session.update` for a transcription-only session."""
    transcription: dict = {
        "model": model or DEFAULT_LIVE_MODEL,
        "prompt": INTERVIEW_STT_PROMPT,
    }
    lang = (language or "").strip()
    if lang and lang.lower() not in {"auto", "detect"}:
        transcription["language"] = lang
    return {
        "type": "session.update",
        "session": {
            "type": "transcription",
            "audio": {
                "input": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    "transcription": transcription,
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 400,
                        "silence_duration_ms": max(800, int(silence_ms)),
                    },
                }
            },
        },
    }


def legacy_session_update_event(
    model: str,
    *,
    language: str = "en",
    silence_ms: int = 2000,
) -> dict:
    """Older Realtime session shape, used if the nested payload is rejected."""
    transcription: dict = {
        "model": model or DEFAULT_LIVE_MODEL,
        "prompt": INTERVIEW_STT_PROMPT,
    }
    lang = (language or "").strip()
    if lang and lang.lower() not in {"auto", "detect"}:
        transcription["language"] = lang
    return {
        "type": "session.update",
        "session": {
            "input_audio_format": "pcm16",
            "input_audio_transcription": transcription,
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 400,
                "silence_duration_ms": max(800, int(silence_ms)),
            },
        },
    }


def openai_realtime_urls(model: str) -> tuple[str, ...]:
    chosen = (model or DEFAULT_LIVE_MODEL).strip()
    return (
        "wss://api.openai.com/v1/realtime?intent=transcription",
        f"wss://api.openai.com/v1/realtime?model={chosen}",
    )
