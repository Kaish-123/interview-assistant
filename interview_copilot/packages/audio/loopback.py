"""Windows WASAPI loopback — capture what the computer is playing (Zoom, Meet, YouTube)."""

from __future__ import annotations

from typing import Any, Optional

from interview_copilot.shared.config.settings import AppSettings, get_settings
from interview_copilot.shared.logging import get_logger

logger = get_logger("audio.loopback")


def windows_loopback_stream_kwargs(settings: AppSettings | None = None) -> dict[str, Any]:
    """Return sounddevice InputStream kwargs for WASAPI loopback, or {}."""
    settings = settings or get_settings()
    if settings.platform != "windows":
        return {}
    try:
        import sounddevice as sd
    except Exception:
        return {}
    wasapi = getattr(sd, "WasapiSettings", None)
    if wasapi is None:
        return {}
    try:
        extra = wasapi(loopback=True)
    except Exception as exc:
        logger.info(f"WASAPI loopback unavailable: {exc}", extra={"stage": "audio"})
        return {}
    out_idx = _default_output_index()
    if out_idx is None:
        return {}
    logger.info(
        f"using WASAPI loopback on output device #{out_idx}",
        extra={"stage": "audio"},
    )
    return {
        "device": out_idx,
        "extra_settings": extra,
        "channels": 2,
    }


def _default_output_index() -> Optional[int]:
    try:
        import sounddevice as sd

        default = sd.default.device
        if isinstance(default, (list, tuple)) and len(default) >= 2:
            idx = default[1]
            if idx is not None and int(idx) >= 0:
                return int(idx)
        raw = sd.query_devices(kind="output")
        if isinstance(raw, dict):
            # query_devices(kind=) returns one device; find its index
            name = str(raw.get("name", ""))
            for i, dev in enumerate(sd.query_devices()):
                if str(dev.get("name", "")) == name and int(dev.get("max_output_channels") or 0) > 0:
                    return i
    except Exception:
        return None
    return None
