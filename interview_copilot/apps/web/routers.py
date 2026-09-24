"""FastAPI routers for Interview Copilot web companion."""

from __future__ import annotations

import asyncio
import io
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from PIL import Image

from interview_copilot.apps.web.privacy_native import (
    apply_native_listen_command,
    refresh_overlay_liveness,
    spawn_native_overlay,
    stop_native_overlay,
)
from interview_copilot.apps.web.runtime import get_runtime
from interview_copilot.packages.context import load_document
from interview_copilot.packages.audio.devices import loopback_status
from interview_copilot.packages.llm.answer_modes import label_answer_mode
from interview_copilot.packages.llm.answer_prefs import (
    describe_prefs,
    normalize_answer_prefs,
    preview_answer,
)
from interview_copilot.packages.session import live_files as live_files
from interview_copilot.packages.session.call_sessions import (
    CONNECTIONS,
    PLATFORMS,
    compose_session_extra,
    elapsed_seconds,
    public_session,
)
from interview_copilot.packages.session.chats import AUTO_SAVE_TITLE
from interview_copilot.packages.stt.question_text import collapse_snowball
from interview_copilot.shared.config.paths import get_paths

router = APIRouter(prefix="/api")


# ── models ──────────────────────────────────────────────────────────


class CreateEngineRequest(BaseModel):
    kind: str = "studio"
    model: Optional[str] = None
    language: str = "en"
    resume: str = ""
    job_description: str = ""
    extra: str = ""


class ChatRequest(BaseModel):
    engine_id: str
    text: str
    image_data_urls: list[str] = Field(default_factory=list)
    temperature: float = 0.4
    draft: bool = False


class CommitQARequest(BaseModel):
    engine_id: str
    text: str
    answer: str = ""


class ContextRequest(BaseModel):
    engine_id: str
    resume: str = ""
    job_description: str = ""
    extra: str = ""


class ModeRequest(BaseModel):
    engine_id: str
    answer_mode: Optional[str] = None
    optimization_mode: Optional[bool] = None
    model: Optional[str] = None
    language: Optional[str] = None


class BookmarkRequest(BaseModel):
    engine_id: str
    line_index: int
    preview: str = ""


class ChatIndexRequest(BaseModel):
    engine_id: str
    index: int


class RenameChatRequest(BaseModel):
    index: int
    title: str


class SaveNamedChatRequest(BaseModel):
    engine_id: str
    title: str


class TabCreate(BaseModel):
    name: str


class SubtabCreate(BaseModel):
    tab_index: int
    name: str
    prompt: str = ""
    text_input: str = ""


class SubtabUpdate(BaseModel):
    tab_index: int
    subtab_index: int
    prompt: str = ""
    text_input: str = ""


class ProfileUpsert(BaseModel):
    name: str
    subtab_ids: list[str]


class DefaultInterviewRequest(BaseModel):
    subtab_ids: list[str]


class PrefsPatch(BaseModel):
    data: dict[str, Any]


class NotesRequest(BaseModel):
    engine_id: str
    session_id: Optional[str] = None


class LiveSaveRequest(BaseModel):
    engine_id: str
    session_id: Optional[str] = None


class EngineIdBody(BaseModel):
    engine_id: str


class PrivacyCommandRequest(BaseModel):
    engine_id: str
    command: str


class PrivacyStateRequest(BaseModel):
    engine_id: str
    listening: Optional[bool] = None
    auto: Optional[bool] = None
    transcript: Optional[str] = None
    answer: Optional[str] = None
    status: Optional[str] = None


class CreateCallSessionRequest(BaseModel):
    kind: str = "interview"
    title: str = ""
    company: str = ""
    description: str = ""
    posting_url: str = ""
    language: str = "en"
    model: Optional[str] = None
    auto_answer: bool = False
    save_transcript: bool = True
    resume: str = ""
    instructions: str = ""
    answer_prefs: dict[str, Any] = Field(default_factory=dict)


class JoinSessionRequest(BaseModel):
    connection: str = "real"
    platform: str = "browser"


class AnswerPrefsRequest(BaseModel):
    format: Optional[str] = None
    length: Optional[str] = None
    tone: Optional[str] = None
    question_type: Optional[str] = None
    star: Optional[bool] = None
    filler_words: Optional[bool] = None


class TranscriptLineRequest(BaseModel):
    role: str
    text: str
    t: int = 0


class LibraryCreateRequest(BaseModel):
    kind: str = "document"
    name: str
    text: str = ""


