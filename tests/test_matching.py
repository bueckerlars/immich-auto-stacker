"""Tests for regex grouping (immich-stacker README examples)."""

import re

from immich_auto_stacker.matching import (
    StackGroup,
    apply_asset_to_groups,
    group_key_from_filename,
)


def test_raw_jpg_pair() -> None:
    match = re.compile(r"\.(JPG|RW2)$", re.IGNORECASE)
    parent = re.compile(r"\.JPG$", re.IGNORECASE)
    groups: dict[str, StackGroup] = {}
    apply_asset_to_groups(
        groups,
        asset_id="a1",
        original_file_name="IMG_0001.JPG",
        file_created_at="2020-01-01T00:00:00Z",
        match_pattern=match,
        parent_pattern=parent,
        compare_created=False,
    )
    apply_asset_to_groups(
        groups,
        asset_id="a2",
        original_file_name="IMG_0001.RW2",
        file_created_at="2020-01-01T00:00:00Z",
        match_pattern=match,
        parent_pattern=parent,
        compare_created=False,
    )
    assert len(groups) == 1
    g = next(iter(groups.values()))
    assert g.parent_id == "a1"
    assert g.child_ids == ["a2"]
    assert g.stackable() is True


def test_burst_cover_parent() -> None:
    match = re.compile(r"BURST[0-9]{3}(_COVER)?\.jpg$", re.IGNORECASE)
    parent = re.compile(r"_COVER\.jpg$", re.IGNORECASE)
    groups: dict[str, StackGroup] = {}
    apply_asset_to_groups(
        groups,
        asset_id="c1",
        original_file_name="BURST001_COVER.jpg",
        file_created_at="2020-01-01T00:00:00Z",
        match_pattern=match,
        parent_pattern=parent,
        compare_created=False,
    )
    apply_asset_to_groups(
        groups,
        asset_id="c2",
        original_file_name="BURST001.jpg",
        file_created_at="2020-01-01T00:00:00Z",
        match_pattern=match,
        parent_pattern=parent,
        compare_created=False,
    )
    g = next(iter(groups.values()))
    assert g.parent_id == "c1"
    assert "c2" in g.child_ids


def test_group_key_replace_all() -> None:
    match = re.compile(r"\.(JPG|RW2)$", re.IGNORECASE)
    k1 = group_key_from_filename(
        "IMG_123.JPG",
        match,
        compare_created=False,
        file_created_at="",
    )
    k2 = group_key_from_filename(
        "IMG_123.RW2",
        match,
        compare_created=False,
        file_created_at="",
    )
    assert k1 == k2 == "IMG_123"


def test_non_participant_returns_none() -> None:
    match = re.compile(r"\.(JPG|RW2)$", re.IGNORECASE)
    k = group_key_from_filename(
        "notes.txt",
        match,
        compare_created=False,
        file_created_at="",
    )
    assert k is None
