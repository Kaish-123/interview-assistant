#!/usr/bin/env python3
"""
Interview Copilot entrypoints.

Live (Parakeet-style overlay):
  python3 -m interview_copilot.main
  python3 -m interview_copilot.main --live

Studio shell:
  python3 -m interview_copilot.main --studio
  python3 -m interview_copilot.apps.studio

Web companion (Studio + Live in browser):
  python3 -m interview_copilot.main --web
  python3 -m interview_copilot.apps.web
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _run_live() -> None:
    from interview_copilot.ui.overlay import OverlayWindow
    from interview_copilot.ui.setup_window import SetupWindow

    setup = SetupWindow(on_start=lambda cfg: None)

    def start_session(cfg: dict):
        setup.withdraw()
        OverlayWindow(setup, cfg)

    setup.on_start = start_session
    setup.mainloop()


def _run_studio() -> None:
    from interview_copilot.apps.studio import run_studio

    run_studio()


def _run_web() -> None:
    from interview_copilot.apps.web.server import main as web_main

    web_main()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Interview Copilot")
    parser.add_argument(
        "--studio",
        action="store_true",
        help="Open Studio shell (chat + listen wired to packages)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Open Live setup + overlay (default if neither flag set)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Run Parakeet-style web companion at http://127.0.0.1:8787",
    )
    args = parser.parse_args(argv)

    if args.web:
        _run_web()
    elif args.studio and not args.live:
        _run_studio()
    else:
        _run_live()


if __name__ == "__main__":
    main()
