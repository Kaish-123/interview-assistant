"""Call-session cards for the web dashboard (create / join / live / ended)."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from interview_copilot.packages.llm.answer_prefs import (
    build_preference_instruction,
    normalize_answer_prefs,
)
from interview_copilot.shared.config.paths import get_paths
from interview_copilot.shared.logging import get_logger

logger = get_logger("session.call_sessions")

KINDS = ("interview", "regular")
CONNECTIONS = ("real", "mock")
PLATFORMS = ("browser", "desktop")
STATES = ("ready", "live", "ended")

MOCK_QUESTIONS = {
    "interview": (
        "Tell me about yourself and how your background fits this role.",
        "Walk me through a recent project you owned end to end.",
        "Tell me about a time you disagreed with a teammate on a technical choice.",
        "How would you design a system that ingests events and serves analytics with a few minutes of delay?",
        "What is the hardest production incident you helped resolve?",
    ),
    "regular": (
        "What is the main goal for this call?",
        "What decision do you want to leave with?",
        "What risks or open questions should we cover first?",
        "What does a successful next step look like after this meeting?",
    ),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def elapsed_seconds(started_at: str | None, ended_at: str | None = None) -> int:
    if not started_at:
        return 0
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at) if ended_at else datetime.now(timezone.utc)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return max(0, int((end - start).total_seconds()))
    except Exception:
        return 0


def _elapsed_seconds(started_at: str | None, ended_at: str | None = None) -> int:
    return elapsed_seconds(started_at, ended_at)


def compose_session_extra(session: dict[str, Any]) -> str:
    parts: list[str] = []
    company = str(session.get("company") or "").strip()
    if company:
        parts.append(f"Company / team: {company}")
    instructions = str(session.get("instructions") or "").strip()
    if instructions:
        parts.append(instructions)
    parts.append(build_preference_instruction(session.get("answer_prefs")))
    kind = session.get("kind") or "interview"
    if kind == "regular":
        parts.append("This is a regular work call, not a formal interview. Keep answers practical and concise.")
    if session.get("connection") == "mock":
        parts.append(
            "This is a practice session. Treat the user's spoken answers as the candidate. "
            "When asked to play interviewer, ask one realistic question at a time."
        )
    return "\n\n".join(parts)


def public_session(session: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(session)
    docs = []
    for doc in out.get("documents") or []:
        text = str(doc.get("text") or "")
        docs.append(
            {
                "name": doc.get("name") or "document",
                "chars": len(text),
                "kind": doc.get("kind") or "document",
            }
        )
    out["documents"] = docs
    out["resume_chars"] = len(str(out.get("resume") or ""))
    out["duration_seconds"] = _elapsed_seconds(out.get("started_at"), out.get("ended_at"))
    return out


class CallSessionStore:
    """JSON list of dashboard call sessions."""

    def __init__(self, file_path: str | Path | None = None):
        self.file_path = Path(file_path) if file_path else get_paths().call_sessions_json
        self.sessions: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if self.file_path.is_file():
            try:
                raw = json.loads(self.file_path.read_text(encoding="utf-8"))
                self.sessions = raw if isinstance(raw, list) else []
            except Exception as e:
                logger.warning(f"call_sessions.json load failed: {e}")
                self.sessions = []
        else:
            self.sessions = []

    def save(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(
            json.dumps(self.sessions, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list_public(self, state: str | None = None) -> list[dict[str, Any]]:
        items = [public_session(s) for s in self.sessions]
        if state and state != "all":
            items = [s for s in items if s.get("state") == state]
        items.sort(key=lambda s: s.get("created_at") or "", reverse=True)
        return items

    def get(self, session_id: str) -> dict[str, Any] | None:
        for s in self.sessions:
            if s.get("id") == session_id:
                return s
        return None

    def create(self, body: dict[str, Any]) -> dict[str, Any]:
        kind = body.get("kind") if body.get("kind") in KINDS else "interview"
        title = str(body.get("title") or body.get("company") or "").strip()
        if not title:
            title = "Interview" if kind == "interview" else "Call"
        session = {
            "id": uuid.uuid4().hex[:12],
            "kind": kind,
            "title": title,
            "company": str(body.get("company") or "").strip(),
            "description": str(body.get("description") or "").strip(),
            "posting_url": str(body.get("posting_url") or "").strip(),
            "connection": "",
            "platform": "",
            "language": str(body.get("language") or "en"),
            "model": str(body.get("model") or ""),
            "auto_answer": bool(body.get("auto_answer")),
            "save_transcript": True if body.get("save_transcript", True) else False,
            "answer_prefs": normalize_answer_prefs(body.get("answer_prefs")),
            "resume": str(body.get("resume") or ""),
            "instructions": str(body.get("instructions") or ""),
            "documents": list(body.get("documents") or []),
            "state": "ready",
            "engine_id": None,
            "created_at": _now(),
            "started_at": None,
            "ended_at": None,
            "mock_index": 0,
            "transcript": [],
        }
        self.sessions.insert(0, session)
        self.save()
        return session

    def update(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        session = self.get(session_id)
        if session is None:
            return None
        allowed = {
            "title",
            "company",
            "description",
            "posting_url",
            "language",
            "model",
            "auto_answer",
            "save_transcript",
            "resume",
            "instructions",
            "kind",
        }
        for key in allowed:
            if key in patch and patch[key] is not None:
                session[key] = patch[key]
        if "answer_prefs" in patch:
            session["answer_prefs"] = normalize_answer_prefs(patch.get("answer_prefs"))
        if patch.get("kind") in KINDS:
            session["kind"] = patch["kind"]
        self.save()
        return session

    def attach_document(
        self,
        session_id: str,
        *,
        name: str,
        text: str,
        kind: str = "document",
    ) -> dict[str, Any] | None:
        session = self.get(session_id)
        if session is None:
            return None
        entry = {"name": name, "text": text, "kind": kind}
        if kind == "resume":
            session["resume"] = text
            session["documents"] = [d for d in session.get("documents") or [] if d.get("kind") != "resume"]
        session.setdefault("documents", []).append(entry)
        self.save()
        return session

    def mark_live(
        self,
        session_id: str,
        *,
        engine_id: str,
        connection: str,
        platform: str,
    ) -> dict[str, Any] | None:
        session = self.get(session_id)
        if session is None:
            return None
        session["engine_id"] = engine_id
        session["connection"] = connection if connection in CONNECTIONS else "real"
        session["platform"] = platform if platform in PLATFORMS else "browser"
        session["state"] = "live"
        session["started_at"] = session.get("started_at") or _now()
        session["ended_at"] = None
        self.save()
        return session

    def mark_ended(self, session_id: str) -> dict[str, Any] | None:
        session = self.get(session_id)
        if session is None:
            return None
        session["state"] = "ended"
        session["ended_at"] = _now()
        self.save()
        return session

    def append_transcript(
        self,
        session_id: str,
        *,
        role: str,
        text: str,
        t: int = 0,
    ) -> dict[str, Any] | None:
        session = self.get(session_id)
        if session is None:
            return None
        session.setdefault("transcript", []).append(
            {"role": role, "text": text, "t": t}
        )
        self.save()
        return session

    def next_mock_question(self, session_id: str) -> str | None:
        session = self.get(session_id)
        if session is None:
            return None
        bucket = MOCK_QUESTIONS["interview" if session.get("kind") == "interview" else "regular"]
        idx = int(session.get("mock_index") or 0)
        question = bucket[idx % len(bucket)]
        session["mock_index"] = idx + 1
        self.save()
        return question
