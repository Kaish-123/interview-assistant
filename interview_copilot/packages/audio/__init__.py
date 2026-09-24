"""Audio capture package — BlackHole / mic → WAV (macOS-first)."""

from interview_copilot.packages.audio.devices import (
    AudioDeviceInfo,
    list_input_devices,
    loopback_status,
    resolve_input_device,
)
from interview_copilot.packages.audio.level import rms_level_percent
from interview_copilot.packages.audio.protocol import AudioSource
from interview_copilot.packages.audio.recorder import AudioRecorder
from interview_copilot.packages.audio.vad import VADGate
from interview_copilot.packages.audio.wav_io import write_wav_int16

__all__ = [
    "AudioDeviceInfo",
    "AudioRecorder",
    "AudioSource",
    "VADGate",
    "list_input_devices",
    "loopback_status",
    "resolve_input_device",
    "rms_level_percent",
    "write_wav_int16",
]
