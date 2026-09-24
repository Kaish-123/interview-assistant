"""In-memory runtime engines for Studio and Live web sessions."""

from __future__ import annotations

import sys
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from interview_copilot.packages.llm import InterviewLLMEngine
from interview_copilot.packages.prompts import PromptTabsStore, SetupProfilesStore
from interview_copilot.packages.session import (
    CallSessionStore,
    ChatHistoryStore,
    LibraryStore,
    UIPreferencesStore,
)
from interview_copilot.packages.session.chats import AUTO_SAVE_TITLE, prune_sessions
from interview_copilot.platform.hotkeys import global_hotkeys_active
from interview_copilot.platform.privacy import overlay_supported
from interview_copilot.shared.config.settings import get_settings
from interview_copilot.shared.logging import setup_logging


@dataclass
class RuntimeEngine:
    id: str
    kind: str  # studio | live
    engine: InterviewLLMEngine
    bookmarks: list = field(default_factory=list)
    chat_index: int | None = None
    title: str = AUTO_SAVE_TITLE
    meta: dict[str, Any] = field(default_factory=dict)
    partial: str = ""
    lock: threading.Lock = field(default_factory=threading.Lock)


class AppRuntime:
    """Shared stores + per-browser session engines."""

    def __init__(self) -> None:
        self.settings = get_settings()
        setup_logging(self.settings)
        self.chats = ChatHistoryStore()
        self.call_sessions = CallSessionStore()
        self.library = LibraryStore()
        self.tabs = PromptTabsStore()
        self.profiles = SetupProfilesStore()
        self.prefs = UIPreferencesStore()
        self._engines: dict[str, RuntimeEngine] = {}
        self._lock = threading.Lock()
        self._hotkey_target_id: str | None = None

    def create_engine(
        self,
        *,
        kind: str = "studio",
        model: str | None = None,
        language: str = "en",
        resume: str = "",
        job_description: str = "",
        extra: str = "",
    ) -> RuntimeEngine:
        eng = InterviewLLMEngine(
            model=model or self.settings.llm.default_model,
            language=language,
            settings=self.settings,
        )
        eng.set_context(resume=resume, job_description=job_description, extra=extra)
        rid = uuid.uuid4().hex[:12]
        runtime = RuntimeEngine(id=rid, kind=kind, engine=eng)
        with self._lock:
            self._engines[rid] = runtime
        return runtime

    def get(self, engine_id: str) -> RuntimeEngine:
        with self._lock:
            runtime = self._engines.get(engine_id)
        if runtime is None:
            raise KeyError(engine_id)
        return runtime

    def drop(self, engine_id: str) -> None:
        with self._lock:
            self._engines.pop(engine_id, None)
            if self._hotkey_target_id == engine_id:
                self._hotkey_target_id = None

    def set_hotkey_target(self, engine_id: str) -> None:
        with self._lock:
            if engine_id in self._engines:
                self._hotkey_target_id = engine_id

    def preferred_for_global_hotkeys(self) -> RuntimeEngine | None:
        """Engine that should receive OS-global `` ` `` listen toggle."""
        with self._lock:
            engines = list(self._engines.values())
            target_id = self._hotkey_target_id
        if target_id:
            hit = next((e for e in engines if e.id == target_id), None)
            if hit is not None:
                return hit
        if not engines:
            return None
        lives = [e for e in engines if e.kind == "live"]
        for eng in reversed(lives):
            overlay = (eng.meta or {}).get("overlay") or {}
            if overlay.get("native") or overlay.get("listening") or overlay.get("pid"):
                return eng
        if lives:
            return lives[-1]
        studios = [e for e in engines if e.kind == "studio"]
        return studios[-1] if studios else engines[-1]

    def autosave(self, runtime: RuntimeEngine) -> None:
        with runtime.lock:
            self.chats.save_current_session(
                runtime.engine.messages,
                title=runtime.title or AUTO_SAVE_TITLE,
                bookmarks=runtime.bookmarks,
            )
            prune_sessions(self.chats, max_chats=10)

    def status(self) -> dict[str, Any]:
        key_ok = bool(self.settings.openai_api_key)
        models = list(self.settings.llm.available_models)
        return {
            "ok": key_ok,
            "api_key_configured": key_ok,
            "default_model": self.settings.llm.default_model,
            "models": models,
            "answer_modes": ["default", "quick", "detailed", "code"],
            "platform": "web",
            "os": sys.platform,
            "privacy_native": overlay_supported(),
            "global_hotkeys": global_hotkeys_active(),
        }


_runtime: AppRuntime | None = None


def get_runtime() -> AppRuntime:
    global _runtime
    if _runtime is None:
        _runtime = AppRuntime()
    return _runtime