# ── helpers ─────────────────────────────────────────────────────────


def _engine_or_404(engine_id: str):
    try:
        return get_runtime().get(engine_id)
    except KeyError as e:
        raise HTTPException(404, f"Unknown engine_id: {engine_id}") from e


def _serialize_messages(messages: list[dict]) -> list[dict]:
    out = []
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if isinstance(content, list):
            texts = []
            images = 0
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    texts.append(part.get("text", ""))
                elif isinstance(part, dict) and part.get("type") == "image_url":
                    images += 1
            content = ("\n".join(texts) + (f"\n[{images} image(s)]" if images else "")).strip()
        out.append({"role": role, "content": content if isinstance(content, str) else str(content)})
    return out


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _last_role(messages: list[dict], role: str) -> str:
    for m in reversed(messages):
        if m.get("role") == role and m.get("content"):
            return str(m["content"])
    return ""


def _stream_deltas(runtime, deltas):
    acc: list[str] = []
    runtime.partial = ""
    try:
        for delta in deltas:
            acc.append(delta)
            runtime.partial = "".join(acc)
            yield delta
    finally:
        runtime.partial = ""


def _user_content(text: str, image_data_urls: list[str]) -> Any:
    if not image_data_urls:
        return text
    parts: list[dict] = [{"type": "text", "text": text or "Analyze the attached image(s)."}]
    for url in image_data_urls:
        parts.append({"type": "image_url", "image_url": {"url": url}})
    return parts


# ── status / engines ────────────────────────────────────────────────


@router.get("/status")
def status():
    return get_runtime().status()


@router.get("/audio/status")
def audio_capture_status():
    return loopback_status()


@router.post("/engines")
def create_engine(body: CreateEngineRequest):
    rt = get_runtime()
    runtime = rt.create_engine(
        kind=body.kind,
        model=body.model,
        language=body.language,
        resume=body.resume,
        job_description=body.job_description,
        extra=body.extra,
    )
    # Restore AutoSave into studio by default
    if body.kind == "studio":
        auto = rt.chats.find_autosave()
        if auto:
            runtime.engine.messages = list(auto.get("messages") or [])
            runtime.bookmarks = list(auto.get("bookmarks") or [])
            runtime.title = AUTO_SAVE_TITLE
    return {
        "engine_id": runtime.id,
        "kind": runtime.kind,
        "model": runtime.engine.model,
        "answer_mode": runtime.engine.answer_mode,
        "optimization_mode": runtime.engine.optimization_mode,
        "language": runtime.engine.language,
        "messages": _serialize_messages(runtime.engine.messages),
        "bookmarks": runtime.bookmarks,
    }


@router.get("/engines/{engine_id}")
def get_engine(engine_id: str, focus: bool = False):
    runtime = _engine_or_404(engine_id)
    if focus:
        get_runtime().set_hotkey_target(engine_id)
    refresh_overlay_liveness(runtime)
    eng = runtime.engine
    messages = _serialize_messages(eng.messages)
    overlay = runtime.meta.get("overlay") or {}
    last_question = (
        str(overlay.get("transcript") or "").strip()
        or _last_role(messages, "user")
    )
    last_answer = (
        str(overlay.get("answer") or "").strip()
        or runtime.partial
        or _last_role(messages, "assistant")
    )
    return {
        "engine_id": runtime.id,
        "kind": runtime.kind,
        "model": eng.model,
        "answer_mode": eng.answer_mode,
        "answer_mode_label": label_answer_mode(eng.answer_mode),
        "optimization_mode": eng.optimization_mode,
        "language": eng.language,
        "messages": messages,
        "bookmarks": runtime.bookmarks,
        "title": runtime.title,
        "meta": runtime.meta,
        "partial": runtime.partial,
        "last_question": last_question,
        "last_answer": last_answer,
    }


@router.patch("/engines/{engine_id}/mode")
def patch_mode(engine_id: str, body: ModeRequest):
    runtime = _engine_or_404(engine_id)
    eng = runtime.engine
    if body.answer_mode:
        if body.answer_mode not in ("default", "quick", "detailed", "code"):
            raise HTTPException(400, "Invalid answer_mode")
        eng.answer_mode = body.answer_mode  # type: ignore[assignment]
    if body.optimization_mode is not None:
        eng.optimization_mode = body.optimization_mode
    if body.model:
        eng.model = body.model
    if body.language is not None:
        eng.language = body.language
    return {
        "model": eng.model,
        "answer_mode": eng.answer_mode,
        "optimization_mode": eng.optimization_mode,
        "language": eng.language,
    }


