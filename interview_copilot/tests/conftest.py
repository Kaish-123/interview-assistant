"""Web tests: keep APIs ungated unless a test opts into AUTH_REQUIRED."""

from __future__ import annotations

import os

os.environ.setdefault("AUTH_REQUIRED", "0")
os.environ.setdefault("AUTH_DEV_SHOW_CODE", "1")
os.environ.setdefault("INTERVIEW_COPILOT_DISABLE_NATIVE_OVERLAY", "1")
os.environ.setdefault("INTERVIEW_COPILOT_DISABLE_GLOBAL_HOTKEYS", "1")
