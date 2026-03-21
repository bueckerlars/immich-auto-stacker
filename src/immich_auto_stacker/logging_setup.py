"""Central loguru configuration."""

from __future__ import annotations

import sys

from loguru import logger

_VALID_LEVELS = frozenset(
    ("TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"),
)


def configure_logging(level: str) -> None:
    """Configure stderr logging; replaces any existing loguru handlers."""

    name = level.upper().strip()
    if name not in _VALID_LEVELS:
        name = "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        level=name,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{file.name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
