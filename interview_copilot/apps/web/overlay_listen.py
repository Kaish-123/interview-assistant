"""Native overlay listen loop — system/call audio even when the browser tab is hidden."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Callable

from interview_copilot.packages.audio.recorder import AudioRecorder
from interview_copilot.packages.audio.vad import VADGate
from interview_copilot.shared.config.paths import get_paths
from interview_copilot.shared.config.settings import get_settings


OnStatus = Callable[[str], None]


def _post_listen(base: str, engine_id: str, wav_path: str) -> None:
    import httpx

    with open(wav_path, "rb") as fh:
        data = fh.read()
    with httpx.Client(timeout=180.0) as client:
        with client.stream(
            "POST",
            f"{base.rstrip('/')}/api/listen/stream",
            files={"file": ("clip.wav", data, "audio/wav")},
            data={"engine_id": engine_id, "force": "true"},
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                raw = line.decode() if isinstance(line, bytes) else line
                if not raw.startswith("data:"):
                    continue
                payload = json.loads(raw[5:].strip() or "{}")
                if payload.get("type") in {"done", "error"}:
                    break


class OverlayListenWorker:
    def __init__(self, base: str, engine_id: str, on_status: OnStatus | None = None):
        self.base = base.rstrip("/")
        self.engine_id = engine_id
        self.on_status = on_status or (lambda _s: None)
        self.rec = AudioRecorder()
        self.rec.input_mode = "internal"
        self._stop = threading.Event()
        self._auto = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def _say(self, msg: str) -> None:
        try:
            self.on_status(msg)
        except Exception:
            pass

    def start_auto(self) -> None:
        with self._lock:
            self._auto = True
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop_auto(self) -> None:
        with self._lock:
            self._auto = False
        self._stop.set()
        try:
            if self.rec.is_recording:
                tmp = get_paths().data_dir / "tmp_uploads"
                tmp.mkdir(parents=True, exist_ok=True)
                self.rec.stop_recording(tmp / "overlay-discard.wav")
        except Exception:
            pass

    def is_manual_listening(self) -> bool:
        return bool(self.rec.is_recording and not self._auto)

    def apply_toggle_command(self, command: str) -> str:
        """listen / stop_listen / toggle_listen — same toggle as the old tool."""
        listening = self.is_manual_listening()
        if command == "listen" and listening:
            return "listening"
        if command == "stop_listen" and not listening:
            return "idle"
        if command in {"listen", "stop_listen", "toggle_listen"}:
            return self.toggle_manual()
        return "listening" if listening else "idle"

    def toggle_manual(self) -> str:
        """Start or stop a hold-to-record clip (Listen button)."""
        if self.rec.is_recording and not self._auto:
            tmp = get_paths().data_dir / "tmp_uploads"
            tmp.mkdir(parents=True, exist_ok=True)
            path = self.rec.stop_recording(tmp / f"overlay-manual-{int(time.time())}.wav")
            self._say("Transcribing…")
            if path:
                try:
                    _post_listen(self.base, self.engine_id, path)
                    Path(path).unlink(missing_ok=True)
                except Exception as exc:
                    self._say(str(exc)[:80])
                    return "error"
            return "idle"
        try:
            self.rec.start_recording()
        except Exception as exc:
            self._say(f"Mic/loopback permission needed: {exc}"[:80])
            return "error"
        self._say("Listening to meeting audio…")
        return "listening"

    def _ensure_recording(self) -> bool:
        if self.rec.is_recording:
            return True
        try:
            self.rec.start_recording()
            self._say("Hearing system audio (Zoom/Meet/Teams/tab)…")
            return True
        except Exception as exc:
            self._say(
                "Allow Microphone (and on Mac install BlackHole). "
                f"{exc}"[:70]
            )
            return False

    def _loop(self) -> None:
        settings = get_settings()
        vad = VADGate(
            speech_rms=settings.vad.speech_rms,
            silence_secs=max(1.1, settings.vad.silence_secs - 0.3),
            min_record_secs=settings.vad.min_record_secs,
            onset_chunks=settings.vad.onset_chunks,
        )
        if not self._ensure_recording():
            return
        tmp = get_paths().data_dir / "tmp_uploads"
        tmp.mkdir(parents=True, exist_ok=True)
        while not self._stop.is_set() and self._auto:
            time.sleep(0.08)
            event = vad.feed(self.rec.last_chunk_rms())
            if event == "onset":
                self.rec.drop_to_preroll(0.4)
                self._say("Question incoming…")
            elif event == "utterance":
                path = self.rec.stop_recording(tmp / f"overlay-auto-{int(time.time())}.wav")
                self._say("Answering…")
                if path:
                    try:
                        _post_listen(self.base, self.engine_id, path)
                    except Exception as exc:
                        self._say(str(exc)[:80])
                    try:
                        Path(path).unlink(missing_ok=True)
                    except Exception:
                        pass
                if self._auto and not self._stop.is_set():
                    vad.reset()
                    self._ensure_recording()
        try:
            if self.rec.is_recording:
                self.rec.stop_recording(tmp / "overlay-stop.wav")
        except Exception:
            pass
