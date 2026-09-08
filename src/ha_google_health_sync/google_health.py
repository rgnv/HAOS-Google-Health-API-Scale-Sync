"""Minimal Google Health API v4 client for write-only measurements."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import Measurement, body_fat_payload, weight_payload

BASE_URL = "https://health.googleapis.com/v4/users/me/dataTypes"


class GoogleHealthApiError(RuntimeError):
    """Raised when Google Health API rejects a write."""


class GoogleHealthApi:
    """Write supported body measurements to Google Health API."""

    def __init__(self, token_provider: object, request_fn: Callable[..., dict] | None = None) -> None:
        self.token_provider = token_provider
        self._request_fn = request_fn or self._request

    @staticmethod
    def _request(url: str, token: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise GoogleHealthApiError(f"Google Health API HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise GoogleHealthApiError(f"Google Health API connection failed: {exc.reason}") from exc
        if not raw:
            return {}
        return json.loads(raw)

    async def _create(self, data_type: str, payload: dict) -> dict:
        token = await self.token_provider.access_token()
        return await asyncio.to_thread(
            self._request_fn,
            f"{BASE_URL}/{data_type}/dataPoints",
            token,
            payload,
        )

    async def create_weight(self, measurement: Measurement) -> dict:
        """Create a weight data point."""
        return await self._create("weight", weight_payload(measurement))

    async def create_body_fat(self, measurement: Measurement) -> dict:
        """Create a body-fat data point."""
        return await self._create("body-fat", body_fat_payload(measurement))
