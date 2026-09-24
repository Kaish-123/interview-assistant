from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

from .config import auth_config
from .store import current_user

_OPEN_PREFIXES = (
    "/api/auth",
    "/api/status",
    "/static",
    "/login",
    "/favicon",
)
_OPEN_EXACT = {"/", "/health"}


def _is_open(path: str) -> bool:
    if path in _OPEN_EXACT:
        return True
    return any(path == p or path.startswith(p + "/") or path.startswith(p) for p in _OPEN_PREFIXES)


async def auth_gate(request: Request, call_next):
    cfg = auth_config()
    if not cfg.required:
        return await call_next(request)
    path = request.url.path
    if _is_open(path):
        return await call_next(request)
    if current_user(request):
        return await call_next(request)
    if path.startswith("/api/"):
        return JSONResponse({"detail": "Sign in required."}, status_code=401)
    nxt = path if path.startswith("/") else "/app"
    return RedirectResponse(f"/login?next={nxt}", status_code=302)
