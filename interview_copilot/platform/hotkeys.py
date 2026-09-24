"""Hotkey modifier map — Cmd on Mac, Ctrl on Windows (backlog W4).

Global listen toggle uses pynput Listener (same idea as chatgpt_toggle_listener):
first `` ` `` starts recording, second `` ` `` stops and answers.

Do not start this listener from overlay_window.py — Accessory Dock hide + pynput
aborts Tk with SIGTRAP.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Callable


_DISABLE_ENV = "INTERVIEW_COPILOT_DISABLE_GLOBAL_HOTKEYS"
_listener_active = False
_listener = None

# Hardware codes: macOS kVK_ANSI_Grave=50, Windows VK_OEM_3=0xC0.
_GRAVE_VKS = {50, 0xC0, 192}


def is_windows() -> bool:
    return sys.platform == "win32"


def overlay_close_hint() -> str:
    if is_windows():
        return "Ctrl+Shift+W close   ·   Ctrl+Shift+O click-through"
    return "⌘⇧W close   ·   ⌘⇧O click-through"


def listen_toggle_hint() -> str:
    return "` listen  ·  ` again stop & answer"


def ui_font(size: int = 10, *, bold: bool = False) -> tuple:
    weight = "bold" if bold else "normal"
    family = "Segoe UI" if is_windows() else "Helvetica"
    return (family, size, weight) if bold else (family, size)


def mono_font(size: int = 12) -> tuple:
    family = "Consolas" if is_windows() else "Menlo"
    return (family, size)


def global_hotkeys_allowed() -> bool:
    if os.environ.get(_DISABLE_ENV) == "1":
        return False
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    return True


def global_hotkeys_active() -> bool:
    return _listener_active


def is_listen_toggle_key(key: Any) -> bool:
    """True for the bare grave/backtick key, including macOS vk=50 with no char."""
    if key is None:
        return False
    char = getattr(key, "char", None) or getattr(key, "_char", None)
    if char == "`":
        return True
    if char == "~":
        return False
    vk = getattr(key, "vk", None)
    try:
        if vk is not None and int(vk) in _GRAVE_VKS:
            return True
    except (TypeError, ValueError):
        pass
    name = str(getattr(key, "name", "") or "").lower()
    return name in {"grave", "backquote", "oem_3"}


def start_global_listen_hotkeys(
    *,
    on_listen_toggle: Callable[[], None],
    on_stop: Callable[[], None] | None = None,
    on_screenshot: Callable[[], None] | None = None,
    force: bool = False,
) -> Any:
    """OS-global `` ` `` listen toggle, even when the app window is unfocused.

    Returns the pynput Listener (call .stop() on shutdown), or None if
    hotkeys are disabled / pynput is unavailable. Safe to call twice.
    """
    global _listener_active, _listener
    if _listener is not None and _listener_active:
        return _listener
    if not force and not global_hotkeys_allowed():
        return None
    from pynput import keyboard

    held = {"grave": False}

    def _fire_toggle() -> None:
        try:
            on_listen_toggle()
        except Exception as exc:
            print(f"Global ` listen toggle error: {exc}")

    def on_press(key):
        if is_listen_toggle_key(key):
            if not held["grave"]:
                held["grave"] = True
                _fire_toggle()
            return
        try:
            ch = getattr(key, "char", None)
            if ch == "~" and on_stop:
                on_stop()
            elif ch == "!" and on_screenshot:
                on_screenshot()
        except Exception:
            pass

    def on_release(key):
        if is_listen_toggle_key(key) or getattr(key, "char", None) in {"`", "~"}:
            held["grave"] = False

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    _listener = listener
    _listener_active = True
    print("Global ` listen hotkey armed (works while other apps are focused).")
    return listener


def stop_global_listen_hotkeys(listener: Any = None) -> None:
    global _listener_active, _listener
    target = listener if listener is not None else _listener
    _listener_active = False
    _listener = None
    if target is None:
        return
    try:
        target.stop()
    except Exception:
        pass
