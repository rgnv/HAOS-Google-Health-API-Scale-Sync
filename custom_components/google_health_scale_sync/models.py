"""Google Health API measurement payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Measurement:
    """One Home Assistant body measurement."""

    weight_kg: float
    body_fat_percent: float | None
    measured_at: datetime
    measurement_id: str | None


def sample_time(value: datetime) -> dict[str, str]:
    """Build the Google Health API sample-time object."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("measured_at must include a timezone")
    utc = value.astimezone(timezone.utc)
    offset_seconds = int(value.utcoffset().total_seconds())
    return {
        "physicalTime": utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "utcOffset": f"{offset_seconds}s",
    }


def validate(measurement: Measurement) -> None:
    """Reject impossible values before sending them to Google."""
    if not 5.0 <= measurement.weight_kg <= 300.0:
        raise ValueError("weight_kg must be between 5 and 300")
    if measurement.body_fat_percent is not None and not 0 <= measurement.body_fat_percent <= 100:
        raise ValueError("body_fat_percent must be between 0 and 100")


def weight_payload(measurement: Measurement) -> dict[str, Any]:
    """Create a weight data-point payload."""
    validate(measurement)
    return {
        "weight": {
            "weightGrams": round(measurement.weight_kg * 1000.0, 3),
            "sampleTime": sample_time(measurement.measured_at),
        }
    }


def body_fat_payload(measurement: Measurement) -> dict[str, Any]:
    """Create a body-fat data-point payload."""
    validate(measurement)
    if measurement.body_fat_percent is None:
        raise ValueError("body_fat_percent is required")
    return {
        "bodyFat": {
            "percentage": round(measurement.body_fat_percent, 3),
            "sampleTime": sample_time(measurement.measured_at),
        }
    }
