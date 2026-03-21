"""Parse duration strings compatible with immich-stacker (seconds, minutes, hours)."""

from __future__ import annotations

import re
from datetime import timedelta

_DURATION_RE = re.compile(
    r"^\s*(?P<n>\d+)\s*(?P<u>[smh])\s*$",
    re.IGNORECASE,
)


def parse_immich_duration(raw: str) -> timedelta:
    """Parse a duration like ``300s``, ``15m``, ``24h`` (Go time.ParseDuration subset)."""

    m = _DURATION_RE.match(raw.strip())
    if not m:
        msg = f"Invalid duration {raw!r}; expected <number>s|m|h (e.g. 300s, 1h)"
        raise ValueError(msg)
    n = int(m.group("n"))
    unit = m.group("u").lower()
    if unit == "s":
        return timedelta(seconds=n)
    if unit == "m":
        return timedelta(minutes=n)
    return timedelta(hours=n)
