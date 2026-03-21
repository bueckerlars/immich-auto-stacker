"""CLI entry: periodic or one-shot Immich stacking."""

from __future__ import annotations

import signal
import sys
import time

from loguru import logger

from immich_auto_stacker.context import ApplicationContext
from immich_auto_stacker.logging_setup import configure_logging
from immich_auto_stacker.settings import Settings
from immich_auto_stacker.stacker_service import run_scan_cycle

_stop_flag = False


def _set_stop(*_args: object) -> None:
    global _stop_flag
    _stop_flag = True


def main() -> None:
    """Load settings, run scan loop until SIGTERM/SIGINT or ``IMMICH_ONCE``."""

    try:
        settings = Settings()  # type: ignore[call-arg]
    except Exception:
        configure_logging("INFO")
        logger.exception("Invalid configuration")
        sys.exit(1)

    configure_logging(settings.log_level)

    if settings.insecure_tls:
        logger.warning(
            "IMMICH_INSECURE_TLS is enabled; TLS certificate verification is disabled",
        )

    ctx = ApplicationContext(settings)
    signal.signal(signal.SIGTERM, _set_stop)
    signal.signal(signal.SIGINT, _set_stop)

    while not _stop_flag:
        try:
            run_scan_cycle(settings, ctx.api)
        except Exception:
            logger.exception("Scan cycle failed")
        if settings.once or _stop_flag:
            break
        logger.info("Sleeping {} until next scan", settings.scan_interval_delta)
        remaining = settings.scan_interval_delta.total_seconds()
        while remaining > 0 and not _stop_flag:
            chunk = min(remaining, 1.0)
            time.sleep(chunk)
            remaining -= chunk

    logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
