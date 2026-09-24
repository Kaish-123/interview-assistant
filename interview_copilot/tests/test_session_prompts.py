"""Phase 1 Milestone 6 — session + prompts JSON contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from interview_copilot.packages.prompts.profiles import SetupProfilesStore
from interview_copilot.packages.prompts.protocol import PromptStore
from interview_copilot.packages.prompts.tabs import PromptTabsStore
from interview_copilot.packages.session.chats import (
    AUTO_SAVE_TITLE,
    ChatHistoryStore,
    prune_sessions,
)
from interview_copilot.packages.session.live_files import (
    new_session_id,
    save_notes,
    save_session,
)
from interview_copilot.packages.session.protocol import SessionStore
from interview_copilot.packages.session.ui_prefs import UIPreferencesStore


def test_chats_autosave_by_title_not_index(tmp_path: Path):
    path = tmp_path / "chats.json"
    store = ChatHistoryStore(path)
    assert isinstance(store, SessionStore)

    store.add_session("Other", [{"role": "user", "content": "x"}])
    store.save_current_session([{"role": "user", "content": "a"}])
    # Reorder: move autosave after other
    store.reorder(0, 1)  # depends on insert order: autosave was insert(0)
    # After add Other then autosave at 0: [AutoSave, Other] if autosave inserted at 0
    # Actually: add_session appends Other first → [Other]
    # save_current inserts AutoSave at 0 → [AutoSave, Other]
    # reorder(0,1): move AutoSave to index 1 → [Other, AutoSave]

    store.save_current_session([{"role": "user", "content": "b"}])
    autos = [s for s in store.sessions if s["title"] == AUTO_SAVE_TITLE]
    assert len(autos) == 1
    assert autos[0]["messages"][0]["content"] == "b"

    # Reload from disk — same contract
    store2 = ChatHistoryStore(path)
    assert store2.find_autosave()["messages"][0]["content"] == "b"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    assert "title" in raw[0] and "messages" in raw[0]


def test_dedupe_autosave_on_load(tmp_path: Path):
    path = tmp_path / "chats.json"
    path.write_text(
        json.dumps(
            [
                {"title": AUTO_SAVE_TITLE, "messages": [{"role": "user", "content": "1"}]},
                {"title": "Real", "messages": []},
                {
                    "title": AUTO_SAVE_TITLE,
                    "messages": [
                        {"role": "user", "content": "1"},
                        {"role": "assistant", "content": "2"},
                    ],
                },
            ]
        ),
        encoding="utf-8",
    )
    store = ChatHistoryStore(path)
    autos = [s for s in store.sessions if s["title"] == AUTO_SAVE_TITLE]
    assert len(autos) == 1
    assert len(autos[0]["messages"]) == 2


def test_bookmarks_and_prune(tmp_path: Path):
    store = ChatHistoryStore(tmp_path / "chats.json")
    store.save_current_session([], bookmarks=[["12.0", "Q1"]])
    for i in range(12):
        store.add_session(f"Chat {i}", [{"role": "user", "content": str(i)}])
    removed = prune_sessions(store, max_chats=10)
    assert removed > 0
    real = [s for s in store.sessions if s["title"] != AUTO_SAVE_TITLE]
    assert len(real) == 1
    assert store.find_autosave() is not None
    assert store.get_session_bookmarks(0) or store.get_session_bookmarks(
        next(i for i, s in enumerate(store.sessions) if s["title"] == AUTO_SAVE_TITLE)
    )


def test_live_session_files(tmp_path: Path):
    sid = new_session_id()
    p = save_session(sid, {"messages": []}, sessions_dir=tmp_path)
    assert p.is_file()
    n = save_notes(sid, "# notes\n", sessions_dir=tmp_path)
    assert n.read_text(encoding="utf-8").startswith("# notes")


def test_tabs_json_contract(tmp_path: Path):
    store = PromptTabsStore(tmp_path / "tabs.json")
    assert isinstance(store, PromptStore)
    t = store.add_tab("Interview")
    s = store.add_subtab(t, "Intro", prompt="Say hello", text_input="Hello there")
    assert store.get_tab_name(t) == "Interview"
    assert store.get_subtab_name(t, s) == "Intro"
    assert store.get_subtab_body(t, s) == "Hello there"
    store.update_subtab_prompt(t, s, "new", text_input="body")
    store2 = PromptTabsStore(tmp_path / "tabs.json")
    raw = json.loads((tmp_path / "tabs.json").read_text(encoding="utf-8"))
    assert "tabs" in raw
    assert raw["tabs"][0]["subTabs"][0]["text_input"] == "body"
    sid = store2.subtab_id(0, 0)
    combined, names = store2.combined_prompt_for_ids([sid])
    assert "body" in combined
    assert names == ["Intro"]


def test_setup_profiles_contract(tmp_path: Path):
    store = SetupProfilesStore(tmp_path / "setup_profiles.json")
    store.upsert("Default", ["sub_0_0", "sub_0_1"])
    store.reorder("Default", ["sub_0_1", "sub_0_0"])
    data = store.load()
    assert data["Default"] == ["sub_0_1", "sub_0_0"]
    assert "Default" in store.list_names()


def test_ui_prefs_merge(tmp_path: Path):
    store = UIPreferencesStore(tmp_path / "ui_prefs.json")
    store.save({"geometry": "100x100"})
    store.set_default_interview_subtabs(["sub_0_0"])
    data = store.load()
    assert data["geometry"] == "100x100"
    assert data["default_interview_subtabs"] == ["sub_0_0"]


def test_core_session_bridge():
    from interview_copilot.core.session import ChatHistoryManager, ChatHistoryStore

    assert ChatHistoryManager is ChatHistoryStore
