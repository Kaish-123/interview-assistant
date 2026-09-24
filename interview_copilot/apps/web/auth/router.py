from __future__ import annotations

import re
import secrets
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from . import codes, google as google_oauth
from .config import auth_config
from .store import current_user, login_user, logout_user, public_user, upsert_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailStart(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class EmailVerify(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    code: str = Field(min_length=4, max_length=8)


def _cfg():
    return auth_config()


@router.get("/me")
def me(request: Request) -> dict[str, Any]:
    cfg = _cfg()
    user = current_user(request)
    return {
        "user": public_user(user) if user else None,
        "required": cfg.required,
        "google": cfg.google_ready,
        "dev_show_code": cfg.dev_show_code,
    }


@router.post("/logout")
def logout(request: Request) -> dict[str, str]:
    logout_user(request)
    return {"ok": "true"}


@router.get("/google/start")
def google_start(request: Request, next: str = "/app"):
    cfg = _cfg()
    if not cfg.google_ready:
        raise HTTPException(
            status_code=501,
            detail="Google sign-in is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    state = secrets.token_urlsafe(24)
    request.session["oauth_state"] = state
    request.session["oauth_next"] = next if next.startswith("/") else "/app"
    return RedirectResponse(google_oauth.authorize_url(cfg, state), status_code=302)


@router.get("/google/callback")
def google_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    cfg = _cfg()
    nxt = request.session.pop("oauth_next", "/app") or "/app"
    expected = request.session.pop("oauth_state", "")
    if error:
        return RedirectResponse(f"/login?error=google", status_code=302)
    if not code or not expected or not secrets.compare_digest(expected, state or ""):
        return RedirectResponse("/login?error=state", status_code=302)
    try:
        info = google_oauth.exchange_code(cfg, code)
    except Exception:
        return RedirectResponse("/login?error=google", status_code=302)
    email = str(info.get("email") or "").strip().lower()
    if not email:
        return RedirectResponse("/login?error=email", status_code=302)
    user = upsert_user(
        email=email,
        name=str(info.get("name") or ""),
        provider="google",
        google_sub=str(info.get("sub") or ""),
    )
    login_user(request, user)
    return RedirectResponse(nxt, status_code=302)


@router.post("/email/start")
def email_start(payload: EmailStart, request: Request) -> dict[str, Any]:
    cfg = _cfg()
    email = str(payload.email).strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    code = codes.issue_code(email, cfg)
    try:
        codes.send_login_email(email, code, cfg)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not send email: {exc}") from exc
    request.session["pending_email"] = email
    body: dict[str, Any] = {"ok": True, "email": email}
    if cfg.dev_show_code:
        body["dev_code"] = code
    return body


@router.post("/email/verify")
def email_verify(payload: EmailVerify, request: Request) -> dict[str, Any]:
    cfg = _cfg()
    email = str(payload.email).strip().lower()
    if not codes.verify_code(email, payload.code, cfg):
        raise HTTPException(status_code=400, detail="That code is invalid or expired.")
    user = upsert_user(email=email, provider="email")
    login_user(request, user)
    return {"ok": True, "user": public_user(user)}