@router.post("/engines/{engine_id}/cycle-answer-mode")
def cycle_answer_mode(engine_id: str):
    runtime = _engine_or_404(engine_id)
    mode = runtime.engine.cycle_answer_mode()
    return {"answer_mode": mode, "label": label_answer_mode(mode)}


@router.post("/engines/{engine_id}/toggle-fast")
def toggle_fast(engine_id: str):
    runtime = _engine_or_404(engine_id)
    on = runtime.engine.toggle_optimization_mode()
    return {"optimization_mode": on, "label": "Fast" if on else "Full"}


@router.post("/engines/{engine_id}/cancel")
def cancel_stream(engine_id: str):
    runtime = _engine_or_404(engine_id)
    runtime.engine.cancel()
    return {"ok": True}


@router.post("/engines/{engine_id}/clear")
def clear_chat(engine_id: str):
    runtime = _engine_or_404(engine_id)
    rt = get_runtime()
    runtime.engine.store.reset(rt.settings.system_prompt)
    runtime.bookmarks = []
    rt.autosave(runtime)
    return {"ok": True, "messages": []}


# ── chat streaming ──────────────────────────────────────────────────


@router.post("/chat/stream")
def chat_stream(body: ChatRequest):
    runtime = _engine_or_404(body.engine_id)
    if not body.text.strip() and not body.image_data_urls:
        raise HTTPException(400, "Empty message")

    content = _user_content(body.text.strip(), body.image_data_urls)
    plain = body.text.strip()

    def gen():
        if plain and not body.image_data_urls and _is_duplicate_answered_turn(runtime, plain):
            yield _sse({"type": "done", "skipped": True, "duplicate": True, "messages": _serialize_messages(runtime.engine.messages)})
            return
        yield _sse({"type": "start", "role": "assistant"})
        try:
            with runtime.lock:
                stream = runtime.engine.stream_answer(
                    content,
                    temperature=body.temperature,
                    persist=not body.draft,
                )
                for delta in _stream_deltas(runtime, stream):
                    yield _sse({"type": "delta", "text": delta})
            if plain and not body.draft:
                _remember_turn(runtime, plain, answered=True)
            get_runtime().autosave(runtime)
            yield _sse(
                {
                    "type": "done",
                    "messages": _serialize_messages(runtime.engine.messages),
                }
            )
        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/chat/commit")
def commit_qa(body: CommitQARequest):
    runtime = _engine_or_404(body.engine_id)
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "Empty message")
    with runtime.lock:
        runtime.engine.store.append_user(text)
        if body.answer.strip():
            runtime.engine.store.append_assistant(body.answer.strip())
    get_runtime().autosave(runtime)
    return {"ok": True, "messages": _serialize_messages(runtime.engine.messages)}


# ── audio / STT ─────────────────────────────────────────────────────


@router.post("/stt")
async def transcribe_audio(
    engine_id: str = Form(...),
    auto_answer: bool = Form(False),
    prompt: str = Form(""),
    file: UploadFile = File(...),
):
    runtime = _engine_or_404(engine_id)
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Empty audio")

    tmp_dir = get_paths().data_dir / "tmp_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=tmp_dir) as tmp:
        tmp.write(raw)
        path = tmp.name

    try:
        hint = (prompt or "").strip() or None
        text = await asyncio.to_thread(runtime.engine.transcribe, path, hint)
    finally:
        Path(path).unlink(missing_ok=True)

    text = collapse_snowball((text or "").strip())
    is_q = runtime.engine.looks_like_question(text) if text else False
    return {
        "text": text,
        "looks_like_question": is_q,
        "auto_answer": auto_answer and is_q and bool(text),
    }


def _similar_utterance(a: str, b: str) -> bool:
    x, y = a.strip().lower(), b.strip().lower()
    if not x or not y:
        return False
    if x == y:
        return True
    return x in y or y in x


def _remember_turn(runtime, text: str, *, answered: bool) -> None:
    runtime.meta["last_listen"] = {
        "text": (text or "").strip(),
        "ts": time.time(),
        "answered": bool(answered),
    }


def _is_duplicate_answered_turn(runtime, text: str, window_s: float = 14.0) -> bool:
    prev = runtime.meta.get("last_listen") or {}
    if not prev.get("answered"):
        return False
    if not _similar_utterance(text or "", str(prev.get("text") or "")):
        return False
    return (time.time() - float(prev.get("ts") or 0)) < window_s


