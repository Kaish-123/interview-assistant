"""Call sessions, library, and answer-preference tests."""

from __future__ import annotations

from pathlib import Path

from interview_copilot.packages.llm.answer_prefs import (
    build_preference_instruction,
    normalize_answer_prefs,
    preview_answer,
)
from interview_copilot.packages.session.call_sessions import (
    CallSessionStore,
    compose_session_extra,
)
from interview_copilot.packages.session.library import LibraryStore


def test_normalize_and_preview():
    prefs = normalize_answer_prefs({"format": "bullets", "question_type": "coding", "bogus": 1})
    assert prefs["format"] == "bullets"
    assert prefs["question_type"] == "coding"
    assert prefs["length"] == "balanced"
    preview = preview_answer(prefs)
    assert "cycle" in preview["answer"].lower() or "pointer" in preview["answer"].lower()
    instr = build_preference_instruction(prefs)
    assert "Coding (LeetCode-style)" in instr
    assert "plain readable text" in instr


def test_call_session_lifecycle(tmp_path: Path):
    store = CallSessionStore(tmp_path / "call_sessions.json")
    created = store.create(
        {
            "kind": "interview",
            "company": "Microsoft",
            "description": "data engineer",
            "auto_answer": False,
        }
    )
    assert created["state"] == "ready"
    assert created["title"] == "Microsoft"
    listed = store.list_public()
    assert listed[0]["id"] == created["id"]
    assert "text" not in listed[0].get("documents", [{}])[0] if listed[0].get("documents") else True

    store.attach_document(created["id"], name="resume.txt", text="Kaish, data engineer", kind="resume")
    store.mark_live(created["id"], engine_id="abc123", connection="real", platform="browser")
    live = store.get(created["id"])
    assert live["state"] == "live"
    assert live["resume"].startswith("Kaish")
    extra = compose_session_extra(live)
    assert "Microsoft" in extra
    assert "ANSWER SHAPE" in extra

    q1 = store.next_mock_question(created["id"])
    q2 = store.next_mock_question(created["id"])
    assert q1 and q2 and q1 != q2
    store.mark_ended(created["id"])
    assert store.get(created["id"])["state"] == "ended"


def test_library_store(tmp_path: Path):
    lib = LibraryStore(tmp_path / "library.json")
    item = lib.add(kind="resume", name="cv.txt", text="hello resume")
    assert item["id"]
    public = lib.list_public(kind="resume")
    assert public[0]["chars"] == 12
    assert "text" not in public[0]
    assert lib.delete(item["id"])
    assert lib.list_public() == []
