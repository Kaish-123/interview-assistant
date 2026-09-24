"""Filesystem layout for the Interview Copilot package."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    """Resolved directories used across Studio and Live."""

    package_root: Path
    repo_root: Path
    sessions_dir: Path
    data_dir: Path
    logs_dir: Path

    def ensure(self) -> AppPaths:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        return self

    @property
    def env_candidates(self) -> tuple[Path, ...]:
        """Load order: repo .env first (shared), then package .env."""
        return (
            self.repo_root / ".env",
            self.package_root / ".env",
        )

    @property
    def chats_json(self) -> Path:
        return self.data_dir / "chats.json"

    @property
    def tabs_json(self) -> Path:
        return self.data_dir / "tabs.json"

    @property
    def ui_prefs_json(self) -> Path:
        return self.data_dir / "ui_prefs.json"

    @property
    def setup_profiles_json(self) -> Path:
        return self.data_dir / "setup_profiles.json"

    @property
    def call_sessions_json(self) -> Path:
        return self.data_dir / "call_sessions.json"

    @property
    def library_json(self) -> Path:
        return self.data_dir / "library.json"


@lru_cache(maxsize=1)
def get_paths() -> AppPaths:
    package_root = Path(__file__).resolve().parents[2]
    repo_root = package_root.parent
    return AppPaths(
        package_root=package_root,
        repo_root=repo_root,
        sessions_dir=package_root / "sessions",
        data_dir=package_root / "data",
        logs_dir=package_root / "logs",
    ).ensure()
