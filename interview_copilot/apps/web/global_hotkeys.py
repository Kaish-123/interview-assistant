"""Dispatch OS-global `` ` `` to the active Studio/Live engine."""

from __future__ import annotations

import threading
import time

_lock = threading.Lock()
_last_toggle_at = 0.0
_DEBOUNCE_SECS = 0.35


def dispatch_listen_toggle() -> None:
    """First `` ` `` starts listening; second stops, transcribes, and answers."""
    global _last_toggle_at
    now = time.monotonic()
    with _lock:
        if now - _last_toggle_at < _DEBOUNCE_SECS:
            return
        _last_toggle_at = now
    try:
        from interview_copilot.apps.web.routers import apply_privacy_command
        from interview_copilot.apps.web.runtime import get_runtime

        engine = get_runtime().preferred_for_global_hotkeys()
        if engine is None:
            print("Global `: no Studio/Live session yet — open /app and join or use Studio.")
            return
        result = apply_privacy_command(engine, "toggle_listen")
        print(f"Global `: toggle_listen → {engine.kind} {engine.id} seq={result.get('seq')}")
    except Exception as exc:
        print(f"Global ` dispatch failed: {exc}")
