"""Milestone 7/8 — Studio shell smoke tests (no mainloop)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_studio_window_builds_with_sidebar(monkeypatch):
    pytest.importorskip("tkinter")
    from interview_copilot.shared.config.settings import reload_settings

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    reload_settings()

    fake_engine = MagicMock()
    fake_engine.answer_mode = "default"
    fake_engine.optimization_mode = False
    fake_engine.messages = [{"role": "system", "content": "sys"}]
    fake_engine.model = "gpt-4o-mini"
    fake_engine.toggle_optimization_mode.return_value = True

    prompts = MagicMock()
    prompts.get_tab_count.return_value = 0
    profiles = MagicMock()
    profiles.list_names.return_value = []
    chats = MagicMock()
    chats.find_autosave.return_value = None
    chats.get_titles.return_value = []
    chats.sessions = []
    prefs = MagicMock()
    prefs.get.side_effect = lambda k, default=None: default

    with patch(
        "interview_copilot.apps.studio.window.InterviewLLMEngine",
        return_value=fake_engine,
    ), patch(
        "interview_copilot.apps.studio.window.AudioRecorder",
    ) as rec_cls, patch(
        "interview_copilot.apps.studio.window.ChatHistoryStore",
        return_value=chats,
    ), patch(
        "interview_copilot.apps.studio.window.PromptTabsStore",
        return_value=prompts,
    ), patch(
        "interview_copilot.apps.studio.window.SetupProfilesStore",
        return_value=profiles,
    ), patch(
        "interview_copilot.apps.studio.window.UIPreferencesStore",
        return_value=prefs,
    ), patch(
        "interview_copilot.apps.studio.window.messagebox.showwarning",
    ), patch(
        "interview_copilot.apps.studio.window.StudioWindow._start_global_hotkeys",
    ):
        rec = MagicMock()
        rec.input_mode = "internal"
        rec_cls.return_value = rec

        from interview_copilot.apps.studio.window import StudioWindow

        app = StudioWindow()
        try:
            assert "Studio" in app.title()
            assert app.tab_tree is not None
            assert app.chat_tree is not None
            assert app.bookmarks is not None
            app.toggle_optimization()
            assert "Fast" in app.opt_var.get() or "Full" in app.opt_var.get()
            app.toggle_model()
            app.toggle_mode()
            app.toggle_audio_mode()
            assert rec.input_mode == "external"
        finally:
            app.destroy()


def test_bookmark_controller_add(monkeypatch):
    pytest.importorskip("tkinter")
    import tkinter as tk

    from interview_copilot.apps.studio.bookmarks import BookmarkController

    root = tk.Tk()
    root.withdraw()
    try:
        lb = tk.Listbox(root)
        text = tk.Text(root)
        text.insert("1.0", "QUESTION: Hello world\nANSWER: hi\n")
        text.config(state=tk.DISABLED)
        changed = []

        ctl = BookmarkController(
            lb, text, on_change=lambda: changed.append(1), status=lambda s: None
        )
        ctl.add_at_cursor()
        assert len(ctl.bookmarks) >= 1
        assert changed
        assert ctl.as_persistable()
    finally:
        root.destroy()


def test_engine_optimization_toggle():
    from dataclasses import replace
    from unittest.mock import MagicMock

    from interview_copilot.packages.llm.engine import InterviewLLMEngine
    from interview_copilot.shared.config.settings import build_settings

    settings = replace(build_settings(), openai_api_key="sk-test")
    engine = InterviewLLMEngine(settings=settings, client=MagicMock())
    before = engine.optimization_mode
    assert engine.toggle_optimization_mode() is (not before)
