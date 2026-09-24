"""Recursive folder walk for attachable documents."""

from __future__ import annotations

import os
from pathlib import Path

from interview_copilot.packages.context.extract import SKIP_EXTS

SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
}

DEFAULT_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def collect_files_from_folder(
    folder_path: str | Path,
    *,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    skip_binary_exts: bool = True,
) -> list[str]:
    """
    Recursively collect readable file paths under a folder.

    Skips hidden dirs/files, build artifacts, and (optionally) known binary extensions.
    """
    root = Path(folder_path)
    if not root.is_dir():
        return []

    paths: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        )
        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if skip_binary_exts and (ext in SKIP_EXTS or fname == ".DS_Store"):
                continue
            try:
                if fpath.stat().st_size <= max_file_size:
                    paths.append(str(fpath.resolve()))
            except OSError:
                continue
    return paths
