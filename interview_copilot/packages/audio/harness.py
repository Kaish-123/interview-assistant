"""
Phase 1 Milestone 2 — audio smoke harness.

List devices, optionally record N seconds to a WAV under logs/.

  python3 -m interview_copilot.packages.audio.harness
  python3 -m interview_copilot.packages.audio.harness --seconds 2 --mode external
  python3 -m interview_copilot.packages.audio.harness --list-only
"""

from __future__ import annotations

import argparse
import time

from interview_copilot.packages.audio.devices import (
    describe_audio_backend,
    list_input_devices,
    resolve_input_device,
)
from interview_copilot.packages.audio.level import rms_level_percent
from interview_copilot.packages.audio.recorder import AudioRecorder
from interview_copilot.packages.audio.wav_io import read_wav_duration_secs
from interview_copilot.shared.config import get_paths, get_settings
from interview_copilot.shared.logging import setup_logging
from interview_copilot.shared.types import AudioInputMode


def main() -> None:
    parser = argparse.ArgumentParser(description="Interview Copilot audio harness")
    parser.add_argument("--seconds", type=float, default=1.5, help="Record duration")
    parser.add_argument(
        "--mode",
        choices=["internal", "external"],
        default=None,
        help="internal=BlackHole/loopback, external=mic",
    )
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    paths = get_paths()
    setup_logging(settings, force=True)

    print("Interview Copilot — Phase 1 Milestone 2 (Audio)")
    print(f"  platform:  {settings.platform}")
    print(f"  backend:   {describe_audio_backend(settings)}")
    print(f"  rate:      {settings.audio.sample_rate} Hz")

    devices = list_input_devices()
    print(f"  inputs:    {len(devices)}")
    for d in devices:
        print(f"    #{d.index}: {d.name} (in={d.max_input_channels})")

    mode: AudioInputMode = args.mode or settings.audio.default_input_mode  # type: ignore[assignment]
    resolved = resolve_input_device(mode, settings=settings)
    print(f"  resolve({mode}): {resolved}")

    if args.list_only:
        return

    recorder = AudioRecorder(settings)
    recorder.input_mode = mode
    out = paths.logs_dir / f"harness_{mode}.wav"
    print(f"  recording {args.seconds}s → {out}")
    recorder.start_recording()
    time.sleep(max(0.2, args.seconds))
    snap = recorder.get_snapshot()
    level = rms_level_percent(snap)
    print(f"  live level: {level}%")
    saved = recorder.stop_recording(out)
    if not saved:
        print("  RESULT: no wav written (silence / device missing / too short)")
        return
    dur = read_wav_duration_secs(saved)
    print(f"  RESULT: wrote {saved} ({dur:.2f}s)")


if __name__ == "__main__":
    main()
