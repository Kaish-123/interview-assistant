"""High-level document load helpers for MessageStore / engines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from interview_copilot.packages.context.extract import ExtractError, extract_text_from_file
from interview_copilot.shared.logging import get_logger

logger = get_logger("context.documents")


@dataclass(frozen=True)
class DocumentLoadResult:
    ok: bool
    message: str
    text: str = ""
    name: str = ""
    path: str = ""

    @property
    def char_count(self) -> int:
        return len(self.text)


def load_document(
    file_path: str | Path,
    *,
    max_chars: int = 50_000,
) -> DocumentLoadResult:
    """
    Load a single file into text for system-context injection.

    Returns DocumentLoadResult (never raises for normal extract failures).
    """
    path = Path(file_path)
    name = path.name
    try:
        text = extract_text_from_file(path)
        if not text.strip():
            return DocumentLoadResult(
                ok=False,
                message=f"⚠️ {name} appears empty or has no readable text.",
                name=name,
                path=str(path),
            )
        clipped = text[:max_chars]
        size_hint = f"{len(text):,} chars"
        logger.info(
            f"loaded document {name} ({size_hint})",
            extra={"stage": "context"},
        )
        return DocumentLoadResult(
            ok=True,
            message=f"📄 {name} loaded ({size_hint}).",
            text=clipped,
            name=name,
            path=str(path),
        )
    except ExtractError as e:
        return DocumentLoadResult(
            ok=False,
            message=f"❌ {e}",
            name=name,
            path=str(path),
        )
    except Exception as e:
        return DocumentLoadResult(
            ok=False,
            message=f"❌ {name}: {e}",
            name=name,
            path=str(path),
        )
