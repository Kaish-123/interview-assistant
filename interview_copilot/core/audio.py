"""Audio capture — mic or BlackHole system audio."""

from __future__ import annotations

import queue
import threading
import wave
from typing import Optional

import numpy as np
import sounddevice as sd

from .config import BLACKHOLE_DEVICE, CHANNELS, CHUNK, DTYPE, SAMPLE_RATE


class AudioRecorder:
    def __init__(self):
        self.frames: list[np.ndarray] = []
        self.is_recording = False
        self.stream = None
        self.audio_queue: queue.Queue = queue.Queue()
        self.input_mode = "internal"  # internal=BlackHole, external=mic
        self.lock = threading.Lock()
        self._process_thread: Optional[threading.Thread] = None

    def find_device(self) -> Optional[int]:
        try:
            devices = sd.query_devices()
        except Exception as e:
            print(f"Could not query audio devices: {e}")
            return None

        bh = BLACKHOLE_DEVICE.lower()
        target = None

        if self.input_mode == "internal":
            for idx, dev in enumerate(devices):
                if dev.get("max_input_channels", 0) > 0 and bh in dev.get("name", "").lower():
                    target = idx
                    break
        else:
            for idx, dev in enumerate(devices):
                if dev.get("max_input_channels", 0) > 0 and bh not in dev.get("name", "").lower():
                    target = idx
                    break

        if target is None:
            return None
        try:
            print(f"Using device #{target}: {devices[target]['name']} ({self.input_mode})")
        except Exception:
            pass
        return target

    def start_recording(self):
        device_id = self.find_device()
        self.frames = []
        self.is_recording = True

        def callback(indata, frames, time_info, status):
            if self.is_recording:
                self.audio_queue.put(indata.copy())

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=callback,
            device=device_id,
            blocksize=CHUNK,
        )
        self.stream.start()
        self._process_thread = threading.Thread(target=self._process_audio, daemon=True)
        self._process_thread.start()

    def _process_audio(self):
        while self.is_recording or not self.audio_queue.empty():
            try:
                frame = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            with self.lock:
                self.frames.append(frame)

    def stop_recording(self, filename: str) -> Optional[str]:
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        if self._process_thread:
            self._process_thread.join(timeout=2.0)
            self._process_thread = None

        with self.lock:
            if not self.frames:
                return None
            audio = np.concatenate(self.frames)
            self.frames = []

        if len(audio) < SAMPLE_RATE // 4:
            return None

        with wave.open(filename, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.astype(np.int16).tobytes())
        return filename
