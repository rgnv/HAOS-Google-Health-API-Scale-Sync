"""Durable per-metric deduplication store."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class SyncStore:
    """Store successful Google data-point writes."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS synced (metric_key TEXT PRIMARY KEY, data_point_name TEXT, synced_at TEXT NOT NULL)"
        )
        self._connection.commit()

    def has(self, metric_key: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM synced WHERE metric_key = ?", (metric_key,)
        ).fetchone()
        return row is not None

    def mark(self, metric_key: str, data_point_name: str | None) -> None:
        self._connection.execute(
            "INSERT OR IGNORE INTO synced(metric_key, data_point_name, synced_at) VALUES (?, ?, ?)",
            (metric_key, data_point_name, datetime.now(timezone.utc).isoformat()),
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()
