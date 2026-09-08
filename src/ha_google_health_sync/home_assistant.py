"""Small Home Assistant REST API reader."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import Measurement, parse_timestamp


class HomeAssistantApiError(RuntimeError):
    """Raised when Home Assistant state cannot be read."""


class HomeAssistantClient:
    """Read the measurement sensors from Home Assistant."""

    def __init__(
        self,
        base_url: str,
        token: str,
        measurement_id_entity: str,
        weight_entity: str,
        body_fat_entity: str | None,
        source: str,
        request_fn: Callable[..., dict] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.measurement_id_entity = measurement_id_entity
        self.weight_entity = weight_entity
        self.body_fat_entity = body_fat_entity
        self.source = source
        self._request_fn = request_fn or self._request

    def _request(self, entity_id: str) -> dict:
        request = Request(
            f"{self.base_url}/api/states/{entity_id}",
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise HomeAssistantApiError(f"Home Assistant HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise HomeAssistantApiError(f"Home Assistant connection failed: {exc.reason}") from exc

    async def get_state(self, entity_id: str) -> dict:
        """Read one state entity."""
        return await asyncio.to_thread(self._request_fn, entity_id)

    @staticmethod
    def _number(state: dict, label: str) -> float | None:
        value = state.get("state")
        if value in (None, "unknown", "unavailable", "none", ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise HomeAssistantApiError(f"{label} state is not numeric: {value!r}") from exc

    async def latest_measurement(self) -> Measurement | None:
        """Read a complete measurement, or return None while entities are unavailable."""
        id_state = await self.get_state(self.measurement_id_entity)
        measurement_id = id_state.get("state")
        if measurement_id in (None, "unknown", "unavailable", "none", ""):
            return None
        measured_at_value = id_state.get("last_changed") or id_state.get("last_updated")
        if not measured_at_value:
            raise HomeAssistantApiError("measurement ID state has no timestamp")
        measured_at = parse_timestamp(measured_at_value)

        weight_state = await self.get_state(self.weight_entity)
        weight_kg = self._number(weight_state, "weight")
        if weight_kg is None:
            return None

        body_fat_percent = None
        if self.body_fat_entity:
            fat_state = await self.get_state(self.body_fat_entity)
            body_fat_percent = self._number(fat_state, "body fat")

        return Measurement(
            measurement_id=str(measurement_id),
            measured_at=measured_at,
            weight_kg=weight_kg,
            body_fat_percent=body_fat_percent,
            source=self.source,
        )
