"""Measurement synchronization orchestration."""

from __future__ import annotations

from typing import Any

from .google_health import GoogleHealthApi
from .home_assistant import HomeAssistantClient
from .store import SyncStore


async def sync_once(
    home_assistant: HomeAssistantClient,
    google_health: GoogleHealthApi,
    store: SyncStore,
) -> dict[str, Any]:
    """Synchronize the newest HA measurement, preserving per-metric idempotency."""
    measurement = await home_assistant.latest_measurement()
    if measurement is None:
        return {"status": "not_ready", "written": []}

    written: list[str] = []
    weight_key = f"{measurement.event_key}:weight"
    if not store.has(weight_key):
        response = await google_health.create_weight(measurement)
        store.mark(weight_key, response.get("name"))
        written.append("weight")

    if measurement.body_fat_percent is not None:
        fat_key = f"{measurement.event_key}:body_fat"
        if not store.has(fat_key):
            response = await google_health.create_body_fat(measurement)
            store.mark(fat_key, response.get("name"))
            written.append("body_fat")

    return {
        "status": "ok",
        "measurement_id": measurement.measurement_id,
        "event_key": measurement.event_key,
        "written": written,
    }
