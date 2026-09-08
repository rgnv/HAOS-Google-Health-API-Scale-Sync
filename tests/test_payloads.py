from datetime import datetime, timezone, timedelta

from ha_google_health_sync.models import Measurement, body_fat_payload, sample_time, weight_payload


def measurement() -> Measurement:
    return Measurement(
        measurement_id="42",
        measured_at=datetime(2026, 9, 8, 12, 34, 56, tzinfo=timezone(timedelta(hours=-7))),
        weight_kg=82.44,
        body_fat_percent=21.5,
        source="test",
    )


def test_sample_time_preserves_physical_time_and_offset() -> None:
    assert sample_time(measurement().measured_at) == {
        "physicalTime": "2026-09-08T19:34:56Z",
        "utcOffset": "-25200s",
    }


def test_weight_payload_uses_grams() -> None:
    assert weight_payload(measurement()) == {
        "weight": {
            "weightGrams": 82440.0,
            "sampleTime": {
                "physicalTime": "2026-09-08T19:34:56Z",
                "utcOffset": "-25200s",
            },
        }
    }


def test_body_fat_payload_uses_percentage_points() -> None:
    assert body_fat_payload(measurement())["bodyFat"]["percentage"] == 21.5