@router.post("/listen/stream")
async def listen_and_answer(
    engine_id: str = Form(...),
    file: UploadFile = File(...),
    force: bool = Form(False),
):
    """Transcribe uploaded clip; if question (or force), stream an answer."""
    runtime = _engine_or_404(engine_id)
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    raw = await file.read()
    tmp_dir = get_paths().data_dir / "tmp_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=tmp_dir) as tmp:
        tmp.write(raw)
        path = tmp.name

    try:
        raw = await asyncio.to_thread(runtime.engine.transcribe, path)
        text = collapse_snowball((raw or "").strip())
    finally:
        Path(path).unlink(missing_ok=True)

    if not text:
        return StreamingResponse(
            iter([_sse({"type": "error", "message": "No speech detected"})]),
            media_type="text/event-stream",
        )

    prev = runtime.meta.get("last_listen") or {}
    if _is_duplicate_answered_turn(runtime, text):
        def skip():
            yield _sse({"type": "transcript", "text": text, "looks_like_question": True, "duplicate": True})
            yield _sse({"type": "done", "skipped": True, "duplicate": True, "messages": _serialize_messages(runtime.engine.messages)})

        return StreamingResponse(skip(), media_type="text/event-stream")
    if (
        not force
        and _similar_utterance(text, str(prev.get("text") or ""))
        and (time.time() - float(prev.get("ts") or 0)) < 14
    ):
        def skip_recent():
            yield _sse({"type": "transcript", "text": text, "looks_like_question": True, "duplicate": True})
            yield _sse({"type": "done", "skipped": True, "duplicate": True, "messages": _serialize_messages(runtime.engine.messages)})

        return StreamingResponse(skip_recent(), media_type="text/event-stream")

    _remember_turn(runtime, text, answered=False)
    is_q = force or runtime.engine.looks_like_question(text)
    overlay = runtime.meta.setdefault("overlay", {})
    overlay["transcript"] = text
    overlay["answer"] = ""
    overlay["status"] = "Answering…" if is_q else "Heard speech"

    def gen():
        yield _sse({"type": "transcript", "text": text, "looks_like_question": is_q})
        if not is_q:
            yield _sse({"type": "done", "skipped": True, "messages": _serialize_messages(runtime.engine.messages)})
            return
        yield _sse({"type": "start", "role": "assistant"})
        acc: list[str] = []
        try:
            with runtime.lock:
                for delta in _stream_deltas(runtime, runtime.engine.stream_answer(text)):
                    acc.append(delta)
                    overlay["answer"] = "".join(acc)
                    overlay["status"] = "Writing answer…"
                    yield _sse({"type": "delta", "text": delta})
            _remember_turn(runtime, text, answered=True)
            overlay["status"] = "Ready"
            get_runtime().autosave(runtime)
            yield _sse(
                {
                    "type": "done",
                    "messages": _serialize_messages(runtime.engine.messages),
                }
            )
        except Exception as e:
            overlay["status"] = str(e)[:80]
            yield _sse({"type": "error", "message": str(e)})

    return StreamingResponse(gen(), media_type="text/event-stream")


# ── documents / screen ──────────────────────────────────────────────


@router.post("/context")
def set_context(body: ContextRequest):
    runtime = _engine_or_404(body.engine_id)
    runtime.engine.set_context(
        resume=body.resume,
        job_description=body.job_description,
        extra=body.extra,
    )
    runtime.meta.update(
        {
            "resume": body.resume[:200],
            "job_description": body.job_description[:200],
            "extra": body.extra[:200],
        }
    )
    return {"ok": True}


@router.post("/documents/upload")
async def upload_document(
    engine_id: str = Form(...),
    file: UploadFile = File(...),
):
    runtime = _engine_or_404(engine_id)
    name = file.filename or "upload.bin"
    raw = await file.read()
    tmp_dir = get_paths().data_dir / "tmp_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / name
    dest.write_bytes(raw)
    try:
        result = load_document(str(dest))
        if result.ok:
            runtime.engine.store.append_system_document(result.name, result.text)
        return {
            "ok": result.ok,
            "name": result.name,
            "message": result.message,
            "chars": len(result.text or ""),
        }
    finally:
        dest.unlink(missing_ok=True)


