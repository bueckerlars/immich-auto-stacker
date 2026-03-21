"""Normalize Immich base URLs for the immich-sdk client (server root, no ``/api`` suffix)."""

from __future__ import annotations


def normalize_immich_base_url(raw: str) -> str:
    """Strip trailing slashes and a trailing ``/api`` segment.

    The SDK expects ``base_url`` such that requests use paths like ``/api/search/metadata``.
    Users migrating from immich-stacker often set ``IMMICH_ENDPOINT`` to ``.../api``;
    that suffix must not be duplicated.
    """

    s = raw.strip().rstrip("/")
    if s.lower().endswith("/api"):
        return s[:-4].rstrip("/")
    return s
