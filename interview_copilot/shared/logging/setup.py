"""Logging configuration for Interview Copilot."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional

from interview_copilot.shared.config.paths import get_paths
from interview_copilot.shared.config.settings import AppSettings, get_settings

_CONFIGURED = False
LOGGER_NAME = "interview_copilot"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in (
            "stage",
            "stt_ms",
            "llm_ttft_ms",
            "llm_total_ms",
            "total_ms",
            "vad_ms",
            "model",
            "session_id",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class PlainFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = []
        for key in (
            "stage",
            "stt_ms",
            "llm_ttft_ms",
            "llm_total_ms",
            "total_ms",
            "vad_ms",
            "model",
            "session_id",
        ):
            if hasattr(record, key):
                extras.append(f"{key}={getattr(record, key)}")
        if extras:
            return f"{base} | {' '.join(extras)}"
        return base


def setup_logging(
    settings: Optional[AppSettings] = None,
    *,
    force: bool = False,
) -> logging.Logger:
    """
    Configure package logger once.

    Writes to stderr and `logs/interview_copilot.log`.
    """
    global _CONFIGURED
    settings = settings or get_settings()
    logger = logging.getLogger(LOGGER_NAME)

    if _CONFIGURED and not force:
        return logger

    logger.handlers.clear()
    logger.setLevel(getattr(logging, settings.log_level, logging.INFO))
    logger.propagate = False

    formatter: logging.Formatter
    if settings.log_json:
        formatter = JsonFormatter()
    else:
        formatter = PlainFormatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )

    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    log_path = get_paths().logs_dir / "interview_copilot.log"
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _CONFIGURED = True
    logger.debug(
        "logging configured",
        extra={
            "stage": "config",
            "model": settings.llm.default_model,
        },
    )
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    if not _CONFIGURED:
        setup_logging()
    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)
