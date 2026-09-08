"""Home Assistant actions for Google Health API Scale Sync."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_BODY_FAT_PERCENT,
    ATTR_ENTRY_ID,
    ATTR_MEASURED_AT,
    ATTR_MEASUREMENT_ID,
    ATTR_WEIGHT_KG,
    DOMAIN,
    SERVICE_LOG_BODY_MEASUREMENTS,
)
from .models import Measurement

_LOGGER = logging.getLogger(__name__)
SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_WEIGHT_KG): vol.All(vol.Coerce(float), vol.Range(min=5, max=300)),
        vol.Optional(ATTR_BODY_FAT_PERCENT): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
        vol.Optional(ATTR_MEASURED_AT): cv.datetime,
        vol.Optional(ATTR_MEASUREMENT_ID): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)


def _entries(hass: HomeAssistant) -> list[Any]:
    return hass.config_entries.async_entries(DOMAIN)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register the body-measurement action once."""
    if hass.services.has_service(DOMAIN, SERVICE_LOG_BODY_MEASUREMENTS):
        return

    async def log_body_measurements(call: ServiceCall) -> None:
        entries = _entries(hass)
        if not entries:
            raise HomeAssistantError("No Google Health API Scale Sync entry is configured")
        requested_entry_id = call.data.get(ATTR_ENTRY_ID)
        entry = next((item for item in entries if item.entry_id == requested_entry_id), None)
        if requested_entry_id and entry is None:
            raise HomeAssistantError(f"Unknown entry_id: {requested_entry_id}")
        entry = entry or entries[0]
        runtime = getattr(entry, "runtime_data", None)
        if runtime is None:
            raise HomeAssistantError("Google Health API Scale Sync is not ready")

        measured_at = call.data.get(ATTR_MEASURED_AT, dt_util.utcnow())
        if not isinstance(measured_at, datetime):
            raise HomeAssistantError("measured_at must be a datetime")
        measurement = Measurement(
            weight_kg=float(call.data[ATTR_WEIGHT_KG]),
            body_fat_percent=(
                float(call.data[ATTR_BODY_FAT_PERCENT])
                if ATTR_BODY_FAT_PERCENT in call.data
                else None
            ),
            measured_at=measured_at,
            measurement_id=call.data.get(ATTR_MEASUREMENT_ID),
        )
        weight_response = await runtime.api.create_weight(measurement)
        fat_response = None
        if measurement.body_fat_percent is not None:
            fat_response = await runtime.api.create_body_fat(measurement)
        _LOGGER.info(
            "Wrote Google Health measurement%s (weight=%s, body_fat=%s)",
            f" {measurement.measurement_id}" if measurement.measurement_id else "",
            weight_response.get("name"),
            fat_response.get("name") if fat_response else None,
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_LOG_BODY_MEASUREMENTS,
        log_body_measurements,
        schema=SERVICE_SCHEMA,
    )
