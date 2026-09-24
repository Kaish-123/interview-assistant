"""
Phase 1 Milestone 3 — STT harness.

Transcribe an existing WAV (e.g. from audio harness) via Whisper.

  python3 -m interview_copilot.packages.stt.harness
  python3 -m interview_copilot.packages.stt.harness --wav path/to/file.wav
  python3 -m interview_copilot.packages.stt.harness --record 2 --mode external
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from interview_copilot.packages.stt import OpenAIWhisperSTT, STTError
from interview_copilot.shared.config import get_paths, get_settings
from interview_copilot.shared.logging import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Interview Copilot STT harness")
    parser.add_argument("--wav", type=str, default=None, help="Path to WAV to transcribe")
    parser.add_argument("--record", type=float, default=0, help="Record N seconds then STT")
    parser.add_argument("--mode", choices=["internal", "external"], default="external")
    parser.add_argument("--prompt", type=str, default="", help="Optional Whisper prompt hint")
    parser.add_argument("--language", type=str, default=None)
    args = parser.parse_args()

    settings = get_settings()
    paths = get_paths()
    setup_logging(settings, force=True)

    print("Interview Copilot — Phase 1 Milestone 3 (STT)")
    print(f"  platform: {settings.platform}")
    print(f"  model:    {settings.stt.model}")
    print(f"  retries:  {settings.stt.max_retries}")
    print(f"  has_key:  {settings.has_api_key}")

    wav_path: Path
    if args.record and args.record > 0:
        from interview_copilot.packages.audio import AudioRecorder

        wav_path = paths.logs_dir / f"stt_harness_{args.mode}.wav"
        rec = AudioRecorder(settings)
        rec.input_mode = args.mode  # type: ignore[assignment]
        print(f"  recording {args.record}s ({args.mode}) → {wav_path}")
        rec.start_recording()
        time.sleep(args.record)
        saved = rec.stop_recording(wav_path)
        if not saved:
            print("  RESULT: no audio captured")
            return
    elif args.wav:
        wav_path = Path(args.wav)
    else:
        # Prefer last audio harness file
        candidates = [
            paths.logs_dir / "harness_external.wav",
            paths.logs_dir / "harness_internal.wav",
        ]
        wav_path = next((p for p in candidates if p.is_file()), candidates[0])

    if not wav_path.is_file():
        print(f"  RESULT: wav not found: {wav_path}")
        print("  Tip: run audio harness first, or pass --record 2 / --wav FILE")
        return

    print(f"  wav:      {wav_path}")
    stt = OpenAIWhisperSTT(settings)
    try:
        result = stt.transcribe(
            wav_path,
            prompt=args.prompt or None,
            language=args.language,
        )
    except STTError as e:
        print(f"  RESULT: FAILED — {e}")
        return

    print(f"  stt_ms:   {result.stt_ms}")
    print(f"  attempts: {result.attempts}")
    print(f"  text:     {result.text!r}")


if __name__ == "__main__":
    main()
