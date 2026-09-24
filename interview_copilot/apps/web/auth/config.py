from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from interview_copilot.shared.config.paths import get_paths


def _flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AuthConfig:
    secret: str
    required: bool
    public_url: str
    google_client_id: str
    google_client_secret: str
    dev_show_code: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str

    @property
    def google_ready(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def smtp_ready(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)


def auth_config() -> AuthConfig:
    paths = get_paths()
    for env_path in (paths.repo_root / ".env", paths.package_root / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)
    return AuthConfig(
        secret=os.getenv("AUTH_SECRET", "dev-insecure-change-me"),
        required=_flag("AUTH_REQUIRED", False),
        public_url=os.getenv("AUTH_PUBLIC_URL", "http://127.0.0.1:8787").rstrip("/"),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", "").strip(),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
        dev_show_code=_flag("AUTH_DEV_SHOW_CODE", True),
        smtp_host=os.getenv("SMTP_HOST", "").strip(),
        smtp_port=int(os.getenv("SMTP_PORT", "587") or "587"),
        smtp_user=os.getenv("SMTP_USER", "").strip(),
        smtp_password=os.getenv("SMTP_PASSWORD", "").strip(),
        smtp_from=os.getenv("SMTP_FROM", "Interview Copilot <noreply@localhost>").strip(),
    )
