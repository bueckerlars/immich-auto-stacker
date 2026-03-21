"""Environment-backed configuration (composition root input)."""

from __future__ import annotations

import re
from datetime import timedelta

from pydantic import (
    AnyUrl,
    Field,
    SecretStr,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from immich_auto_stacker.duration_parse import parse_immich_duration
from immich_auto_stacker.url_normalize import normalize_immich_base_url


class Settings(BaseSettings):
    """Runtime settings from ``IMMICH_*`` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="IMMICH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr = Field(
        ...,
        description="Immich API key (x-api-key); requires asset.read and stack.*",
    )
    server_url: AnyUrl | None = Field(
        default=None,
        description="Immich server root URL, e.g. https://photos.example.com",
    )
    endpoint: str | None = Field(
        default=None,
        description="Full API base URL (legacy alias); trailing /api is stripped for the SDK",
    )

    match: str = Field(..., description="Regex: which original filenames participate")
    parent: str = Field(..., description="Regex: which filename becomes stack parent")

    log_level: str = Field(default="INFO")
    compare_created: bool = Field(default=False)
    newer_than: str = Field(
        default="0h",
        description="Only assets with taken time newer than now minus this duration (s/m/h)",
    )
    insecure_tls: bool = Field(default=False)
    read_only: bool = Field(default=False)
    dry_run: bool = Field(default=False)

    scan_interval: str = Field(
        default="1h",
        description="Sleep between scans when not in once mode (e.g. 300s, 15m, 2h)",
    )
    once: bool = Field(
        default=False,
        description="If true, run a single scan and exit (cron-style)",
    )

    @field_validator("server_url", "endpoint", mode="before")
    @classmethod
    def _empty_str_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def _require_url(self) -> Settings:
        if self.server_url is None and self.endpoint is None:
            msg = "Set IMMICH_SERVER_URL and/or IMMICH_ENDPOINT (at least one)"
            raise ValueError(msg)
        return self

    @computed_field
    @property
    def immich_base_url(self) -> str:
        """Server root URL for clients that prefix paths with ``/api/...``."""

        if self.endpoint is not None:
            raw = self.endpoint.strip()
        elif self.server_url is not None:
            raw = str(self.server_url).strip()
        else:
            raw = ""
        return normalize_immich_base_url(raw)

    @computed_field
    @property
    def newer_than_delta(self) -> timedelta:
        return parse_immich_duration(self.newer_than)

    @computed_field
    @property
    def scan_interval_delta(self) -> timedelta:
        return parse_immich_duration(self.scan_interval)

    @computed_field
    @property
    def match_pattern(self) -> re.Pattern[str]:
        return re.compile(self.match)

    @computed_field
    @property
    def parent_pattern(self) -> re.Pattern[str]:
        return re.compile(self.parent)
