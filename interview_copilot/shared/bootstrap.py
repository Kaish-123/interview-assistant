"""
Phase 1 Milestone 1 smoke check.

  python -m interview_copilot.shared.bootstrap

Prints platform, whether API key is present, paths, and a sample stage log.
"""

from __future__ import annotations

from interview_copilot.shared.config import get_paths, get_settings
from interview_copilot.shared.logging import StageTimer, setup_logging


def main() -> None:
    settings = get_settings()
    paths = get_paths()
    logger = setup_logging(settings, force=True)

    print("Interview Copilot — Phase 1 Milestone 1")
    print(f"  platform:     {settings.platform}")
    print(f"  has_api_key:  {settings.has_api_key}")
    print(f"  model:        {settings.llm.default_model}")
    print(f"  audio mode:   {settings.audio.default_input_mode}")
    print(f"  blackhole:    {settings.audio.blackhole_device}")
    print(f"  package:      {paths.package_root}")
    print(f"  sessions:     {paths.sessions_dir}")
    print(f"  data:         {paths.data_dir}")
    print(f"  logs:         {paths.logs_dir}")
    print(f"  env files:    {list(paths.env_candidates)}")

    timer = StageTimer(stage="bootstrap", meta={"model": settings.llm.default_model})
    timer.log("milestone 1 ok")
    logger.info("bootstrap complete", extra={"stage": "bootstrap"})


if __name__ == "__main__":
    main()
