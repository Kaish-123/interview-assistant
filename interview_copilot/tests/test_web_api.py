"""Smoke tests for web companion API (no OpenAI calls required)."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from interview_copilot.apps.web.server import app


@pytest.fixture()
def client():
    return TestClient(app)


def test_status(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert "api_key_configured" in data
    assert "models" in data
    assert data["platform"] == "web"


def test_create_studio_engine(client):
    r = client.post("/api/engines", json={"kind": "studio"})
    assert r.status_code == 200
    data = r.json()
    assert data["engine_id"]
    assert data["kind"] == "studio"


def test_index_serves_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Interview Copilot" in r.text


def test_app_serves_copilot_shell(client):
    r = client.get("/app")
    assert r.status_code == 200
    assert "view-studio" in r.text
    assert "view-sessions" in r.text
    assert "Create Session" in r.text


def test_call_session_api(client, tmp_path):
    from interview_copilot.apps.web.runtime import get_runtime
    from interview_copilot.packages.session.call_sessions import CallSessionStore
    from interview_copilot.packages.session.library import LibraryStore

    rt = get_runtime()
    rt.call_sessions = CallSessionStore(tmp_path / "call_sessions.json")
    rt.library = LibraryStore(tmp_path / "library.json")

    created = client.post(
        "/api/sessions",
        json={"kind": "interview", "company": "Acme", "description": "Python engineer"},
    )
    assert created.status_code == 200, created.text
    session = created.json()
    assert session["title"] == "Acme"
    assert session["state"] == "ready"

    listed = client.get("/api/sessions").json()
    assert listed["count"] >= 1

    joined = client.post(
        f"/api/sessions/{session['id']}/join",
        json={"connection": "real", "platform": "browser"},
    )
    assert joined.status_code == 200
    data = joined.json()
    assert data["engine_id"]
    assert data["session"]["state"] == "live"
    assert data["session"]["connection"] == "real"

    mock_q = client.post(f"/api/sessions/{session['id']}/mock-question")
    assert mock_q.status_code == 200
    assert "yourself" in mock_q.json()["question"].lower() or "goal" in mock_q.json()["question"].lower()

    preview = client.post("/api/answer-prefs/preview", json={"format": "bullets", "question_type": "behavioral"})
    assert preview.status_code == 200
    assert preview.json()["answer"].startswith("-")

    ended = client.post(f"/api/sessions/{session['id']}/end")
    assert ended.json()["state"] == "ended"


def test_prompts_and_prefs(client):
    assert client.get("/api/prompts").status_code == 200
    assert client.get("/api/prefs").status_code == 200
    assert client.get("/api/chats").status_code == 200
    assert client.get("/api/profiles").status_code == 200


def test_audio_status(client):
    r = client.get("/api/audio/status")
    assert r.status_code == 200
    data = r.json()
    assert "setup" in data
    assert "backend" in data
    assert "loopback_ready" in data
    assert data["platform"] in {"macos", "windows", "linux"}


def test_app_has_meeting_audio_grant(client):
    html = client.get("/app").text
    assert "btn-grant-audio" in html
    assert "audio.js" in html
    assert "Allow microphone" in html
    assert 'value="mic" selected' in html
    assert "sessions.js" in html
    assert "btn-create-session" in html
    assert "live-wave" in html
    assert "btn-live-answer" in html


def test_real_session_uses_same_mic_path_as_mock():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    app_js = (root / "apps/web/static/js/app.js").read_text(encoding="utf-8")
    audio_js = (root / "apps/web/static/js/audio.js").read_text(encoding="utf-8")
    assert 'value = connection === "mock" ? "mic" : "call"' not in app_js
    assert "acquireMic({ loopbackFirst: true })" in app_js
    assert "connection === \"real\" || joined.auto_answer" not in app_js
    assert "if (joined.auto_answer) await startLiveAuto()" in app_js
    assert "return this.acquireMic({ loopbackFirst: true })" in audio_js
    assert "echoCancellation: false" in audio_js
    assert "endSilenceMs: 2200" in app_js
    assert "prefetchEveryMs: 2000" in app_js
    assert "coalesceTranscript" in app_js
    assert "scheduleAnswerCommit" in app_js
    assert "questionReadyToAnswer" in app_js
    assert "cancelPrematureAnswer" in app_js
    assert "prefetchAnswer(" not in app_js
    assert "draft: true" not in app_js
    assert "snapshot(" in audio_js
    assert "silent >= endSilenceMs" in audio_js
    assert "_questionOpen" in audio_js
    assert "QuestionText" in app_js
    assert "ingestUtterance" in app_js
    assert "Hearing question…" in app_js


def test_live_captions_are_near_realtime():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    app_js = (root / "apps/web/static/js/app.js").read_text(encoding="utf-8")
    audio_js = (root / "apps/web/static/js/audio.js").read_text(encoding="utf-8")
    html = (root / "apps/web/static/index.html").read_text(encoding="utf-8")
    css = (root / "apps/web/static/css/app.css").read_text(encoding="utf-8")
    assert "interimResults = true" in audio_js
    assert "snapshotPcmWav" in audio_js
    assert "encodeWavPcm" in audio_js
    assert "LiveCaptioner" in audio_js
    assert "prefetchEveryMs || 2000" in audio_js
    assert "prefetchEveryMs: 2000" in app_js
    assert "showLiveCaption" in app_js
    assert "LEFT_CAPTION_IDLE" in app_js
    assert "live && cleaned" in app_js
    assert "live: !commit" in app_js
    assert "Live captions are preview only" in app_js
    assert "Full-buffer snapshot" in app_js
    assert "queuedUtterance" in app_js
    assert "upsertInterviewer(text, { commit: true })" in app_js
    assert "startBrowserCaptions" in app_js
    assert "applyBrowserCaption" in app_js
    assert "collapseSnowball" in app_js
    assert "collapseCaptionResults" in audio_js
    assert "_finalAcc" not in audio_js
    assert "text += ev.results" not in audio_js
    assert "setLiveAnswer" in app_js
    assert "shouldApplyAnswer" in app_js
    assert "resetUtterance" in audio_js
    assert "ev.resultIndex" in audio_js
    assert "live-caption-text" in html
    assert "live-transcript-body" in html
    assert "live-log" in html
    assert "live-room-single" in html
    assert "live-hearing" in html
    assert "Captions appear as the interviewer speaks" in html
    assert "caption-caret" in css
    assert "qa-block" in css
    assert "renderLiveLog" in app_js
    assert "stopLiveListenAndAnswer" in app_js
    assert "autoAnswer: true, force: true" in app_js
    assert "routeListenToggle" in app_js
    assert 'live.wav' in app_js
    assert "LiveTranscribeSocket" in audio_js
    assert "startLiveStt" in app_js
    assert "if (state.liveSttOk) return" in app_js
    assert "/api/stt/live" in audio_js
    assert "async startHold()" in audio_js
    assert "await state.mic.startHold()" in app_js
    assert "await state.liveMic.startHold()" in app_js
    assert "startLiveCaptureLoop" in app_js
    assert "startLiveVadLoop" in app_js
    assert "resumeAuto" not in app_js
    assert "function applyLiveCompleted" in app_js
    apply_src = app_js.split("function applyLiveCompleted")[1].split("function startLiveStt")[0]
    assert "finalizeAssembled" not in apply_src
    stop_src = app_js.split("async function stopLiveListenAndAnswer")[1].split("function stopLiveStt")[0]
    assert "startLiveCaptureLoop" not in stop_src
    assert "container.scrollTop = container.scrollHeight" in app_js
    assert "blocks.push({ kind: \"q\"" in app_js
    assert "startCaptionTap" in audio_js
    assert "pollStudioAfterListen" in app_js
    assert "startDisplayCaptions" in app_js
    assert "startStudioListenCaptions" in app_js
    assert "syncLiveState({ transcript:" in app_js
    assert "lastQ.body.trim() === liveQ" in app_js
    assert "startLiveLogTimer" not in app_js
    assert ", 200);" in app_js
    assert "function ingestQuestion" in app_js
    assert "function flushQuestionWords" in app_js
    assert "function snapQuestion" in app_js
    assert "function resetQuestionType" in app_js
    assert "Q.nextWordChunk" in app_js
    assert "setInterval(flushQuestionWords, 42)" in app_js


def test_stt_live_websocket_route_registered():
    paths = [getattr(r, "path", None) for r in app.routes]
    assert "/api/stt/live" in paths


def test_dashboard_and_live_layout_fill_the_pane():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    css = (root / "apps/web/static/css/app.css").read_text(encoding="utf-8")
    html = (root / "apps/web/static/index.html").read_text(encoding="utf-8")
    assert "#app.app-shell" in css
    assert "flex-direction: row" in css
    assert 'body[data-mode="sessions"] .mode-tabs' in css
    assert "height: 52px" in css
    assert ".live-stage.has-room .live-answer" in css
    assert "max-height: none" in css
    assert "question.js" in html
    assert 'id="live-wave" width="640" height="56"' in html
    assert "live-qna-foot" in html
    assert "live-room-single" in html
    assert "live-hearing" in css


def test_chat_commit_persists_without_llm(client):
    eid = client.post("/api/engines", json={"kind": "live"}).json()["engine_id"]
    r = client.post(
        "/api/chat/commit",
        json={"engine_id": eid, "text": "What is REST?", "answer": "Representational state transfer."},
    )
    assert r.status_code == 200
    snap = client.get(f"/api/engines/{eid}").json()
    roles = [(m["role"], m["content"]) for m in snap["messages"] if m["role"] in {"user", "assistant"}]
    assert ("user", "What is REST?") in roles
    assert ("assistant", "Representational state transfer.") in roles


def test_listen_duplicate_helper():
    from interview_copilot.apps.web.routers import _is_duplicate_answered_turn, _remember_turn, _similar_utterance

    assert _similar_utterance("what is REST", "what is REST")
    assert _similar_utterance("what is REST", "what is REST architecture")
    assert not _similar_utterance("alpha", "beta")

    class _RT:
        meta = {}

    rt = _RT()
    assert _is_duplicate_answered_turn(rt, "What is TCP?") is False
    _remember_turn(rt, "What is TCP?", answered=True)
    assert _is_duplicate_answered_turn(rt, "What is TCP?") is True
    _remember_turn(rt, "What is TCP?", answered=False)
    assert _is_duplicate_answered_turn(rt, "What is TCP?") is False
