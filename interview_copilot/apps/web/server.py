"""Interview Copilot web companion — FastAPI entrypoint."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from interview_copilot.apps.web.auth.config import auth_config
from interview_copilot.apps.web.auth.gate import auth_gate
from interview_copilot.apps.web.auth.router import router as auth_router
from interview_copilot.apps.web.routers import router
from interview_copilot.apps.web.runtime import get_runtime
from interview_copilot.apps.web.stt_live import router as stt_live_router
from interview_copilot.platform.hotkeys import (
    global_hotkeys_allowed,
    start_global_listen_hotkeys,
    stop_global_listen_hotkeys,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
MARKETING_DIR = STATIC_DIR / "marketing"


def _arm_global_listen_hotkey():
    """Start OS-global `` ` ``. Safe to call from main() and from lifespan."""
    if not global_hotkeys_allowed():
        return None
    try:
        from interview_copilot.apps.web.global_hotkeys import dispatch_listen_toggle

        return start_global_listen_hotkeys(on_listen_toggle=dispatch_listen_toggle)
    except Exception as exc:
        print(f"Global listen hotkey unavailable: {exc}")
        return None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_runtime()
    listener = _arm_global_listen_hotkey()
    yield
    # Keep the listener if main() owns it (same singleton); only stop if we started it
    # and the process is shutting down.
    if listener is not None and not getattr(_app.state, "hotkeys_from_main", False):
        stop_global_listen_hotkeys(listener)


app = FastAPI(
    title="Interview Copilot Web",
    description="Landing, auth, and Studio + Live web companion over shared packages",
    version="1.0.0",
    lifespan=lifespan,
)

class AuthGateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        return await auth_gate(request, call_next)


cfg = auth_config()
# Innermost → outermost: gate (needs session) → session → CORS
app.add_middleware(AuthGateMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=cfg.secret,
    same_site="lax",
    https_only=False,
    max_age=14 * 24 * 3600,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cfg.public_url, "http://127.0.0.1:8787", "http://localhost:8787"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(router)
app.include_router(stt_live_router)


@app.get("/")
def landing():
    return FileResponse(MARKETING_DIR / "landing.html")


@app.get("/login")
def login():
    return FileResponse(MARKETING_DIR / "login.html")


@app.get("/app")
def copilot_app():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"ok": True}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main() -> None:
    import uvicorn

    # Arm pynput on the real main thread *before* asyncio starts. Matching
    # chatgpt_toggle_listener: Listener thread + blocking UI/server loop.
    get_runtime()
    listener = _arm_global_listen_hotkey()
    app.state.hotkeys_from_main = listener is not None
    try:
        uvicorn.run(
            app,
            host=os.getenv("WEB_HOST", "127.0.0.1"),
            port=int(os.getenv("WEB_PORT", "8787")),
            timeout_keep_alive=5,
            lifespan="on",
        )
    finally:
        stop_global_listen_hotkeys(listener)


if __name__ == "__main__":
    main()
