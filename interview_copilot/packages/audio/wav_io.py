"""WAV helpers for int16 mono/stereo PCM."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import wave


def write_wav_int16(
    path: str | Path,
    audio: np.ndarray,
    *,
    sample_rate: int,
    channels: int = 1,
) -> Path:
    """Write int16 PCM WAV. Accepts float or int arrays."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = np.asarray(audio)
    if data.ndim > 1:
        data = data.reshape(-1, data.shape[-1])
        if channels == 1 and data.shape[-1] > 1:
            data = data.mean(axis=-1)
        else:
            data = data.reshape(-1)
    else:
        data = data.reshape(-1)

    if np.issubdtype(data.dtype, np.floating):
        data = np.clip(data, -1.0, 1.0)
        data = (data * 32767.0).astype(np.int16)
    else:
        data = data.astype(np.int16)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data.tobytes())
    return path


def read_wav_duration_secs(path: str | Path) -> float:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate() or 1
        return frames / float(rate)
