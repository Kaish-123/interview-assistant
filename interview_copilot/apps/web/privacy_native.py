"""Spawn / stop the capture-excluded native overlay process (macOS + Windows)."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from typing import Any

from interview_copilot.apps.web.runtime import RuntimeEngine
from interview_copilot.platform.privacy import overlay_supported
from interview_copilot.shared.config.paths import get_paths

_DISABLE_ENV = "INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY"
_log_handles: list[Any] = []
_overlay_procs: dict[str, subprocess.Popen] = {}
_listen_workers: dict[str, Any] = {}
_proc_lock = threading.Lock()


def native_overlay_supported() -> bool:
    return overlay_supported()


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False
    except Exception:
        return False


def _overlay_log_path():
    return get_paths().logs_dir / "overlay.log"


def _popen_kwargs(log_fh) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "stdout": log_fh,
        "stderr": subprocess.STDOUT,
        "cwd": str(get_paths().repo_root),
        "env": {**os.environ, "PYTHONUNBUFFERED": "1"},
    }
    if sys.platform == "win32":
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        kwargs["creationflags"] = flags
    else:
        kwargs["start_new_session"] = True
    return kwargs


def _wait_overlay_alive(proc: subprocess.Popen, timeout: float = 1.15) -> tuple[bool, int | None]:
    deadline = time.monotonic() + timeout
    while True:
        code = proc.poll()
        if code is not None:
            return False, int(code)
        if time.monotonic() >= deadline:
            return True, None
        time.sleep(0.08)


def _read_overlay_log_tail(limit: int = 1200) -> str:
    path = _overlay_log_path()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return text[-limit:].strip()


def spawn_native_overlay(runtime: RuntimeEngine, base_url: str) -> dict[str, Any]:
    stop_native_overlay(runtime)
    if not native_overlay_supported():
        if os.environ.get(_DISABLE_ENV) == "1":
            reason = "Native overlay disabled by INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY."
        elif sys.platform not in {"darwin", "win32"}:
            reason = "Native hide-from-share uses a desktop overlay on macOS and Windows."
        else:
            reason = "Native overlay is not available."
        return {"ok": False, "native": False, "alive": False, "reason": reason}

    cmd = [
        sys.executable,
        "-m",
        "interview_copilot.apps.web.overlay_window",
        "--engine-id",
        runtime.id,
        "--base",
        base_url.rstrip("/"),
    ]
    log_path = _overlay_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        log_fh = log_path.open("ab")
        _log_handles.append(log_fh)
        log_fh.write(f"\n--- spawn {runtime.id} ---\n".encode("utf-8"))
        log_fh.flush()
        proc = subprocess.Popen(cmd, **_popen_kwargs(log_fh))
    except Exception as exc:
        return {"ok": False, "native": False, "alive": False, "reason": str(exc)}

    wait = 0.0 if os.environ.get("PYTEST_CURRENT_TEST") else 1.4
    alive, code = _wait_overlay_alive(proc, timeout=wait)
    overlay = runtime.meta.setdefault("overlay", {})
    if not alive:
        overlay["pid"] = None
        overlay["native"] = False
        overlay["alive"] = False
        try:
            proc.wait(timeout=0.2)
        except Exception:
            pass
        tail = _read_overlay_log_tail()
        reason = f"Overlay exited immediately (code {code})."
        if tail:
            reason = f"{reason} {tail[-400:]}"
        return {"ok": False, "native": False, "alive": False, "reason": reason}

    with _proc_lock:
        _overlay_procs[runtime.id] = proc
    overlay["pid"] = proc.pid
    overlay["native"] = True
    overlay["alive"] = True
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        try:
            attach_listen_worker(runtime, base_url.rstrip("/"))
        except Exception:
            pass
    return {"ok": True, "native": True, "alive": True, "pid": proc.pid}


def _send_signal(pid: int, sig: int) -> None:
    try:
        os.killpg(pid, sig)
    except Exception:
        try:
            os.kill(pid, sig)
        except Exception:
            pass


def _kill_overlay_pid(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            check=False,
        )
        return
    _send_signal(pid, signal.SIGTERM)
    deadline = time.monotonic() + 0.45
    while time.monotonic() < deadline and pid_alive(pid):
        time.sleep(0.04)
    if pid_alive(pid):
        _send_signal(pid, signal.SIGKILL)
        deadline = time.monotonic() + 0.3
        while time.monotonic() < deadline and pid_alive(pid):
            time.sleep(0.04)


def _terminate_proc(proc: subprocess.Popen) -> None:
    """Stop the overlay child and reap it so it cannot linger as a zombie."""
    if sys.platform == "win32":
        _kill_overlay_pid(int(proc.pid))
        try:
            proc.wait(timeout=2)
        except Exception:
            pass
        return
    if proc.poll() is not None:
        try:
            proc.wait(timeout=0.2)
        except Exception:
            pass
        return
    _send_signal(int(proc.pid), signal.SIGTERM)
    try:
        proc.wait(timeout=0.7)
        return
    except subprocess.TimeoutExpired:
        pass
    _send_signal(int(proc.pid), signal.SIGKILL)
    try:
        proc.kill()
    except Exception:
        pass
    try:
        proc.wait(timeout=0.7)
    except Exception:
        pass


def web_listen_base_url(base_url: str | None = None) -> str:
    if base_url:
        return base_url.rstrip("/")
    host = os.getenv("WEB_HOST", "127.0.0.1")
    port = os.getenv("WEB_PORT", "8787")
    return f"http://{host}:{port}"


def attach_listen_worker(runtime: RuntimeEngine, base_url: str) -> None:
    """Native BlackHole/mic recorder — works even if the browser tab is hidden."""
    from interview_copilot.apps.web.overlay_listen import OverlayListenWorker

    if get_listen_worker(runtime.id) is not None:
        return

    def on_status(msg: str) -> None:
        overlay = runtime.meta.setdefault("overlay", {})
        overlay["status"] = msg

    worker = OverlayListenWorker(base_url, runtime.id, on_status=on_status)
    with _proc_lock:
        _listen_workers[runtime.id] = worker


def ensure_listen_worker(runtime: RuntimeEngine, base_url: str | None = None):
    """Python-side recorder so `` ` `` works even when the browser tab is unfocused."""
    existing = get_listen_worker(runtime.id)
    if existing is not None:
        return existing
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return None
    try:
        attach_listen_worker(runtime, web_listen_base_url(base_url))
    except Exception as exc:
        print(f"Listen worker unavailable: {exc}")
        return None
    return get_listen_worker(runtime.id)


def stop_listen_worker(runtime: RuntimeEngine) -> None:
    with _proc_lock:
        worker = _listen_workers.pop(runtime.id, None)
    if worker is None:
        return
    try:
        worker.stop_auto()
    except Exception:
        pass


def get_listen_worker(engine_id: str):
    with _proc_lock:
        return _listen_workers.get(engine_id)


def apply_native_listen_command(runtime: RuntimeEngine, command: str) -> bool:
    """Run the listen toggle in a background thread. Returns True if a worker handled it."""
    worker = ensure_listen_worker(runtime)
    if worker is None:
        return False
    overlay = runtime.meta.setdefault("overlay", {})
    overlay["server_listen"] = True

    def _run() -> None:
        try:
            listening = worker.is_manual_listening()
            if command == "listen" and not listening:
                overlay["listening"] = True
                overlay["status"] = "Listening…"
                overlay["transcript"] = ""
                overlay["answer"] = ""
            elif command in {"stop_listen", "toggle_listen"} and listening:
                overlay["listening"] = False
                overlay["status"] = "Transcribing…"
            elif command == "toggle_listen" and not listening:
                overlay["listening"] = True
                overlay["status"] = "Listening…"
                overlay["transcript"] = ""
                overlay["answer"] = ""
            result = worker.apply_toggle_command(command)
            overlay["listening"] = result == "listening"
            if result == "idle":
                overlay["status"] = "Ready"
            elif result == "error":
                overlay["listening"] = False
        except Exception as exc:
            overlay["listening"] = False
            overlay["status"] = str(exc)[:80]

    threading.Thread(target=_run, daemon=True).start()
    return True


def stop_native_overlay(runtime: RuntimeEngine) -> None:
    overlay = runtime.meta.get("overlay") or {}
    with _proc_lock:
        proc = _overlay_procs.pop(runtime.id, None)
    pid = overlay.get("pid")
    if proc is not None:
        _terminate_proc(proc)
    elif pid:
        _kill_overlay_pid(int(pid))
    overlay["pid"] = None
    overlay["native"] = False
    overlay["alive"] = False
    runtime.meta["overlay"] = overlay


def refresh_overlay_liveness(runtime: RuntimeEngine) -> dict[str, Any]:
    overlay = runtime.meta.setdefault("overlay", {})
    with _proc_lock:
        proc = _overlay_procs.get(runtime.id)
    if proc is not None:
        alive = proc.poll() is None
        if not alive:
            with _proc_lock:
                _overlay_procs.pop(runtime.id, None)
            try:
                proc.wait(timeout=0.2)
            except Exception:
                pass
    else:
        pid = overlay.get("pid")
        alive = pid_alive(pid) if overlay.get("native") else False
    overlay["alive"] = alive
    if overlay.get("native") and not alive:
        overlay["native"] = False
        overlay["pid"] = None
    return overlay
