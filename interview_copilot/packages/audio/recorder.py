"""Threaded InputStream recorder implementing AudioSource."""

from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd

from interview_copilot.packages.audio.devices import resolve_input_device
from interview_copilot.packages.audio.loopback import windows_loopback_stream_kwargs
from interview_copilot.packages.audio.wav_io import write_wav_int16
from interview_copilot.shared.config.settings import AppSettings, get_settings
from interview_copilot.shared.logging import StageTimer, get_logger
from interview_copilot.shared.types import AudioInputMode

logger = get_logger("audio.recorder")


class AudioRecorder:
    """
    Capture mono PCM from BlackHole (internal) or mic (external).

    Thread-safe snapshot for live STT / level meters.
    """

    def __init__(self, settings: AppSettings | None = None):
        self._settings = settings or get_settings()
        self.frames: list[np.ndarray] = []
        self.is_recording = False
        self.stream: Optional[sd.InputStream] = None
        self.audio_queue: queue.Queue = queue.Queue()
        self.input_mode: AudioInputMode = self._settings.audio.default_input_mode
        self.lock = threading.Lock()
        self._process_thread: Optional[threading.Thread] = None
        self._started_at: float = 0.0

    @property
    def sample_rate(self) -> int:
        return self._settings.audio.sample_rate

    @property
    def channels(self) -> int:
        return self._settings.audio.channels

    @property
    def dtype(self) -> str:
        return self._settings.audio.dtype

    @property
    def chunk(self) -> int:
        return self._settings.audio.chunk

    def find_device(self) -> Optional[int]:
        return resolve_input_device(self.input_mode, settings=self._settings)

    def get_snapshot(self) -> Optional[np.ndarray]:
        with self.lock:
            if not self.frames:
                return None
            return np.concatenate(self.frames).copy()

    def drop_to_preroll(self, seconds: float = 0.45) -> None:
        """Keep only the last `seconds` of audio (start of an utterance)."""
        keep = max(1, int(self.sample_rate * seconds))
        with self.lock:
            if not self.frames:
                return
            audio = np.concatenate(self.frames)
            self.frames = [audio[-keep:]]

    @staticmethod
    def _mono(frame: np.ndarray) -> np.ndarray:
        arr = np.asarray(frame)
        if arr.ndim == 2 and arr.shape[1] > 1:
            mixed = arr.mean(axis=1)
            if np.issubdtype(arr.dtype, np.integer):
                info = np.iinfo(arr.dtype)
                return np.clip(np.rint(mixed), info.min, info.max).astype(arr.dtype)
            return mixed.astype(arr.dtype, copy=False)
        return arr.reshape(-1)

    def last_chunk_rms(self) -> float:
        """0..1 RMS of the most recent chunk (for VAD)."""
        with self.lock:
            if not self.frames:
                return 0.0
            chunk = np.asarray(self.frames[-1]).reshape(-1)
        if chunk.size == 0:
            return 0.0
        if np.issubdtype(chunk.dtype, np.floating):
            return float(np.sqrt(np.mean(np.square(chunk))))
        return float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2))) / 32768.0

    def start_recording(self) -> None:
        if self.is_recording:
            logger.warning("start_recording called while already recording", extra={"stage": "audio"})
            return

        self.frames = []
        self.is_recording = True
        self._started_at = time.perf_counter()

        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        def callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"input status: {status}", extra={"stage": "audio"})
            if self.is_recording:
                self.audio_queue.put(indata.copy())

        kwargs: dict = {
            "samplerate": self.sample_rate,
            "dtype": self.dtype,
            "callback": callback,
            "blocksize": self.chunk,
            "channels": self.channels,
        }
        used_loopback = False
        if self.input_mode == "internal" and self._settings.platform == "windows":
            loop_kw = windows_loopback_stream_kwargs(self._settings)
            if loop_kw:
                kwargs.update(loop_kw)
                used_loopback = True
            else:
                kwargs["device"] = self.find_device()
        else:
            kwargs["device"] = self.find_device()

        try:
            self.stream = sd.InputStream(**kwargs)
            self.stream.start()
        except Exception as exc:
            if used_loopback:
                logger.warning(f"WASAPI loopback failed ({exc}); trying default input", extra={"stage": "audio"})
                kwargs.pop("extra_settings", None)
                kwargs["channels"] = self.channels
                kwargs["device"] = self.find_device()
                self.stream = sd.InputStream(**kwargs)
                self.stream.start()
            else:
                self.is_recording = False
                raise
        self._process_thread = threading.Thread(target=self._process_audio, daemon=True)
        self._process_thread.start()
        logger.info(
            "recording started",
            extra={"stage": "audio", "model": "loopback" if used_loopback else self.input_mode},
        )

    def _process_audio(self) -> None:
        while self.is_recording or not self.audio_queue.empty():
            try:
                frame = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            mono = self._mono(frame)
            with self.lock:
                self.frames.append(mono)

    def stop_recording(self, filename: str | Path) -> Optional[str]:
        timer = StageTimer(stage="audio_stop")
        self.is_recording = False

        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.warning(f"stream close error: {e}", extra={"stage": "audio"})
            self.stream = None

        if self._process_thread is not None:
            self._process_thread.join(timeout=2.0)
            self._process_thread = None

        with self.lock:
            if not self.frames:
                logger.info("no audio frames captured", extra={"stage": "audio"})
                return None
            audio = np.concatenate(self.frames)
            self.frames = []

        min_samples = max(1, self.sample_rate // 4)  # ~0.25s
        if len(audio) < min_samples:
            logger.info(
                f"audio too short ({len(audio)} samples)",
                extra={"stage": "audio"},
            )
            return None

        path = write_wav_int16(
            filename,
            audio,
            sample_rate=self.sample_rate,
            channels=self.channels,
        )
        elapsed = round((time.perf_counter() - self._started_at) * 1000, 1) if self._started_at else None
        logger.info(
            f"wrote wav {path.name} ({len(audio)} samples)",
            extra={
                "stage": "audio",
                "total_ms": elapsed or timer.total_ms,
            },
        )
        return str(path)
