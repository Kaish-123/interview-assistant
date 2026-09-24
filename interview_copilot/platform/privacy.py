"""OS privacy facade — apps and packages import this, never macos/windows directly.

macOS: NSWindowSharingNone + Dock accessory + ignoresMouseEvents
Windows: SetWindowDisplayAffinity (WDA_EXCLUDEFROMCAPTURE) + tool window + WS_EX_TRANSPARENT
Linux: no native overlay (browser float / PiP fallback)
"""

from __future__ import annotations

import os
import sys
from typing import Any

_DISABLE_ENV = "INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY"


def overlay_supported() -> bool:
    if os.environ.get(_DISABLE_ENV) == "1":
        return False
    return sys.platform in {"darwin", "win32"}


def _impl():
    if sys.platform == "darwin":
        from interview_copilot.platform.macos import privacy as impl

        return impl
    if sys.platform == "win32":
        from interview_copilot.platform.windows import privacy as impl

        return impl
    return None


def overlay_start_geometry(width: int = 440, height: int = 560) -> str:
    """Place the overlay on the display under the mouse when the OS adapter can."""
    impl = _impl()
    fn = getattr(impl, "overlay_start_geometry", None) if impl is not None else None
    if fn is None:
        return f"{width}x{height}+64+80"
    try:
        return str(fn(width, height))
    except Exception:
        return f"{width}x{height}+64+80"


def hide_app_from_dock() -> bool:
    impl = _impl()
    return bool(impl and impl.hide_app_from_dock())


def bring_app_to_front(tk_window: Any = None) -> bool:
    """Make the overlay visible and focused after spawn (Dock/taskbar hide comes after)."""
    impl = _impl()
    if impl is None:
        return False
    fn = getattr(impl, "bring_app_to_front", None)
    if fn is None:
        return False
    try:
        return bool(fn(tk_window))
    except TypeError:
        return bool(fn())


def hide_from_taskbar(tk_window: Any) -> bool:
    impl = _impl()
    if impl is None:
        return False
    fn = getattr(impl, "hide_from_taskbar", None)
    if fn is None:
        return hide_app_from_dock()
    return bool(fn(tk_window))


def exclude_all_app_windows_from_capture() -> bool:
    impl = _impl()
    return bool(impl and impl.exclude_all_app_windows_from_capture())


def exclude_tk_window_from_capture(tk_window: Any) -> bool:
    impl = _impl()
    return bool(impl and impl.exclude_tk_window_from_capture(tk_window))


def set_click_through(tk_window: Any, enabled: bool, *, title: str | None = None) -> bool:
    impl = _impl()
    if impl is None:
        return False
    try:
        return bool(impl.set_click_through(tk_window, enabled, title=title))
    except TypeError:
        return bool(impl.set_click_through(tk_window, enabled))


def window_ignores_mouse_events(title: str) -> bool | None:
    impl = _impl()
    if impl is None:
        return None
    fn = getattr(impl, "window_ignores_mouse_events", None)
    if fn is None:
        return None
    return fn(title)
