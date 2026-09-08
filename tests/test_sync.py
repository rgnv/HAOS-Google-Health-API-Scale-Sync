import asyncio
from datetime import datetime, timezone
from pathlib import Path

from ha_google_health_sync.models import Measurement
from ha_google_health_sync.store import SyncStore
from ha_google_health_sync.sync import sync_once


class FakeHomeAssistant:
    async def latest_measurement(self) -> Measurement:
        return Measurement(
            measurement_id="7",
            measured_at=datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc),
            weight_kg=80.0,
            body_fat_percent=20.0,
            source="test",
        )


class FakeGoogleHealth:
    def __init__(self) -> None:
        self.writes: list[str] = []

    async def create_weight(self, measurement: Measurement) -> dict:
        self.writes.append("weight")
        return {"name": "weight-point"}

    async def create_body_fat(self, measurement: Measurement) -> dict:
        self.writes.append("body_fat")
        return {"name": "body-fat-point"}


def test_sync_once_writes_each_metric_only_once(tmp_path: Path) -> None:
    async def run() -> None:
        store = SyncStore(tmp_path / "sync.sqlite3")
        google = FakeGoogleHealth()
        ha = FakeHomeAssistant()
        first = await sync_once(ha, google, store)
        second = await sync_once(ha, google, store)
        assert first["written"] == ["weight", "body_fat"]
        assert second["written"] == []
        assert google.writes == ["weight", "body_fat"]
        store.close()

    asyncio.run(run())