@router.post("/screen/analyze")
async def analyze_screen(
    engine_id: str = Form(...),
    file: UploadFile = File(...),
):
    runtime = _engine_or_404(engine_id)
    raw = await file.read()
    try:
        img = Image.open(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(400, f"Invalid image: {e}") from e

    def gen():
        yield _sse({"type": "start", "role": "assistant"})
        try:
            with runtime.lock:
                for delta in _stream_deltas(runtime, runtime.engine.analyze_screenshot(img)):
                    yield _sse({"type": "delta", "text": delta})
            get_runtime().autosave(runtime)
            yield _sse(
                {
                    "type": "done",
                    "messages": _serialize_messages(runtime.engine.messages),
                }
            )
        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})

    return StreamingResponse(gen(), media_type="text/event-stream")


# ── chats ───────────────────────────────────────────────────────────


@router.get("/chats")
def list_chats():
    rt = get_runtime()
    sessions = []
    for i, s in enumerate(rt.chats.sessions):
        sessions.append(
            {
                "index": i,
                "title": s.get("title", "Untitled"),
                "message_count": len(s.get("messages") or []),
                "bookmark_count": len(s.get("bookmarks") or []),
                "is_autosave": s.get("title") == AUTO_SAVE_TITLE,
            }
        )
    return {"sessions": sessions}


@router.post("/chats/load")
def load_chat(body: ChatIndexRequest):
    runtime = _engine_or_404(body.engine_id)
    rt = get_runtime()
    msgs = rt.chats.get_session(body.index)
    bookmarks = rt.chats.get_session_bookmarks(body.index)
    titles = rt.chats.get_titles()
    if not (0 <= body.index < len(titles)):
        raise HTTPException(404, "Chat not found")
    runtime.engine.messages = msgs
    runtime.bookmarks = bookmarks
    runtime.chat_index = body.index
    runtime.title = titles[body.index]
    return {
        "title": runtime.title,
        "messages": _serialize_messages(msgs),
        "bookmarks": bookmarks,
    }


@router.post("/chats/save-named")
def save_named(body: SaveNamedChatRequest):
    runtime = _engine_or_404(body.engine_id)
    rt = get_runtime()
    idx = rt.chats.add_session(
        body.title.strip() or "Saved Chat",
        runtime.engine.messages,
        bookmarks=runtime.bookmarks,
    )
    runtime.chat_index = idx
    runtime.title = body.title.strip()
    return {"index": idx, "title": runtime.title}


@router.post("/chats/rename")
def rename_chat(body: RenameChatRequest):
    ok = get_runtime().chats.rename_session(body.index, body.title)
    if not ok:
        raise HTTPException(400, "Rename failed")
    return {"ok": True}


@router.delete("/chats/{index}")
def delete_chat(index: int):
    rt = get_runtime()
    if not (0 <= index < len(rt.chats.sessions)):
        raise HTTPException(404, "Chat not found")
    if rt.chats.sessions[index].get("title") == AUTO_SAVE_TITLE:
        raise HTTPException(400, "Cannot delete AutoSave")
    del rt.chats.sessions[index]
    rt.chats.save()
    return {"ok": True}


@router.post("/bookmarks")
def add_bookmark(body: BookmarkRequest):
    runtime = _engine_or_404(body.engine_id)
    preview = body.preview or f"Line {body.line_index}"
    runtime.bookmarks.append([body.line_index, preview[:120]])
    get_runtime().autosave(runtime)
    return {"bookmarks": runtime.bookmarks}


@router.delete("/bookmarks/{engine_id}/{bookmark_index}")
def delete_bookmark(engine_id: str, bookmark_index: int):
    runtime = _engine_or_404(engine_id)
    if 0 <= bookmark_index < len(runtime.bookmarks):
        runtime.bookmarks.pop(bookmark_index)
        get_runtime().autosave(runtime)
    return {"bookmarks": runtime.bookmarks}


# ── prompts / profiles ──────────────────────────────────────────────


@router.get("/prompts")
def get_prompts():
    return get_runtime().tabs.data


@router.post("/prompts/tabs")
def add_tab(body: TabCreate):
    idx = get_runtime().tabs.add_tab(body.name.strip() or "Tab")
    return {"index": idx, "tabs": get_runtime().tabs.data}


@router.post("/prompts/subtabs")
def add_subtab(body: SubtabCreate):
    idx = get_runtime().tabs.add_subtab(
        body.tab_index,
        body.name.strip() or "Prompt",
        prompt=body.prompt,
        text_input=body.text_input,
    )
    if idx < 0:
        raise HTTPException(400, "Invalid tab")
    return {"index": idx, "tabs": get_runtime().tabs.data}


