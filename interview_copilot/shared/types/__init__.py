"""Shared typed aliases used across packages."""

from __future__ import annotations

from typing import Literal, TypedDict

AudioInputMode = Literal["internal", "external"]
AnswerMode = Literal["default", "quick", "detailed", "code"]
PlatformName = Literal["macos", "windows", "linux", "unknown"]


class ChatMessage(TypedDict, total=False):
    role: str
    content: str | list


class SessionMeta(TypedDict, total=False):
    title: str
    session_id: str
    model: str
    language: str
