"""macOS audio adapters — BlackHole loopback naming."""

from __future__ import annotations

from interview_copilot.shared.config.settings import AudioSettings


def loopback_name_hints(audio: AudioSettings) -> tuple[str, ...]:
    return (audio.blackhole_device.lower(), "blackhole")


SETUP_HINT = (
    "Install BlackHole, create a Multi-Output Device (Speakers + BlackHole), "
    "and set that as the system output so Interview Copilot can capture call audio."
)