@router.patch("/prompts/subtabs")
def update_subtab(body: SubtabUpdate):
    ok = get_runtime().tabs.update_subtab_prompt(
        body.tab_index,
        body.subtab_index,
        body.prompt,
        body.text_input,
    )
    if not ok:
        raise HTTPException(400, "Invalid subtab")
    return {"tabs": get_runtime().tabs.data}


@router.get("/prompts/subtab-body")
def subtab_body(tab_index: int, subtab_index: int):
    tabs = get_runtime().tabs
    return {
        "id": tabs.subtab_id(tab_index, subtab_index),
        "name": tabs.get_subtab_name(tab_index, subtab_index),
        "body": tabs.get_subtab_body(tab_index, subtab_index),
    }


@router.get("/profiles")
def list_profiles():
    rt = get_runtime()
    return {"profiles": rt.profiles.load(), "names": rt.profiles.list_names()}


@router.post("/profiles")
def upsert_profile(body: ProfileUpsert):
    get_runtime().profiles.upsert(body.name.strip(), body.subtab_ids)
    return {"profiles": get_runtime().profiles.load()}


@router.delete("/profiles/{name}")
def delete_profile(name: str):
    ok = get_runtime().profiles.delete(name)
    if not ok:
        raise HTTPException(404, "Profile not found")
    return {"ok": True}


@router.get("/default-interview")
def get_default_interview():
    ids = get_runtime().prefs.get("default_interview_subtabs", []) or []
    return {"subtab_ids": ids}


@router.put("/default-interview")
def set_default_interview(body: DefaultInterviewRequest):
    get_runtime().prefs.set_default_interview_subtabs(body.subtab_ids)
    return {"subtab_ids": body.subtab_ids}


@router.post("/default-interview/bodies")
def default_interview_bodies():
    """Ordered prompt bodies for default interview (Intro first)."""
    rt = get_runtime()
    ids = list(rt.prefs.get("default_interview_subtabs", []) or [])
    items = []
    for sid in ids:
        resolved = rt.tabs.resolve_subtab_id(sid)
        if not resolved:
            continue
        t, s = resolved
        name = rt.tabs.get_subtab_name(t, s)
        body = rt.tabs.get_subtab_body(t, s)
        items.append({"id": sid, "name": name, "body": body})
    # Intro first
    items.sort(key=lambda x: (0 if (x["name"] or "").strip().lower() == "intro" else 1))
    return {"items": items}


# ── prefs / live notes ──────────────────────────────────────────────


@router.get("/prefs")
def get_prefs():
    return get_runtime().prefs.load()


@router.patch("/prefs")
def patch_prefs(body: PrefsPatch):
    get_runtime().prefs.save(body.data)
    return get_runtime().prefs.load()


@router.post("/live/notes")
def generate_notes(body: NotesRequest):
    runtime = _engine_or_404(body.engine_id)
    notes = runtime.engine.generate_notes()
    sid = body.session_id or live_files.new_session_id()
    path = live_files.save_notes(sid, notes)
    return {"session_id": sid, "notes": notes, "path": str(path)}


@router.post("/live/save")
def save_live_session(body: LiveSaveRequest):
    runtime = _engine_or_404(body.engine_id)
    sid = body.session_id or live_files.new_session_id()
    path = live_files.save_session(
        sid,
        {
            "kind": "live",
            "model": runtime.engine.model,
            "language": runtime.engine.language,
            "messages": runtime.engine.messages,
            "meta": runtime.meta,
        },
    )
    get_runtime().autosave(runtime)
    return {"session_id": sid, "path": str(path)}


@router.get("/live/sessions")
def list_live_sessions():
    root = get_paths().sessions_dir
    files = sorted(root.glob("session_*.json"), reverse=True)
    out = []
    for f in files[:30]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out.append(
                {
                    "id": data.get("id") or f.stem.replace("session_", ""),
                    "saved_at": data.get("saved_at"),
                    "message_count": len(data.get("messages") or []),
                }
            )
        except Exception:
            continue
    return {"sessions": out}


# ── call sessions / library / answer prefs ───────────────────────────


def _session_or_404(session_id: str):
    session = get_runtime().call_sessions.get(session_id)
    if session is None:
        raise HTTPException(404, "Session not found")
    return session


