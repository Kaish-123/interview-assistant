from __future__ import annotations

from urllib.parse import urlencode

import httpx

from .config import AuthConfig

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def redirect_uri(cfg: AuthConfig) -> str:
    return f"{cfg.public_url}/api/auth/google/callback"


def authorize_url(cfg: AuthConfig, state: str) -> str:
    params = {
        "client_id": cfg.google_client_id,
        "redirect_uri": redirect_uri(cfg),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
        "access_type": "online",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(cfg: AuthConfig, code: str) -> dict:
    with httpx.Client(timeout=20.0) as client:
        token_res = client.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": cfg.google_client_id,
                "client_secret": cfg.google_client_secret,
                "redirect_uri": redirect_uri(cfg),
                "grant_type": "authorization_code",
            },
        )
        token_res.raise_for_status()
        token = token_res.json()
        access = token.get("access_token")
        info_res = client.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access}"},
        )
        info_res.raise_for_status()
        return info_res.json()
