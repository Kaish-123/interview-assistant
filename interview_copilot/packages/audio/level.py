"""Audio level helpers for UI meters."""

from __future__ import annotations

from typing import Optional

import numpy as np


def rms_level_percent(
    samples: Optional[np.ndarray],
    *,
    last_n: int = 1600,
    scale: float = 300.0,
) -> int:
    """
    Rough 0–100 meter from recent int16/float samples.

    Matches prototype behavior (RMS of last ~0.1s at 16 kHz → /300*100).
    """
    if samples is None or len(samples) == 0:
        return 0
    chunk = np.asarray(samples).reshape(-1)
    if last_n > 0:
        chunk = chunk[-last_n:]
    if chunk.size == 0:
        return 0
    if np.issubdtype(chunk.dtype, np.floating):
        # assume -1..1
        rms = float(np.sqrt(np.mean(np.square(chunk))))
        level = int(min(100, rms * 100))
    else:
        rms = float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2)))
        level = int(min(100, rms / scale * 100))
    return max(0, level)
