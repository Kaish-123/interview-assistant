"""Privacy overlay API + native adapter smoke tests."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from interview_copilot.apps.web.server import app
from interview_copilot.apps.web.privacy_native import (
    native_overlay_supported,
    spawn_native_overlay,
    stop_native_overlay,
)
from interview_copilot.apps.web.runtime import RuntimeEngine


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY", "1")
    return TestClient(app)


def test_index_has_float_and_privacy_controls(client):
    html = client.get("/app").text
    assert "btn-overlay-float" in html
    assert "btn-overlay-privacy" in html
    assert "share-safe-cover" in html
    assert "privacy.js" in html
    assert "Hide from share" in html


def test_privacy_js_served(client):
    r = client.get("/static/js/privacy.js")
    assert r.status_code == 200
    body = r.text
    assert "documentPictureInPicture" in body
    assert "enableHideFromShare" in body
    assert "_fallbackAttempted" in body
    assert "privacyOn" in body
    assert "if (!id) return" in body


def test_status_includes_privacy_native(client):
    data = client.get("/api/status").json()
    assert "privacy_native" in data
    assert "os" in data
    assert data["privacy_native"] is False


def test_engine_snapshot_includes_partial_fields(client):
    created = client.post("/api/engines", json={"kind": "live"}).json()
    eid = created["engine_id"]
    snap = client.get(f"/api/engines/{eid}").json()
    assert snap["partial"] == ""
    assert "last_question" in snap
    assert "last_answer" in snap


def test_privacy_overlay_disabled_in_tests(client):
    created = client.post("/api/engines", json={"kind": "live"}).json()
    r = client.post("/api/privacy/overlay", json={"engine_id": created["engine_id"]})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert data["native"] is False
    assert "reason" in data


def test_privacy_command_and_state(client):
    eid = client.post("/api/engines", json={"kind": "live"}).json()["engine_id"]
    cmd = client.post("/api/privacy/command", json={"engine_id": eid, "command": "listen"}).json()
    assert cmd["ok"] is True
    assert cmd["seq"] == 1
    assert cmd["command"] == "listen"
    st = client.post(
        "/api/privacy/state",
        json={
            "engine_id": eid,
            "listening": True,
            "status": "Listening…",
            "transcript": "hello",
            "answer": "hi there",
        },
    ).json()
    assert st["ok"] is True
    snap = client.get(f"/api/engines/{eid}").json()
    overlay = snap["meta"]["overlay"]
    assert overlay["command"] == "listen"
    assert overlay["listening"] is True
    assert overlay["transcript"] == "hello"
    assert overlay["answer"] == "hi there"
    assert snap["last_question"] == "hello"
    assert snap["last_answer"] == "hi there"
    tog = client.post("/api/privacy/command", json={"engine_id": eid, "command": "toggle_listen"}).json()
    assert tog["ok"] is True
    assert tog["command"] == "toggle_listen"
    assert tog["seq"] == 2


def test_privacy_stop(client):
    eid = client.post("/api/engines", json={"kind": "live"}).json()["engine_id"]
    r = client.post("/api/privacy/overlay/stop", json={"engine_id": eid})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_native_overlay_spawn_mocked(monkeypatch):
    monkeypatch.delenv("INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY", raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    runtime = RuntimeEngine(id="abc123", kind="live", engine=MagicMock())
    fake = MagicMock()
    fake.pid = 4242
    fake.poll.return_value = None
    with patch("interview_copilot.apps.web.privacy_native.subprocess.Popen", return_value=fake) as popen:
        result = spawn_native_overlay(runtime, "http://127.0.0.1:8787")
    assert result["ok"] is True
    assert result["native"] is True
    assert result["pid"] == 4242
    assert popen.call_args[0][0][2] == "interview_copilot.apps.web.overlay_window"


def test_native_overlay_spawn_mocked_windows(monkeypatch):
    monkeypatch.delenv("INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY", raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    runtime = RuntimeEngine(id="win123", kind="live", engine=MagicMock())
    fake = MagicMock()
    fake.pid = 5150
    fake.poll.return_value = None
    with patch("interview_copilot.apps.web.privacy_native.subprocess.Popen", return_value=fake) as popen:
        result = spawn_native_overlay(runtime, "http://127.0.0.1:8787")
    assert result["ok"] is True
    assert result["pid"] == 5150
    kwargs = popen.call_args.kwargs
    assert "creationflags" in kwargs


def test_windows_privacy_returns_false_off_windows():
    from interview_copilot.platform.windows.privacy import (
        exclude_tk_window_from_capture,
        hide_from_taskbar,
        not_implemented_message,
        set_click_through,
    )

    assert exclude_tk_window_from_capture(None) is False
    assert hide_from_taskbar(None) is False
    assert set_click_through(None, True, title="Live Assist") is False
    assert "WDA_EXCLUDEFROMCAPTURE" in not_implemented_message()


def test_windows_exclude_sets_affinity(monkeypatch):
    from interview_copilot.platform.windows import privacy as wp

    monkeypatch.setattr(wp, "_is_windows", lambda: True)
    fake = MagicMock()
    fake.GetAncestor.return_value = 1234
    fake.SetWindowDisplayAffinity.return_value = 1
    monkeypatch.setattr(wp, "_user32", lambda: fake)
    tk_win = MagicMock()
    tk_win.winfo_id.return_value = 99
    tk_win.title.return_value = "Live Assist"
    assert wp.exclude_tk_window_from_capture(tk_win) is True
    fake.SetWindowDisplayAffinity.assert_called()


def test_windows_click_through_toggles_exstyle(monkeypatch):
    from interview_copilot.platform.windows import privacy as wp

    monkeypatch.setattr(wp, "_is_windows", lambda: True)
    fake = MagicMock()
    fake.FindWindowW.return_value = 88
    fake.GetWindowLongPtrW.return_value = 0
    fake.SetWindowLongPtrW.return_value = 1
    fake.GetWindowLongW.return_value = 0
    fake.SetWindowLongW.return_value = 1
    monkeypatch.setattr(wp, "_user32", lambda: fake)
    assert wp.set_click_through(None, True, title="Live Assist") is True
    assert wp.set_click_through(None, False, title="Live Assist") is True


def test_overlay_main_allows_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    with patch("interview_copilot.apps.web.overlay_window.run_overlay") as run:
        from interview_copilot.apps.web.overlay_window import main

        assert main(["--engine-id", "x", "--base", "http://127.0.0.1:8787"]) == 0
        run.assert_called_once()


def test_overlay_main_rejects_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    from interview_copilot.apps.web.overlay_window import main

    assert main(["--engine-id", "x"]) == 2


def test_overlay_start_geometry_format():
    from interview_copilot.platform.privacy import overlay_start_geometry

    geo = overlay_start_geometry(440, 560)
    assert geo.startswith("440x560+")
    assert geo.count("+") == 2


def test_privacy_facade_overlay_supported(monkeypatch):
    from interview_copilot.platform.privacy import overlay_supported

    monkeypatch.delenv("INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY", raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    assert overlay_supported() is True
    monkeypatch.setattr(sys, "platform", "linux")
    assert overlay_supported() is False


def test_hotkey_hint_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    from interview_copilot.platform.hotkeys import overlay_close_hint, ui_font

    assert "Ctrl+Shift" in overlay_close_hint()
    assert ui_font()[0] == "Segoe UI"


def test_macos_privacy_helpers_import():
    from interview_copilot.platform.macos.privacy import (
        exclude_all_app_windows_from_capture,
        hide_app_from_dock,
        NSWindowSharingNone,
    )

    assert NSWindowSharingNone == 0
    if sys.platform != "darwin":
        assert hide_app_from_dock() is False
        assert exclude_all_app_windows_from_capture() is False


def test_click_through_on_then_off(monkeypatch):
    """Turning click-through off must work even when the window is not key."""
    pytest.importorskip("tkinter")
    if sys.platform != "darwin":
        pytest.skip("macOS only")
    import tkinter as tk
    from interview_copilot.platform.macos.privacy import set_click_through

    root = tk.Tk()
    root.title("Live Assist")
    root.withdraw()
    root.update_idletasks()
    try:
        assert set_click_through(root, True, title="Live Assist") is True
        assert set_click_through(root, False, title="Live Assist") is True
    finally:
        root.destroy()


def test_click_through_spares_control_strip():
    """Control strip stays clickable while the main overlay ignores the mouse."""
    pytest.importorskip("tkinter")
    if sys.platform != "darwin":
        pytest.skip("macOS only")
    import tkinter as tk
    from interview_copilot.platform.macos.privacy import (
        set_click_through,
        window_ignores_mouse_events,
    )

    root = tk.Tk()
    root.title("Live Assist")
    root.geometry("320x200+40+80")
    chip = tk.Toplevel(root)
    chip.title("Live Assist Controls")
    chip.geometry("320x44+40+24")
    root.update()
    chip.update()
    try:
        assert set_click_through(root, True, title="Live Assist") is True
        assert window_ignores_mouse_events("Live Assist") is True
        assert window_ignores_mouse_events("Live Assist Controls") is False
        assert set_click_through(chip, False, title="Live Assist Controls") is True
        assert window_ignores_mouse_events("Live Assist Controls") is False
        assert set_click_through(root, False, title="Live Assist") is True
        assert window_ignores_mouse_events("Live Assist") is False
    finally:
        chip.destroy()
        root.destroy()


def test_close_chip_sits_on_overlay_corner():
    from interview_copilot.apps.web.overlay_window import close_chip_geometry

    assert close_chip_geometry(48, 80, 440) == "36x28+448+86"
    assert close_chip_geometry(0, 0, 200) == "36x28+160+8"


def test_overlay_qa_prefers_live_tab_state():
    from interview_copilot.apps.web.overlay_window import (
        moved_geometry,
        overlay_qa_from_snapshot,
        should_apply_answer,
    )

    q, a = overlay_qa_from_snapshot(
        {
            "messages": [{"role": "user", "content": "old chat q"}],
            "last_question": "old chat q",
            "partial": "",
            "meta": {"overlay": {"transcript": "How does TCP work?", "answer": "TCP is..."}},
        }
    )
    assert q == "How does TCP work?"
    assert a.startswith("TCP")
    waiting, placeholder = overlay_qa_from_snapshot({"messages": [], "meta": {}})
    assert "Waiting" in waiting
    assert "Listening" in placeholder or "answers" in placeholder.lower()

    from interview_copilot.apps.web.overlay_window import overlay_log_from_snapshot

    history = overlay_log_from_snapshot(
        {
            "messages": [
                {"role": "system", "content": "ignore"},
                {"role": "user", "content": "What is TCP?"},
                {"role": "assistant", "content": "TCP is a transport protocol."},
                {"role": "user", "content": "And UDP?"},
                {"role": "assistant", "content": "UDP is datagram-based."},
            ],
            "meta": {},
        }
    )
    assert history.count("QUESTION:") == 2
    assert "What is TCP?" in history
    assert "And UDP?" in history
    assert "datagram-based" in history
    live_turn = overlay_log_from_snapshot(
        {
            "messages": [
                {"role": "user", "content": "old q"},
                {"role": "assistant", "content": "old a"},
            ],
            "meta": {"overlay": {"transcript": "How does TCP work?", "answer": "TCP is..."}},
        }
    )
    assert "old q" in live_turn
    assert "How does TCP work?" in live_turn
    assert "TCP is..." in live_turn
    idle = overlay_log_from_snapshot({"messages": [], "meta": {}})
    assert "Waiting" in idle
    assert "Scroll" in idle
    snow = (
        "If you want to talk to computer you need to talk to them in terms of come. "
        "If you want to talk to computer you need to talk to them in terms of zeros. "
        "If you want to talk to computer you need to talk to them in terms of zeros and ones of course"
    )
    q_clean, _ = overlay_qa_from_snapshot({"meta": {"overlay": {"transcript": snow}}})
    assert q_clean.count("If you want to talk to") == 1
    assert "of course" in q_clean
    assert "come." not in q_clean
    assert moved_geometry(100, 80, 12, -5) == "+112+75"
    assert should_apply_answer("", "Hello") is True
    assert should_apply_answer("Hello world this is long", "Hello") is False
    assert should_apply_answer("Hello", "Hello there") is True
    assert should_apply_answer("Done answer", "Listening — answers stream here.") is False


def test_overlay_turns_keep_new_question_at_bottom():
    from interview_copilot.apps.web.overlay_window import overlay_turns_from_snapshot

    first = overlay_turns_from_snapshot(
        {
            "messages": [
                {"role": "user", "content": "What is TCP?"},
                {"role": "assistant", "content": "A transport protocol."},
            ],
            "meta": {"overlay": {"transcript": "How does UDP work?"}},
        }
    )
    assert first[-1] == ("user", "How does UDP work?")
    assert first[0] == ("user", "What is TCP?")
    assert first[1] == ("assistant", "A transport protocol.")

    growing = overlay_turns_from_snapshot(
        {
            "messages": [
                {"role": "user", "content": "What is TCP?"},
                {"role": "assistant", "content": "A transport protocol."},
            ],
            "meta": {
                "overlay": {
                    "transcript": "How does UDP work in detail?",
                    "answer": "UDP is datagram-based.",
                }
            },
        }
    )
    assert growing[-2] == ("user", "How does UDP work in detail?")
    assert growing[-1] == ("assistant", "UDP is datagram-based.")
    assert growing[1] == ("assistant", "A transport protocol.")

    live_update = overlay_turns_from_snapshot(
        {
            "messages": [{"role": "user", "content": "What is TCP?"}],
            "meta": {"overlay": {"transcript": "What is TCP exactly?"}},
        }
    )
    assert live_update == [("user", "What is TCP exactly?")]

    committed = overlay_turns_from_snapshot(
        {
            "messages": [
                {"role": "user", "content": "What is TCP?"},
                {"role": "assistant", "content": "A transport protocol."},
            ],
            "meta": {
                "overlay": {
                    "transcript": "What is TCP?",
                    "answer": "A transport protocol.",
                }
            },
        }
    )
    assert committed == [
        ("user", "What is TCP?"),
        ("assistant", "A transport protocol."),
    ]

    streaming = overlay_turns_from_snapshot(
        {
            "messages": [
                {"role": "user", "content": "What is TCP?"},
                {"role": "assistant", "content": "TCP"},
            ],
            "meta": {
                "overlay": {
                    "transcript": "What is TCP?",
                    "answer": "TCP is a transport protocol.",
                }
            },
        }
    )
    assert streaming == [
        ("user", "What is TCP?"),
        ("assistant", "TCP is a transport protocol."),
    ]


def test_overlay_window_does_not_use_global_hotkeys():
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "apps/web/overlay_window.py"
    text = src.read_text(encoding="utf-8")
    assert "GlobalHotKeys" not in text
    assert "from pynput" not in text
    assert "bring_app_to_front" in text
    assert "os._exit(0)" in text
    assert "Toplevel" in text
    assert "Live Assist Close" in text
    assert "close_chip_geometry" in text
    assert "Live Assist Controls" not in text
    assert "overlay_start_geometry" in text
    assert "_start_drag" in text
    assert 'send_cmd("toggle_listen")' in text
    assert 'send_cmd("listen")' in text
    assert 'send_cmd("stop_listen")' in text
    assert "Stop & Process" in text
    assert "start_listen_from_overlay" in text
    assert "stop_listen_from_overlay" in text
    assert "listen_toggle_hint" in text
    assert "overlay_log_from_snapshot" in text
    assert "question_type_chunks" in text
    assert "_enqueue_suffix" in text
    assert "_pump_type" in text
    assert "root.after(42, _pump_type)" in text
    assert "q_var" not in text
    assert "root.after(120, poll)" in text


def test_spawn_reports_dead_overlay_process(monkeypatch):
    monkeypatch.delenv("INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY", raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    runtime = RuntimeEngine(id="dead1", kind="live", engine=MagicMock())
    fake = MagicMock()
    fake.pid = 99
    fake.poll.return_value = 133
    with patch("interview_copilot.apps.web.privacy_native.subprocess.Popen", return_value=fake):
        result = spawn_native_overlay(runtime, "http://127.0.0.1:8787")
    assert result["ok"] is False
    assert result["native"] is False
    assert "133" in result["reason"]


def test_pid_alive_helper():
    from interview_copilot.apps.web.privacy_native import pid_alive

    assert pid_alive(os.getpid()) is True
    assert pid_alive(None) is False
    assert pid_alive(999_999_999) is False


def test_stop_native_overlay_reaps_popen(monkeypatch):
    monkeypatch.delenv("INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY", raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    runtime = RuntimeEngine(id="stop-reap", kind="live", engine=MagicMock())
    fake = MagicMock()
    fake.pid = 424242
    fake.poll.return_value = None
    fake.wait.return_value = 0
    with (
        patch("interview_copilot.apps.web.privacy_native.subprocess.Popen", return_value=fake),
        patch("interview_copilot.apps.web.privacy_native.os.killpg"),
        patch("interview_copilot.apps.web.privacy_native.os.kill"),
    ):
        result = spawn_native_overlay(runtime, "http://127.0.0.1:8787")
        assert result["ok"] is True
        stop_native_overlay(runtime)
    fake.wait.assert_called()
    assert runtime.meta["overlay"]["alive"] is False
    assert runtime.meta["overlay"]["pid"] is None


def test_overlay_process_stays_alive_on_macos():
    """Regression: Accessory Dock hide + pynput used to abort Tk with SIGTRAP (~exit 133)."""
    pytest.importorskip("tkinter")
    if sys.platform != "darwin":
        pytest.skip("macOS only")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-u",
            "-m",
            "interview_copilot.apps.web.overlay_window",
            "--engine-id",
            "stay-alive-test",
            "--base",
            "http://127.0.0.1:9",
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        time.sleep(1.6)
        assert proc.poll() is None, f"overlay exited with {proc.poll()}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def test_overlay_spawn_and_stop_on_macos(monkeypatch):
    """Float / Hide from share must stay up, then actually exit on stop."""
    pytest.importorskip("tkinter")
    if sys.platform != "darwin":
        pytest.skip("macOS only")
    monkeypatch.delenv("INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY", raising=False)
    from interview_copilot.apps.web.privacy_native import pid_alive

    runtime = RuntimeEngine(id="spawn-stop-e2e", kind="live", engine=MagicMock())
    result = spawn_native_overlay(runtime, "http://127.0.0.1:9")
    assert result["ok"] is True, result
    pid = int(result["pid"])
    try:
        time.sleep(1.6)
        assert pid_alive(pid), "overlay died after opening"
        assert runtime.meta["overlay"]["alive"] is True
    finally:
        stop_native_overlay(runtime)
    time.sleep(0.15)
    assert not pid_alive(pid), "overlay should be gone after stop"
    assert runtime.meta["overlay"]["pid"] is None
    assert runtime.meta["overlay"]["alive"] is False
