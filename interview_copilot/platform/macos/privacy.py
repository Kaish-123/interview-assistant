"""macOS privacy adapters — capture exclude, click-through, Dock hide.

Honest overlay privacy (build flow §4): exclude this process's windows from
screen capture and optionally hide the Dock icon. Not for disguising the app.
"""

from __future__ import annotations

import sys
from typing import Any

NSWindowSharingNone = 0


def _appkit():
    if sys.platform != "darwin":
        return None
    try:
        import AppKit  # type: ignore
        return AppKit
    except Exception:
        return None


def overlay_start_geometry(width: int = 440, height: int = 560) -> str:
    """Park the overlay on the display under the mouse (same screen as Float)."""
    AppKit = _appkit()
    if AppKit is None:
        return f"{width}x{height}+64+80"
    try:
        mouse = AppKit.NSEvent.mouseLocation()
        screens = list(AppKit.NSScreen.screens() or [])
        if not screens:
            return f"{width}x{height}+64+80"
        primary_h = float(screens[0].frame().size.height)
        chosen = screens[0]
        for screen in screens:
            frame = screen.frame()
            x0 = float(frame.origin.x)
            y0 = float(frame.origin.y)
            x1 = x0 + float(frame.size.width)
            y1 = y0 + float(frame.size.height)
            if x0 <= float(mouse.x) <= x1 and y0 <= float(mouse.y) <= y1:
                chosen = screen
                break
        vis = chosen.visibleFrame()
        left = float(vis.origin.x) + float(vis.size.width) - width - 28
        left = max(float(vis.origin.x) + 16, left)
        cocoa_top = float(vis.origin.y) + float(vis.size.height) - 28
        tk_y = int(round(primary_h - cocoa_top))
        if tk_y < 22:
            tk_y = 22
        return f"{width}x{height}+{int(round(left))}+{tk_y}"
    except Exception:
        return f"{width}x{height}+64+80"


def bring_app_to_front(_tk_window: Any = None) -> bool:
    """Show the overlay in front of the browser after spawn."""
    AppKit = _appkit()
    if AppKit is None:
        return False
    try:
        app = AppKit.NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)
        return True
    except Exception:
        return False


def hide_app_from_dock() -> bool:
    """LSUIElement-style: overlay process stays off the Dock."""
    AppKit = _appkit()
    if AppKit is None:
        return False
    try:
        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        return True
    except Exception:
        return False


def exclude_all_app_windows_from_capture() -> bool:
    """Mark every NSWindow in this process as NSWindowSharingNone."""
    AppKit = _appkit()
    if AppKit is None:
        return False
    try:
        AppKit.NSApplication.sharedApplication()
        behavior = (
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
            | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
            | AppKit.NSWindowCollectionBehaviorStationary
        )
        ok = False
        for win in AppKit.NSApp.windows():
            win.setSharingType_(AppKit.NSWindowSharingNone)
            try:
                win.setCollectionBehavior_(behavior)
            except Exception:
                pass
            ok = True
        return ok
    except Exception:
        return False


def exclude_tk_window_from_capture(tk_window: Any) -> bool:
    """Exclude a Tk Aqua window (and every other window in this process)."""
    if sys.platform != "darwin":
        return False
    try:
        tk_window.update_idletasks()
    except Exception:
        pass
    return exclude_all_app_windows_from_capture()


def hide_from_taskbar(_tk_window: Any) -> bool:
    """macOS has no taskbar; Dock hide covers the same product intent."""
    return hide_app_from_dock()


def window_ignores_mouse_events(title: str) -> bool | None:
    """Return ignoresMouseEvents for the NSWindow with this title, if any."""
    AppKit = _appkit()
    if AppKit is None:
        return None
    try:
        AppKit.NSApplication.sharedApplication()
        for win in AppKit.NSApp.windows() or []:
            if str(win.title() or "") == title:
                return bool(win.ignoresMouseEvents())
    except Exception:
        return None
    return None


def set_click_through(tk_window: Any, enabled: bool, *, title: str | None = None) -> bool:
    """Pass mouse events through one overlay window only.

    The always-clickable control strip uses a different title so it stays hittable.
    """
    AppKit = _appkit()
    if AppKit is None:
        return False
    match = title
    if match is None and tk_window is not None:
        try:
            match = str(tk_window.title() or "")
        except Exception:
            match = ""
    if not match:
        match = "Live Assist"
    try:
        if tk_window is not None:
            tk_window.update_idletasks()
        AppKit.NSApplication.sharedApplication()
        ok = False
        for win in AppKit.NSApp.windows() or []:
            if str(win.title() or "") != match:
                continue
            win.setIgnoresMouseEvents_(bool(enabled))
            ok = True
        return ok
    except Exception:
        return False
