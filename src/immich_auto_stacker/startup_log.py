"""Log effective configuration at startup (no secrets)."""

from __future__ import annotations

from loguru import logger

from immich_auto_stacker.settings import Settings

_MAX_PATTERN_PREVIEW = 80


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _preview_pattern(raw: str) -> str:
    if len(raw) <= _MAX_PATTERN_PREVIEW:
        return raw
    return f"{raw[: _MAX_PATTERN_PREVIEW - 1]}…"


def format_effective_settings_table(settings: Settings) -> str:
    """Markdown-style table for INFO logs (single message with embedded newlines)."""

    scan_value = (
        settings.scan_interval if not settings.once else "(not used: IMMICH_ONCE)"
    )
    rows: list[tuple[str, str]] = [
        ("IMMICH_BASE_URL", settings.immich_base_url),
        ("IMMICH_ONCE", str(settings.once)),
        ("IMMICH_SCAN_INTERVAL", scan_value),
        ("IMMICH_NEWER_THAN", settings.newer_than),
        ("IMMICH_COMPARE_CREATED", str(settings.compare_created)),
        ("IMMICH_READ_ONLY", str(settings.read_only)),
        ("IMMICH_DRY_RUN", str(settings.dry_run)),
        ("IMMICH_INSECURE_TLS", str(settings.insecure_tls)),
        ("IMMICH_LOG_LEVEL", settings.log_level.upper()),
        (
            "IMMICH_MATCH (preview)",
            _preview_pattern(settings.match),
        ),
        (
            "IMMICH_PARENT (preview)",
            _preview_pattern(settings.parent),
        ),
    ]
    lines = [
        "[config] Effective settings",
        "",
        "| Setting | Value |",
        "| --- | --- |",
    ]
    for key, val in rows:
        lines.append(f"| {_escape_cell(key)} | {_escape_cell(val)} |")
    return "\n".join(lines)


def log_effective_settings(settings: Settings) -> None:
    """Log INFO table and DEBUG full regex patterns."""

    logger.info("{}", format_effective_settings_table(settings))
    logger.debug("Full IMMICH_MATCH regex:\n{}", settings.match)
    logger.debug("Full IMMICH_PARENT regex:\n{}", settings.parent)
