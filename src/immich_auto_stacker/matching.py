"""Filename grouping logic aligned with mattdavis90/immich-stacker."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


def _empty_str_list() -> list[str]:
    return []


@dataclass
class StackGroup:
    """Assets sharing the same computed group key."""

    parent_id: str | None = None
    child_ids: list[str] = field(default_factory=_empty_str_list)

    def stackable(self) -> bool:
        return self.parent_id is not None and len(self.child_ids) > 0


def group_key_from_filename(
    original_file_name: str,
    match_pattern: re.Pattern[str],
    *,
    compare_created: bool,
    file_created_at: str,
) -> str | None:
    """Return the grouping key, or ``None`` if the file does not participate.

    Uses :func:`re.search` so patterns like ``\\.(JPG|RW2)$`` match typical filenames
    (Go's ``regexp.Match`` would require a ``^.*`` prefix for the same intent).
    """

    if not match_pattern.search(original_file_name):
        return None
    key = match_pattern.sub("", original_file_name)
    if compare_created:
        key += "_" + _file_created_local_string(file_created_at)
    return key


def _file_created_local_string(file_created_at: str) -> str:
    """Mirror Go's ``FileCreatedAt.Local().String()`` as closely as practical."""

    s = file_created_at.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return file_created_at
    local = dt.astimezone()
    return local.strftime("%Y-%m-%d %H:%M:%S %z")


def apply_asset_to_groups(
    groups: dict[str, StackGroup],
    *,
    asset_id: str,
    original_file_name: str,
    file_created_at: str,
    match_pattern: re.Pattern[str],
    parent_pattern: re.Pattern[str],
    compare_created: bool,
) -> None:
    """Merge one asset into ``groups`` (mutates)."""

    key = group_key_from_filename(
        original_file_name,
        match_pattern,
        compare_created=compare_created,
        file_created_at=file_created_at,
    )
    if key is None:
        return
    g = groups.get(key)
    if g is None:
        g = StackGroup()
        groups[key] = g
    if parent_pattern.search(original_file_name):
        g.parent_id = asset_id
    elif asset_id not in g.child_ids:
        g.child_ids.append(asset_id)
