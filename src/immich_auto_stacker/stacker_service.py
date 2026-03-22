"""One scan cycle: fetch assets, group by regex, create stacks."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from immich_sdk.models import MetadataSearchDto
from loguru import logger
from tqdm import tqdm

from immich_auto_stacker.matching import StackGroup, apply_asset_to_groups
from immich_auto_stacker.settings import Settings

if TYPE_CHECKING:
    from immich_auto_stacker.immich_api import ImmichApiClient


@dataclass
class ScanStats:
    """Counters for one scan run."""

    stackable: int = 0
    already_stacked: int = 0
    not_stackable: int = 0
    success: int = 0
    failed: int = 0


def _short_key(key: str, max_len: int = 48) -> str:
    """Truncate long filenames for tqdm postfix (one line)."""
    if len(key) <= max_len:
        return key
    return f"{key[: max_len - 1]}…"


def _stack_postfix(pbar: Any, refresh: bool, fields: dict[str, object]) -> None:
    """Thin wrapper: tqdm typings vary by import path; postfix is dynamic."""
    pbar.set_postfix(ordered_dict=fields, refresh=refresh)


def run_scan_cycle(settings: Settings, api: ImmichApiClient) -> ScanStats:
    """Execute a single end-to-end scan (search, group, stack)."""

    stats = ScanStats()
    ver = api.get_server_version()
    logger.info("Connected to Immich server version {}", ver)

    taken_after: datetime | None = None
    if settings.newer_than_delta.total_seconds() != 0:
        taken_after = datetime.now(UTC) - settings.newer_than_delta

    groups: dict[str, StackGroup] = {}
    next_page: float | None = 1.0
    total_count = 0

    while next_page is not None:
        dto = MetadataSearchDto.model_construct(
            page=int(next_page),
            size=500,
        )
        resp = api.search_metadata(dto, taken_after=taken_after)
        assets_page = resp.assets
        total_count += assets_page.count
        for a in assets_page.items:
            apply_asset_to_groups(
                groups,
                asset_id=a.id,
                original_file_name=a.originalFileName,
                file_created_at=a.fileCreatedAt,
                match_pattern=settings.match_pattern,
                parent_pattern=settings.parent_pattern,
                compare_created=settings.compare_created,
            )
        raw_next = assets_page.nextPage
        next_page = None if raw_next is None else float(raw_next)

    logger.info(
        "Search finished: {} assets in page stream, {} candidate groups",
        total_count,
        len(groups),
    )

    group_items = list(groups.items())
    with tqdm(
        group_items,
        total=len(group_items),
        desc="Stacks",
        unit="grp",
        file=sys.stderr,
        mininterval=0.25,
        disable=False,
    ) as pbar:
        for key, s in pbar:
            if not s.stackable():
                stats.not_stackable += 1
                logger.debug("Skip group {!r}: need parent and at least one child", key)
                continue
            assert s.parent_id is not None
            stats.stackable += 1
            parent = api.get_asset_info(s.parent_id)
            st = parent.stack
            if st is not None and st.assetCount > 0:
                stats.already_stacked += 1
                logger.debug("Group {!r}: parent already in a stack", key)
                continue

            ordered_ids: list[str] = [s.parent_id]
            for cid in s.child_ids:
                if cid not in ordered_ids:
                    ordered_ids.append(cid)

            if settings.read_only or settings.dry_run:
                _stack_postfix(
                    pbar,
                    refresh=False,
                    fields={
                        "last": _short_key(key),
                        "mode": "dry",
                        "n": len(ordered_ids),
                    },
                )
                continue

            try:
                api.create_stack(ordered_ids)
            except Exception:
                logger.exception("Failed to create stack for group {!r}", key)
                stats.failed += 1
                _stack_postfix(
                    pbar,
                    refresh=True,
                    fields={
                        "last": _short_key(key),
                        "ok": stats.success,
                        "fail": stats.failed,
                    },
                )
            else:
                stats.success += 1
                _stack_postfix(
                    pbar,
                    refresh=True,
                    fields={
                        "last": _short_key(key),
                        "ok": stats.success,
                        "fail": stats.failed,
                        "n": len(ordered_ids),
                    },
                )

    logger.info(
        "Scan done: stackable={} already_stacked={} not_stackable={} success={} failed={}",
        stats.stackable,
        stats.already_stacked,
        stats.not_stackable,
        stats.success,
        stats.failed,
    )
    return stats