def _apply_session_to_engine(runtime, session: dict[str, Any]) -> None:
    extra = compose_session_extra(session)
    keep = [m for m in runtime.engine.messages if m.get("role") != "system"]
    runtime.engine.set_context(
        resume=str(session.get("resume") or ""),
        job_description=str(session.get("description") or ""),
        extra=extra,
    )
    if session.get("model"):
        runtime.engine.model = session["model"]
    if session.get("language"):
        runtime.engine.language = session["language"]
    for doc in session.get("documents") or []:
        name = str(doc.get("name") or "document")
        text = str(doc.get("text") or "")
        if text and doc.get("kind") != "resume":
            runtime.engine.store.append_system_document(name, text)
    runtime.engine.messages.extend(keep)
    runtime.meta["session_id"] = session.get("id")
    runtime.meta["connection"] = session.get("connection")
    runtime.title = session.get("title") or runtime.title


@router.get("/answer-prefs")
def get_answer_prefs():
    return describe_prefs()


@router.post("/answer-prefs/preview")
def post_answer_prefs_preview(body: AnswerPrefsRequest):
    return preview_answer(body.model_dump())


@router.get("/sessions")
def list_call_sessions(state: str = "all"):
    items = get_runtime().call_sessions.list_public(state=state)
    live = any(s.get("state") == "live" for s in items)
    return {"sessions": items, "live": live, "count": len(items)}


@router.post("/sessions")
def create_call_session(body: CreateCallSessionRequest):
    rt = get_runtime()
    payload = body.model_dump()
    payload["answer_prefs"] = normalize_answer_prefs(payload.get("answer_prefs"))
    if not payload.get("model"):
        payload["model"] = rt.settings.llm.default_model
    session = rt.call_sessions.create(payload)
    return public_session(session)


@router.get("/sessions/{session_id}")
def get_call_session(session_id: str):
    return public_session(_session_or_404(session_id))


@router.patch("/sessions/{session_id}")
def patch_call_session(session_id: str, body: CreateCallSessionRequest):
    session = get_runtime().call_sessions.update(session_id, body.model_dump(exclude_unset=True))
    if session is None:
        raise HTTPException(404, "Session not found")
    if session.get("engine_id"):
        try:
            runtime = get_runtime().get(session["engine_id"])
            _apply_session_to_engine(runtime, session)
        except KeyError:
            pass
    return public_session(session)


@router.patch("/sessions/{session_id}/answer-prefs")
def patch_session_answer_prefs(session_id: str, body: AnswerPrefsRequest):
    current = _session_or_404(session_id)
    prefs = current.get("answer_prefs") or {}
    merged = {**prefs, **{k: v for k, v in body.model_dump().items() if v is not None}}
    session = get_runtime().call_sessions.update(session_id, {"answer_prefs": merged})
    if session and session.get("engine_id"):
        try:
            runtime = get_runtime().get(session["engine_id"])
            _apply_session_to_engine(runtime, session)
        except KeyError:
            pass
    return {"session": public_session(session), "preview": preview_answer(merged)}


@router.post("/sessions/{session_id}/document")
async def attach_session_document(
    session_id: str,
    kind: str = Form("document"),
    file: UploadFile = File(...),
):
    _session_or_404(session_id)
    name = file.filename or "upload.bin"
    raw = await file.read()
    tmp_dir = get_paths().data_dir / "tmp_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / name
    dest.write_bytes(raw)
    try:
        result = load_document(str(dest))
        if not result.ok:
            raise HTTPException(400, result.message or "Could not read file")
        session = get_runtime().call_sessions.attach_document(
            session_id, name=result.name, text=result.text, kind=kind
        )
        get_runtime().library.add(kind=kind if kind in ("resume", "document", "instructions") else "document", name=result.name, text=result.text)
        return public_session(session)
    finally:
        dest.unlink(missing_ok=True)


@router.post("/sessions/{session_id}/join")
def join_call_session(session_id: str, body: JoinSessionRequest):
    session = _session_or_404(session_id)
    connection = body.connection if body.connection in CONNECTIONS else "real"
    platform = body.platform if body.platform in PLATFORMS else "browser"
    rt = get_runtime()
    runtime = rt.create_engine(
        kind="live",
        model=session.get("model") or None,
        language=session.get("language") or "en",
        resume=str(session.get("resume") or ""),
        job_description=str(session.get("description") or ""),
        extra=compose_session_extra({**session, "connection": connection}),
    )
    session = rt.call_sessions.mark_live(
        session_id, engine_id=runtime.id, connection=connection, platform=platform
    )
    _apply_session_to_engine(runtime, session)
    return {
        "engine_id": runtime.id,
        "session": public_session(session),
        "model": runtime.engine.model,
        "language": runtime.engine.language,
        "auto_answer": bool(session.get("auto_answer")),
    }


