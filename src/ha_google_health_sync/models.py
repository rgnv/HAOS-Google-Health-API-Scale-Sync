"""Data models and Google Health API payload construction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Measurement:
    """One completed Home Assistant measurement sequence."""

    measurement_id: str
    measured_at: datetime
    weight_kg: float
    body_fat_percent: float | None
    source: str

    @property
    def event_key(self) -> str:
        """Return a stable local key for this measurement."""
        return f"{self.source}:{self.measurement_id}:{self.measured_at.isoformat()}"


def parse_timestamp(value: str) -> datetime:
    """Parse an HA RFC-3339 timestamp and require timezone information."""
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("measurement timestamp must include a timezone")
    return parsed


def sample_time(measured_at: datetime) -> dict[str, str]:
    """Build the Google Health API ObservationSampleTime object."""
    if measured_at.tzinfo is None or measured_at.utcoffset() is None:
        raise ValueError("measurement timestamp must include a timezone")
    utc = measured_at.astimezone(timezone.utc)
    physical = utc.isoformat(timespec="seconds").replace("+00:00", "Z")
    offset_seconds = int(measured_at.utcoffset().total_seconds())
    return {"physicalTime": physical, "utcOffset": f"{offset_seconds}s"}


def validate_measurement(measurement: Measurement) -> None:
    """Reject values that should never reach the cloud API."""
    if not 5.0 <= measurement.weight_kg <= 300.0:
        raise ValueError("weight must be between 5 and 300 kg")
    if measurement.body_fat_percent is not None and not 0 <= measurement.body_fat_percent <= 100:
        raise ValueError("body fat must be between 0 and 100 percent")


def weight_payload(measurement: Measurement) -> dict[str, Any]:
    """Create a Google Health API weight data point payload."""
    validate_measurement(measurement)
    return {
        "weight": {
            "weightGrams": round(measurement.weight_kg * 1000.0, 3),
            "sampleTime": sample_time(measurement.measured_at),
        }
    }


def body_fat_payload(measurement: Measurement) -> dict[str, Any]:
    """Create a Google Health API body-fat data point payload."""
    validate_measurement(measurement)
    if measurement.body_fat_percent is None:
        raise ValueError("body fat is not present")
    return {
        "bodyFat": {
            "percentage": round(measurement.body_fat_percent, 3),
            "sampleTime": sample_time(measurement.measured_at),
        }
    }
