"""Phase 1 Milestone 2 — audio package tests (mocked devices + real wav/level)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np

from interview_copilot.packages.audio.devices import (
    list_input_devices,
    loopback_status,
    resolve_input_device,
)
from interview_copilot.packages.audio.loopback import windows_loopback_stream_kwargs
from interview_copilot.packages.audio.vad import VADGate
from interview_copilot.packages.audio.level import rms_level_percent
from interview_copilot.packages.audio.protocol import AudioSource
from interview_copilot.packages.audio.recorder import AudioRecorder
from interview_copilot.packages.audio.wav_io import read_wav_duration_secs, write_wav_int16
from interview_copilot.shared.config.settings import build_settings


def _fake_devices():
    return [
        {
            "name": "Built-in Microphone",
            "max_input_channels": 1,
            "max_output_channels": 0,
            "default_samplerate": 48000,
        },
        {
            "name": "BlackHole 2ch",
            "max_input_channels": 2,
            "max_output_channels": 2,
            "default_samplerate": 48000,
        },
        {
            "name": "CABLE Output (VB-Audio Virtual Cable)",
            "max_input_channels": 2,
            "max_output_channels": 0,
            "default_samplerate": 48000,
        },
    ]


def test_list_input_devices_filters_outputs():
    devices = list_input_devices(query_fn=_fake_devices)
    assert len(devices) == 3
    assert devices[1].name == "BlackHole 2ch"


def test_resolve_internal_prefers_blackhole_on_macos():
    settings = replace(build_settings(), platform="macos")
    idx = resolve_input_device("internal", settings=settings, query_fn=_fake_devices)
    assert idx == 1


def test_resolve_external_skips_loopback():
    settings = replace(build_settings(), platform="macos")
    idx = resolve_input_device("external", settings=settings, query_fn=_fake_devices)
    assert idx == 0


def test_resolve_windows_prefers_vb_cable():
    settings = replace(build_settings(), platform="windows")
    idx = resolve_input_device("internal", settings=settings, query_fn=_fake_devices)
    assert idx == 2


def test_write_and_read_wav(tmp_path: Path):
    sr = 16000
    audio = np.sin(np.linspace(0, 2 * np.pi * 10, sr)).astype(np.float32) * 0.2
    path = write_wav_int16(tmp_path / "tone.wav", audio, sample_rate=sr, channels=1)
    assert path.is_file()
    dur = read_wav_duration_secs(path)
    assert 0.95 <= dur <= 1.05


def test_rms_level_percent_silent_and_loud():
    assert rms_level_percent(None) == 0
    assert rms_level_percent(np.zeros(1600, dtype=np.int16)) == 0
    loud = np.ones(1600, dtype=np.int16) * 10000
    assert rms_level_percent(loud) > 50


def test_audio_recorder_is_audio_source():
    rec = AudioRecorder(build_settings())
    assert isinstance(rec, AudioSource)


def test_stop_without_start_returns_none(tmp_path: Path):
    rec = AudioRecorder(build_settings())
    assert rec.stop_recording(tmp_path / "empty.wav") is None


def test_core_bridge_exports_recorder():
    from interview_copilot.core.audio import AudioRecorder as Legacy

    assert Legacy is AudioRecorder


def test_vad_gate_onset_then_utterance():
    gate = VADGate(speech_rms=0.1, silence_secs=0.5, min_record_secs=0.3, onset_chunks=2)
    assert gate.feed(0.2, 1.0) == ""
    assert gate.feed(0.2, 1.1) == "onset"
    assert gate.feed(0.0, 1.2) == ""
    assert gate.feed(0.0, 1.8) == "utterance"
    assert gate.in_speech is False


def test_vad_gate_ignores_silence():
    gate = VADGate(speech_rms=0.1, onset_chunks=3)
    assert gate.feed(0.0, 1.0) == ""
    assert gate.feed(0.05, 1.1) == ""
    assert gate.in_speech is False


def test_loopback_status_finds_blackhole():
    settings = replace(build_settings(), platform="macos")
    info = loopback_status(settings=settings, query_fn=_fake_devices)
    assert info["loopback_device"] == "BlackHole 2ch"
    assert info["loopback_ready"] is True
    assert "BlackHole" in info["setup"]


def test_loopback_status_windows_ready_without_cable():
    settings = replace(build_settings(), platform="windows")

    def empty():
        return []

    info = loopback_status(settings=settings, query_fn=empty)
    assert info["loopback_ready"] is True
    assert "WASAPI" in info["setup"]


def test_windows_loopback_kwargs_empty_on_macos():
    settings = replace(build_settings(), platform="macos")
    assert windows_loopback_stream_kwargs(settings) == {}


def test_recorder_preroll_and_rms():
    rec = AudioRecorder(build_settings())
    rec.frames = [
        np.ones(8000, dtype=np.int16) * 100,
        np.ones(8000, dtype=np.int16) * 8000,
    ]
    assert rec.last_chunk_rms() > 0.1
    rec.drop_to_preroll(0.1)
    kept = int(np.concatenate(rec.frames).shape[0])
    assert kept <= rec.sample_rate * 0.1 + 1
