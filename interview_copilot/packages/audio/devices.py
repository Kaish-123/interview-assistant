"""Input device resolution — macOS BlackHole first; Windows VB-Cable identified."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence

import sounddevice as sd

from interview_copilot.shared.config.settings import AppSettings, AudioSettings, get_settings
from interview_copilot.shared.logging import get_logger
from interview_copilot.shared.types import AudioInputMode, PlatformName

logger = get_logger("audio.devices")


@dataclass(frozen=True)
class AudioDeviceInfo:
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_samplerate: float


def list_input_devices(query_fn=None) -> list[AudioDeviceInfo]:
    """Return input-capable devices."""
    query = query_fn or sd.query_devices
    raw = query()
    # sounddevice may return a single dict for default device query forms;
    # query_devices() with no args returns a DeviceList (sequence of dicts).
    devices: Sequence[Any]
    if isinstance(raw, dict):
        devices = [raw]
    else:
        devices = list(raw)

    out: list[AudioDeviceInfo] = []
    for idx, dev in enumerate(devices):
        try:
            mic = int(dev.get("max_input_channels", 0) or 0)
            if mic <= 0:
                continue
            out.append(
                AudioDeviceInfo(
                    index=idx,
                    name=str(dev.get("name", f"device-{idx}")),
                    max_input_channels=mic,
                    max_output_channels=int(dev.get("max_output_channels", 0) or 0),
                    default_samplerate=float(dev.get("default_samplerate", 0) or 0),
                )
            )
        except Exception:
            continue
    return out


def _internal_name_hints(settings: AppSettings) -> tuple[str, ...]:
    """Platform-aware substrings for system/loopback audio devices."""
    audio = settings.audio
    platform: PlatformName = settings.platform
    if platform == "windows":
        # Windows enhancement backlog W1 — prefer VB-Cable / Voicemeeter when present
        return (
            audio.vb_cable_device.lower(),
            "cable output",
            "voicemeeter",
            "vb-audio",
        )
    # macOS (primary) + fallback for others
    return (audio.blackhole_device.lower(), "blackhole")


def resolve_input_device(
    mode: AudioInputMode = "internal",
    *,
    settings: AppSettings | None = None,
    query_fn=None,
) -> Optional[int]:
    """
    Resolve an input device index.

    - internal: BlackHole on macOS; VB-Cable/Voicemeeter on Windows (when installed)
    - external: first non-loopback input device

    Returns None → sounddevice default input.
    """
    settings = settings or get_settings()
    devices = list_input_devices(query_fn=query_fn)
    if not devices:
        logger.warning("no input devices found", extra={"stage": "audio"})
        return None

    hints = _internal_name_hints(settings)

    def is_loopback(name: str) -> bool:
        n = name.lower()
        return any(h and h in n for h in hints)

    target: Optional[AudioDeviceInfo] = None
    if mode == "internal":
        for d in devices:
            if is_loopback(d.name):
                target = d
                break
        if target is None and settings.platform == "windows":
            logger.info(
                "Windows internal audio device not found "
                "(install VB-Audio Cable or Voicemeeter). Falling back to default.",
                extra={"stage": "audio"},
            )
        elif target is None:
            logger.info(
                "BlackHole not found — falling back to default input. "
                "Install BlackHole and set multi-output device for call audio.",
                extra={"stage": "audio"},
            )
    else:
        for d in devices:
            if not is_loopback(d.name):
                target = d
                break

    if target is None:
        logger.info(
            "using sounddevice default input",
            extra={"stage": "audio"},
        )
        return None

    logger.info(
        f"using device #{target.index}: {target.name} (mode={mode})",
        extra={"stage": "audio"},
    )
    return target.index


def describe_audio_backend(settings: AppSettings | None = None) -> str:
    settings = settings or get_settings()
    audio: AudioSettings = settings.audio
    if settings.platform == "windows":
        return f"windows/vb-cable preferred ({audio.vb_cable_device}); WASAPI loopback fallback"
    return f"macos/blackhole preferred ({audio.blackhole_device})"


def loopback_status(settings: AppSettings | None = None, query_fn=None) -> dict[str, Any]:
    """What the OS can hear besides the built-in mic — for permission / setup UI."""
    settings = settings or get_settings()
    try:
        devices = list_input_devices(query_fn=query_fn)
    except Exception:
        devices = []
    hints = _internal_name_hints(settings)
    loopback = next((d for d in devices if any(h and h in d.name.lower() for h in hints)), None)
    if settings.platform == "macos":
        setup = (
            "macOS: System Settings → Privacy & Security → Microphone — allow Python/Terminal. "
            "To hear Zoom/Teams/YouTube, install BlackHole, make a Multi-Output Device "
            "(Speakers + BlackHole), and set that as system output."
        )
    elif settings.platform == "windows":
        setup = (
            "Windows: Settings → Privacy → Microphone — allow this app. "
            "Hide from share uses WASAPI loopback (hears Zoom/Teams/Chrome). "
            "Or install VB-Audio Cable. In the browser, share a tab/window and enable Share audio."
        )
    else:
        setup = "Use browser Share tab audio, or a virtual cable if your OS supports it."
    return {
        "platform": settings.platform,
        "backend": describe_audio_backend(settings),
        "loopback_device": None if loopback is None else loopback.name,
        "loopback_ready": loopback is not None or settings.platform == "windows",
        "inputs": [{"index": d.index, "name": d.name} for d in devices[:24]],
        "setup": setup,
    }
