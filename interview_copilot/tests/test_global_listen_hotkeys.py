"""OS-global `` ` `` listen toggle — Studio, browser, and float overlay."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from interview_copilot.apps.web.server import app
from interview_copilot.platform import hotkeys as hk
from interview_copilot.platform.hotkeys import (
    global_hotkeys_allowed,
    is_listen_toggle_key,
    listen_toggle_hint,
    start_global_listen_hotkeys,
    stop_global_listen_hotkeys,
)


@pytest.fixture()
def client():
    return TestClient(app)


class _Key:
    def __init__(self, char=None, vk=None, name=None):
        self.char = char
        self.vk = vk
        self.name = name


def test_listen_toggle_hint_mentions_backtick():
    hint = listen_toggle_hint()
    assert "`" in hint
    assert "listen" in hint.lower()
    assert "answer" in hint.lower()


def test_is_listen_toggle_key_matches_mac_and_windows_grave():
    assert is_listen_toggle_key(_Key(char="`")) is True
    assert is_listen_toggle_key(_Key(vk=50)) is True
    assert is_listen_toggle_key(_Key(vk=192)) is True
    assert is_listen_toggle_key(_Key(name="grave")) is True
    assert is_listen_toggle_key(_Key(char="a")) is False
    assert is_listen_toggle_key(_Key(char="~")) is False
    assert is_listen_toggle_key(None) is False


def test_global_hotkeys_disabled_in_pytest():
    assert global_hotkeys_allowed() is False
    assert start_global_listen_hotkeys(on_listen_toggle=lambda: None) is None
    stop_global_listen_hotkeys(None)


def test_forced_listener_fires_once_per_physical_press():
    captured = {}

    class FakeListener:
        def __init__(self, on_press=None, on_release=None):
            captured["press"] = on_press
            captured["release"] = on_release

        def start(self):
            captured["started"] = True

        def stop(self):
            captured["stopped"] = True

    hits: list[str] = []
    hk._listener = None
    hk._listener_active = False
    with patch("pynput.keyboard.Listener", FakeListener):
        start_global_listen_hotkeys(on_listen_toggle=lambda: hits.append("t"), force=True)
        assert captured.get("started") is True
        captured["press"](_Key(vk=50))
        captured["press"](_Key(vk=50))  # key repeat must not double-toggle
        captured["release"](_Key(vk=50))
        captured["press"](_Key(char="`"))
        captured["release"](_Key(char="`"))
        captured["press"](_Key(char="a"))
        assert hits == ["t", "t"]
        stop_global_listen_hotkeys()
        assert captured.get("stopped") is True
        assert hk.global_hotkeys_active() is False


def test_overlay_listen_toggle_command():
    rec = MagicMock()
    rec.is_recording = False
    rec.start_recording = MagicMock()
    rec.stop_recording = MagicMock(return_value=None)
    with patch("interview_copilot.apps.web.overlay_listen.AudioRecorder", return_value=rec):
        from interview_copilot.apps.web.overlay_listen import OverlayListenWorker

        worker = OverlayListenWorker("http://127.0.0.1:9", "eng1")
        assert worker.apply_toggle_command("listen") == "listening"
        rec.start_recording.assert_called_once()
        rec.is_recording = True
        assert worker.apply_toggle_command("listen") == "listening"
        rec.stop_recording.assert_not_called()
        assert worker.apply_toggle_command("stop_listen") == "idle"
        rec.stop_recording.assert_called_once()
        rec.is_recording = False
        rec.start_recording.reset_mock()
        assert worker.apply_toggle_command("stop_listen") == "idle"
        rec.start_recording.assert_not_called()
        rec.is_recording = False
        assert worker.apply_toggle_command("toggle_listen") == "listening"


def test_listen_and_stop_commands_drive_worker(monkeypatch):
    from interview_copilot.apps.web.privacy_native import apply_native_listen_command
    from interview_copilot.apps.web.runtime import RuntimeEngine

    worker = MagicMock()
    worker.is_manual_listening.return_value = False
    worker.apply_toggle_command.return_value = "listening"
    runtime = RuntimeEngine(id="hot1", kind="live", engine=MagicMock())
    monkeypatch.setattr(
        "interview_copilot.apps.web.privacy_native.ensure_listen_worker",
        lambda rt, base=None: worker,
    )
    assert apply_native_listen_command(runtime, "listen") is True
    import time

    time.sleep(0.08)
    worker.apply_toggle_command.assert_called_with("listen")
    worker.is_manual_listening.return_value = True
    worker.apply_toggle_command.return_value = "idle"
    assert apply_native_listen_command(runtime, "stop_listen") is True
    time.sleep(0.08)
    worker.apply_toggle_command.assert_called_with("stop_listen")
    assert runtime.meta["overlay"]["server_listen"] is True


def test_preferred_engine_follows_focus(client):
    studio = client.post("/api/engines", json={"kind": "studio"}).json()
    live = client.post("/api/engines", json={"kind": "live"}).json()
    focused = client.get(f"/api/engines/{studio['engine_id']}?focus=1")
    assert focused.status_code == 200
    from interview_copilot.apps.web.runtime import get_runtime

    pref = get_runtime().preferred_for_global_hotkeys()
    assert pref is not None
    assert pref.id == studio["engine_id"]
    client.get(f"/api/engines/{live['engine_id']}?focus=1")
    pref = get_runtime().preferred_for_global_hotkeys()
    assert pref.id == live["engine_id"]


def test_status_reports_global_hotkeys(client):
    data = client.get("/api/status").json()
    assert "global_hotkeys" in data
    assert data["global_hotkeys"] is False


def test_studio_window_uses_shared_listen_hotkeys():
    src = Path(__file__).resolve().parents[1] / "apps/studio/window.py"
    text = src.read_text(encoding="utf-8")
    assert "start_global_listen_hotkeys" in text
    assert "toggle_listen" in text
    assert "Stop & Process" in text
    assert 'input_mode != "internal"' in text
    assert "GlobalHotKeys" not in text


def test_web_main_arms_hotkeys_before_uvicorn():
    src = Path(__file__).resolve().parents[1] / "apps/web/server.py"
    text = src.read_text(encoding="utf-8")
    main = text.split("def main")[-1]
    assert "_arm_global_listen_hotkey" in main
    assert "uvicorn.run(" in main
    assert "server:app" not in main
