from __future__ import annotations

import hashlib
import hmac
import random
import smtplib
import time
from email.message import EmailMessage
from typing import Any

from .config import AuthConfig

_codes: dict[str, dict[str, Any]] = {}
TTL_SEC = 600
MAX_ATTEMPTS = 8


def _hash(secret: str, email: str, code: str) -> str:
    raw = f"{email}:{code}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def issue_code(email: str, cfg: AuthConfig) -> str:
    email_n = email.strip().lower()
    code = f"{random.SystemRandom().randint(0, 999999):06d}"
    _codes[email_n] = {
        "digest": _hash(cfg.secret, email_n, code),
        "expires": time.time() + TTL_SEC,
        "attempts": 0,
    }
    return code


def verify_code(email: str, code: str, cfg: AuthConfig) -> bool:
    email_n = email.strip().lower()
    row = _codes.get(email_n)
    if not row:
        return False
    if time.time() > float(row["expires"]):
        _codes.pop(email_n, None)
        return False
    row["attempts"] = int(row.get("attempts") or 0) + 1
    if row["attempts"] > MAX_ATTEMPTS:
        _codes.pop(email_n, None)
        return False
    ok = hmac.compare_digest(row["digest"], _hash(cfg.secret, email_n, code.strip()))
    if ok:
        _codes.pop(email_n, None)
    return ok


def send_login_email(email: str, code: str, cfg: AuthConfig) -> None:
    subject = "Your Interview Copilot login code"
    body = (
        f"Your login code is {code}.\n\n"
        "It expires in 10 minutes. Open it on this device, or type the code on the login page.\n"
    )
    print(f"[auth] Login code for {email}: {code}", flush=True)
    if not cfg.smtp_ready:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.smtp_from
    msg["To"] = email
    msg.set_content(body)
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=20) as smtp:
        smtp.starttls()
        if cfg.smtp_user:
            smtp.login(cfg.smtp_user, cfg.smtp_password)
        smtp.send_message(msg)
