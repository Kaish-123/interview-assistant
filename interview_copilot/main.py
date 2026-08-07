#!/usr/bin/env python3
"""
Interview Copilot — Parakeet-inspired real-time interview assistant.

Flow:
  1) Setup session (resume, JD, model, language, audio source)
  2) Live overlay listens (BlackHole/mic) → transcribes → auto-answers questions
  3) Analyze Screen for coding problems
  4) End + Notes writes post-call summary under interview_copilot/sessions/

Run from repo root:
  python -m interview_copilot.main

Or:
  python interview_copilot/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python interview_copilot/main.py` from repo root
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from interview_copilot.ui.overlay import OverlayWindow
from interview_copilot.ui.setup_window import SetupWindow


def main():
    setup = SetupWindow(on_start=lambda cfg: None)

    def start_session(cfg: dict):
        setup.withdraw()
        OverlayWindow(setup, cfg)

    setup.on_start = start_session
    setup.mainloop()


if __name__ == "__main__":
    main()
