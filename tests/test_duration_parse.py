"""Tests for duration parsing."""

from datetime import timedelta

import pytest

from immich_auto_stacker.duration_parse import parse_immich_duration


def test_parse_seconds() -> None:
    assert parse_immich_duration("300s") == timedelta(seconds=300)


def test_parse_hours() -> None:
    assert parse_immich_duration("1h") == timedelta(hours=1)


def test_parse_minutes() -> None:
    assert parse_immich_duration("15m") == timedelta(minutes=15)


def test_invalid_raises() -> None:
    with pytest.raises(ValueError):
        parse_immich_duration("2d")
