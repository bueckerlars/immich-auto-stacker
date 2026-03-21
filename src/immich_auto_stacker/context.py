"""Composition root: wire settings and the Immich API client once at startup."""

from __future__ import annotations

from immich_auto_stacker.immich_api import ImmichApiClient
from immich_auto_stacker.settings import Settings


class ApplicationContext:
    """Single place where dependencies are constructed."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._api = ImmichApiClient(
            settings.immich_base_url,
            settings.api_key.get_secret_value(),
            verify=not settings.insecure_tls,
        )

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def api(self) -> ImmichApiClient:
        return self._api
