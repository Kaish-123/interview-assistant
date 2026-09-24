from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Request

from interview_copilot.shared.config.paths import get_paths

_lock = threading.Lock()
SESSION_KEY = "user_id"


def users_path() -> Path:
    return get_paths().data_dir / "users.json"


def load_users() -> dict[str, Any]:
    path = users_path()
    if not path.exists():
        return {"users": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"users": []}
    if not isinstance(data, dict) or not isinstance(data.get("users"), list):
        return {"users": []}
    return data


def _save(data: dict[str, Any]) -> None:
    path = users_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "name": user.get("name") or user.get("email"),
        "provider": user.get("provider"),
    }


def get_user(user_id: str | None) -> dict[str, Any] | None:
    if not user_id:
        return None
    with _lock:
        for user in load_users().get("users", []):
            if str(user.get("id")) == str(user_id):
                return user
    return None


def current_user(request: Request) -> dict[str, Any] | None:
    return get_user(request.session.get(SESSION_KEY))


def upsert_user(
    *,
    email: str,
    name: str = "",
    provider: str,
    google_sub: str = "",
) -> dict[str, Any]:
    email_n = email.strip().lower()
    with _lock:
        data = load_users()
        users: list[dict[str, Any]] = data.setdefault("users", [])
        found: dict[str, Any] | None = None
        for user in users:
            if google_sub and user.get("google_sub") == google_sub:
                found = user
                break
            if str(user.get("email", "")).lower() == email_n:
                found = user
                break
        now = datetime.now(timezone.utc).isoformat()
        if found is None:
            found = {
                "id": uuid.uuid4().hex,
                "email": email_n,
                "name": name or email_n.split("@")[0],
                "provider": provider,
                "google_sub": google_sub,
                "created_at": now,
                "last_login_at": now,
            }
            users.append(found)
        else:
            found["email"] = email_n
            if name:
                found["name"] = name
            if google_sub:
                found["google_sub"] = google_sub
            found["provider"] = provider
            found["last_login_at"] = now
        _save(data)
        return dict(found)


def login_user(request: Request, user: dict[str, Any]) -> None:
    request.session[SESSION_KEY] = user["id"]


def logout_user(request: Request) -> None:
    request.session.clear()
