"""Landing, login pages, and email/Google auth."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from interview_copilot.apps.web.server import app


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTH_REQUIRED", "0")
    monkeypatch.setenv("AUTH_DEV_SHOW_CODE", "1")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")
    monkeypatch.setattr(
        "interview_copilot.apps.web.auth.store.users_path",
        lambda: tmp_path / "users.json",
    )
    return TestClient(app)


def test_landing_is_marketing_home(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Try Interview Copilot for Free" in r.text
    assert "Screen share safe" in r.text
    assert "Sign in" in r.text
    assert "Task Manager" not in r.text
    assert "Cursor Undetectable" not in r.text


def test_login_page(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "Continue with Google" in r.text
    assert "Continue with Email" in r.text


def test_app_page_serves_copilot(client):
    r = client.get("/app")
    assert r.status_code == 200
    assert "btn-overlay-float" in r.text
    assert "Hide from share" in r.text


def test_auth_me_guest(client):
    data = client.get("/api/auth/me").json()
    assert data["user"] is None
    assert data["google"] is False


def test_email_login_roundtrip(client):
    start = client.post("/api/auth/email/start", json={"email": "dev@example.com"})
    assert start.status_code == 200
    code = start.json()["dev_code"]
    assert len(code) == 6
    verify = client.post(
        "/api/auth/email/verify",
        json={"email": "dev@example.com", "code": code},
    )
    assert verify.status_code == 200
    me = client.get("/api/auth/me").json()
    assert me["user"]["email"] == "dev@example.com"
    out = client.post("/api/auth/logout")
    assert out.status_code == 200
    assert client.get("/api/auth/me").json()["user"] is None


def test_google_not_configured(client):
    r = client.get("/api/auth/google/start", follow_redirects=False)
    assert r.status_code == 501


def test_auth_required_redirects_app(monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    gated = TestClient(app)
    r = gated.get("/app", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers.get("location", "")
    api = gated.get("/api/engines")
    assert api.status_code == 401
    assert gated.get("/").status_code == 200
    assert gated.get("/login").status_code == 200
