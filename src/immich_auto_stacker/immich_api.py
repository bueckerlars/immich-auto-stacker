"""HTTP access to Immich using immich-sdk models and a configurable TLS verify flag."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

import httpx
from immich_sdk.exception import ImmichHTTPError, ImmichValidationError
from immich_sdk.models import (
    AssetResponseDto,
    MetadataSearchDto,
    SearchResponseDto,
)
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential


def _server_version_display(payload: dict[str, Any]) -> str:
    """Format ``/api/server/version`` JSON for logging.

    Immich returns either a ``version`` string (older clients / OpenAPI) or
    ``major`` / ``minor`` / ``patch`` integers (current servers). The bundled
    ``ServerVersionResponseDto`` in immich-sdk only models the former.
    """

    ver = payload.get("version")
    if isinstance(ver, str) and ver.strip() != "":
        return ver.strip()
    try:
        major = payload["major"]
        minor = payload["minor"]
        patch = payload["patch"]
        return f"{major}.{minor}.{patch}"
    except KeyError:
        return str(payload)


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout))


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    body: str | bytes | None = resp.content
    message: str | None = None
    details: list[dict[str, object]] | None = None
    try:
        if resp.headers.get("content-type", "").startswith("application/json"):
            raw = resp.json()
            data = cast(dict[str, object], raw) if isinstance(raw, dict) else None
            if data is not None:
                msg: object = data.get("message") or data.get("error")
                message = str(msg) if msg is not None else None
                det: object = data.get("details")
                details = (
                    cast("list[dict[str, object]] | None", det)
                    if isinstance(det, list)
                    else None
                )
            body = resp.text
    except Exception:
        pass
    if resp.status_code == 422:
        raise ImmichValidationError(
            status_code=422,
            message=message or resp.text,
            details=details,
        )
    raise ImmichHTTPError(
        status_code=resp.status_code,
        message=message or resp.text,
        response_body=body,
    )


class ImmichApiClient:
    """Thin client: same paths as immich-sdk ``BaseClient``, with ``verify`` support."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        verify: bool = True,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._verify = verify
        self._timeout = timeout
        self._max_retries = max(1, max_retries)

    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self._api_key}

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"

        @retry(
            retry=retry_if_exception(_should_retry),
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        )
        def _do() -> httpx.Response:
            with httpx.Client(timeout=self._timeout, verify=self._verify) as client:
                resp = client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json_body,
                )
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError:
                    _raise_for_status(resp)
                return resp

        return _do()

    def get_server_version(self) -> str:
        """Return a short version string for logging (SDK DTO may not match server JSON)."""

        resp = self._request("GET", "/api/server/version")
        raw = resp.json()
        if isinstance(raw, dict):
            return _server_version_display(cast(dict[str, Any], raw))
        return str(raw)

    def get_asset_info(self, asset_id: str) -> AssetResponseDto:
        resp = self._request("GET", f"/api/assets/{asset_id}")
        return AssetResponseDto.model_validate(resp.json())

    def search_metadata(
        self,
        dto: MetadataSearchDto,
        *,
        taken_after: datetime | None,
    ) -> SearchResponseDto:
        payload: dict[str, Any] = dict(dto.model_dump(mode="json", exclude_none=True))
        if taken_after is not None:
            payload["takenAfter"] = taken_after.isoformat().replace("+00:00", "Z")
        resp = self._request("POST", "/api/search/metadata", json_body=payload)
        return SearchResponseDto.model_validate(resp.json())

    def create_stack(self, asset_ids: list[str]) -> None:
        """Create a stack; parent asset id must be first."""

        body = {"assetIds": asset_ids}
        self._request("POST", "/api/stacks", json_body=body)
