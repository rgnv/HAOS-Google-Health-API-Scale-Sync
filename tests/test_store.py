from pathlib import Path

from ha_google_health_sync.store import SyncStore


def test_store_is_idempotent(tmp_path: Path) -> None:
    store = SyncStore(tmp_path / "sync.sqlite3")
    assert not store.has("event:weight")
    store.mark("event:weight", "users/1/dataTypes/weight/dataPoints/2")
    store.mark("event:weight", "users/1/dataTypes/weight/dataPoints/3")
    assert store.has("event:weight")
    store.close()
