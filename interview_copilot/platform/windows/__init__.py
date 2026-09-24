"""Windows audio adapters — enhancement backlog W1 (VB-Cable / Voicemeeter)."""

from __future__ import annotations

from interview_copilot.shared.config.settings import AudioSettings


def loopback_name_hints(audio: AudioSettings) -> tuple[str, ...]:
    return (
        audio.vb_cable_device.lower(),
        "cable output",
        "voicemeeter",
        "vb-audio",
    )


SETUP_HINT = (
    "Windows enhancement: install VB-Audio Virtual Cable or Voicemeeter, "
    "then set AUDIO internal mode. Mac remains the primary supported platform."
)


def not_implemented_message() -> str:
    return (
        "Windows internal-audio adapter is identified but not fully validated yet. "
        + SETUP_HINT
    )
