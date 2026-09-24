"""Windows privacy adapters — capture exclude, taskbar hide, click-through.

Honest overlay privacy (build flow §4 / W5 / W6): omit this process's windows
from capture via WDA_EXCLUDEFROMCAPTURE, hide the overlay from the taskbar,
and pass clicks through the answer pane. Not for disguising the process.
"""

from __future__ import annotations

import ctypes
import sys
from typing import Any

WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
GA_ROOT = 2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020


def _is_windows() -> bool:
    return sys.platform == "win32"


def _user32():
    if not _is_windows():
        return None
    try:
        return ctypes.windll.user32
    except Exception:
        return None


def _kernel32():
    if not _is_windows():
        return None
    try:
        return ctypes.windll.kernel32
    except Exception:
        return None


def _hwnd_from_tk(tk_window: Any) -> int:
    user32 = _user32()
    if user32 is None or tk_window is None:
        return 0
    try:
        tk_window.update_idletasks()
        wid = int(tk_window.winfo_id())
    except Exception:
        return 0
    try:
        root = int(user32.GetAncestor(wid, GA_ROOT) or 0)
        return root or wid
    except Exception:
        return wid


def _hwnd_by_title(title: str) -> int:
    user32 = _user32()
    if user32 is None or not title:
        return 0
    try:
        return int(user32.FindWindowW(None, str(title)) or 0)
    except Exception:
        return 0


def _resolve_hwnd(tk_window: Any, title: str | None) -> int:
    if title:
        found = _hwnd_by_title(title)
        if found:
            return found
    return _hwnd_from_tk(tk_window)


def _set_affinity(hwnd: int, affinity: int) -> bool:
    user32 = _user32()
    if user32 is None or not hwnd:
        return False
    try:
        return bool(user32.SetWindowDisplayAffinity(hwnd, ctypes.c_uint(affinity)))
    except Exception:
        return False


def _long_ptr(user32):
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        getter = user32.GetWindowLongPtrW
        setter = user32.SetWindowLongPtrW
    else:
        getter = user32.GetWindowLongW
        setter = user32.SetWindowLongW
    return getter, setter


def _exstyle(hwnd: int) -> int:
    user32 = _user32()
    if user32 is None or not hwnd:
        return 0
    getter, _setter = _long_ptr(user32)
    try:
        return int(getter(hwnd, GWL_EXSTYLE) or 0)
    except Exception:
        return 0


def _set_exstyle(hwnd: int, style: int) -> bool:
    user32 = _user32()
    if user32 is None or not hwnd:
        return False
    _getter, setter = _long_ptr(user32)
    try:
        setter(hwnd, GWL_EXSTYLE, style)
        user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
        )
        return True
    except Exception:
        return False


def exclude_tk_window_from_capture(tk_window: Any) -> bool:
    hwnd = _hwnd_from_tk(tk_window)
    if not hwnd:
        title = ""
        try:
            title = str(tk_window.title() or "") if tk_window is not None else ""
        except Exception:
            title = ""
        hwnd = _hwnd_by_title(title)
    return _set_affinity(hwnd, WDA_EXCLUDEFROMCAPTURE)


def exclude_all_app_windows_from_capture() -> bool:
    user32 = _user32()
    kernel32 = _kernel32()
    if user32 is None or kernel32 is None:
        return False
    try:
        pid = int(kernel32.GetCurrentProcessId())
    except Exception:
        return False
    found = {"ok": False}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _callback(hwnd, _lparam):
        proc = ctypes.c_ulong()
        try:
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc))
        except Exception:
            return True
        if int(proc.value) != pid:
            return True
        if _set_affinity(int(hwnd), WDA_EXCLUDEFROMCAPTURE):
            found["ok"] = True
        return True

    try:
        user32.EnumWindows(_callback, 0)
    except Exception:
        return False
    return found["ok"]


def hide_from_taskbar(tk_window: Any) -> bool:
    hwnd = _hwnd_from_tk(tk_window)
    if not hwnd:
        return False
    style = _exstyle(hwnd)
    style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
    return _set_exstyle(hwnd, style)


def hide_app_from_dock() -> bool:
    """Windows equivalent of Dock hide: process windows become tool windows."""
    if not _is_windows():
        return False
    exclude_all_app_windows_from_capture()
    return True


def bring_app_to_front(tk_window: Any = None) -> bool:
    user32 = _user32()
    hwnd = _resolve_hwnd(tk_window, "Live Assist")
    if user32 is None or not hwnd:
        return False
    try:
        user32.ShowWindow(hwnd, 5)  # SW_SHOW
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def set_click_through(tk_window: Any, enabled: bool, *, title: str | None = None) -> bool:
    """Pass mouse events through one overlay window only (not the control strip)."""
    match = title
    if match is None and tk_window is not None:
        try:
            match = str(tk_window.title() or "")
        except Exception:
            match = ""
    hwnd = _resolve_hwnd(tk_window, match)
    if not hwnd:
        return False
    style = _exstyle(hwnd)
    if enabled:
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
    else:
        style = (style | WS_EX_LAYERED) & ~WS_EX_TRANSPARENT
    return _set_exstyle(hwnd, style)


def window_ignores_mouse_events(title: str) -> bool | None:
    hwnd = _hwnd_by_title(title)
    if not hwnd:
        return None
    return bool(_exstyle(hwnd) & WS_EX_TRANSPARENT)


def overlay_start_geometry(width: int = 440, height: int = 560) -> str:
    """Park the overlay on the monitor under the cursor."""
    if not _is_windows():
        return f"{width}x{height}+64+80"
    user32 = _user32()
    if user32 is None:
        return f"{width}x{height}+64+80"
    try:
        class _POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        class _RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class _MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("rcMonitor", _RECT),
                ("rcWork", _RECT),
                ("dwFlags", ctypes.c_ulong),
            ]

        pt = _POINT()
        if not user32.GetCursorPos(ctypes.byref(pt)):
            return f"{width}x{height}+64+80"
        monitor = user32.MonitorFromPoint(pt, 2)  # MONITOR_DEFAULTTONEAREST
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(_MONITORINFO)
        if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return f"{width}x{height}+64+80"
        work = info.rcWork
        x = int(work.right) - width - 28
        y = int(work.top) + 28
        x = max(int(work.left) + 16, x)
        return f"{width}x{height}+{x}+{y}"
    except Exception:
        return f"{width}x{height}+64+80"


def not_implemented_message() -> str:
    return (
        "On Windows, Hide from share uses SetWindowDisplayAffinity "
        "(WDA_EXCLUDEFROMCAPTURE) and a tool window so the overlay stays off "
        "the taskbar. Share the meeting window/tab if an older Windows build "
        "ignores capture exclusion."
    )