@router.post("/sessions/{session_id}/end")
def end_call_session(session_id: str):
    session = get_runtime().call_sessions.mark_ended(session_id)
    if session is None:
        raise HTTPException(404, "Session not found")
    return public_session(session)


@router.post("/sessions/{session_id}/transcript")
def append_session_transcript(session_id: str, body: TranscriptLineRequest):
    session = _session_or_404(session_id)
    if not session.get("save_transcript", True):
        return public_session(session)
    role = body.role if body.role in ("interviewer", "you", "assistant") else "interviewer"
    updated = get_runtime().call_sessions.append_transcript(
        session_id, role=role, text=body.text.strip(), t=body.t
    )
    return public_session(updated)


@router.post("/sessions/{session_id}/mock-question")
def next_mock_question(session_id: str):
    session = _session_or_404(session_id)
    question = get_runtime().call_sessions.next_mock_question(session_id)
    if not question:
        raise HTTPException(404, "Session not found")
    t = elapsed_seconds(session.get("started_at")) if session.get("started_at") else 0
    get_runtime().call_sessions.append_transcript(session_id, role="interviewer", text=question, t=t)
    return {"question": question, "t": t}


@router.get("/library")
def list_library(kind: Optional[str] = None):
    return {"items": get_runtime().library.list_public(kind=kind)}


@router.post("/library")
def create_library_item(body: LibraryCreateRequest):
    item = get_runtime().library.add(kind=body.kind, name=body.name, text=body.text)
    return {"id": item["id"], "kind": item["kind"], "name": item["name"], "chars": len(item["text"])}


@router.post("/library/upload")
async def upload_library_item(kind: str = Form("document"), file: UploadFile = File(...)):
    name = file.filename or "upload.bin"
    raw = await file.read()
    tmp_dir = get_paths().data_dir / "tmp_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / name
    dest.write_bytes(raw)
    try:
        result = load_document(str(dest))
        if not result.ok:
            raise HTTPException(400, result.message or "Could not read file")
        item = get_runtime().library.add(kind=kind, name=result.name, text=result.text)
        return {"id": item["id"], "kind": item["kind"], "name": item["name"], "chars": len(item["text"])}
    finally:
        dest.unlink(missing_ok=True)


@router.delete("/library/{item_id}")
def delete_library_item(item_id: str):
    ok = get_runtime().library.delete(item_id)
    if not ok:
        raise HTTPException(404, "Item not found")
    return {"ok": True}


# ── privacy / native overlay ────────────────────────────────────────


def _overlay_meta(runtime) -> dict:
    return runtime.meta.setdefault("overlay", {})


@router.post("/privacy/overlay")
def open_privacy_overlay(body: EngineIdBody, request: Request):
    runtime = _engine_or_404(body.engine_id)
    base = str(request.base_url).rstrip("/")
    result = spawn_native_overlay(runtime, base)
    overlay = _overlay_meta(runtime)
    overlay.update({"status": "Hidden from share", "seq": int(overlay.get("seq") or 0)})
    return result


@router.post("/privacy/overlay/stop")
def stop_privacy_overlay(body: EngineIdBody):
    runtime = _engine_or_404(body.engine_id)
    stop_native_overlay(runtime)
    return {"ok": True}


def apply_privacy_command(runtime, command: str) -> dict[str, Any]:
    """Set overlay command (browser poll) and optionally native listen toggle."""
    overlay = _overlay_meta(runtime)
    overlay["seq"] = int(overlay.get("seq") or 0) + 1
    overlay["command"] = command
    if command in {"listen", "stop_listen", "toggle_listen"}:
        apply_native_listen_command(runtime, command)
    return {"ok": True, "seq": overlay["seq"], "command": command}


@router.post("/privacy/command")
def privacy_command(body: PrivacyCommandRequest):
    runtime = _engine_or_404(body.engine_id)
    return apply_privacy_command(runtime, body.command)


@router.post("/privacy/state")
def privacy_state(body: PrivacyStateRequest):
    runtime = _engine_or_404(body.engine_id)
    overlay = _overlay_meta(runtime)
    if body.listening is not None:
        overlay["listening"] = body.listening
    if body.auto is not None:
        overlay["auto"] = body.auto
    if body.transcript is not None:
        overlay["transcript"] = body.transcript
    if body.answer is not None:
        overlay["answer"] = body.answer
    if body.status is not None:
        overlay["status"] = body.status
    return {"ok": True, "overlay": overlay}
