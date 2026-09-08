"""Google Health API Scale Sync integration."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .api import GoogleHealthApi
from .const import DOMAIN
from .services import async_setup_services


@dataclass
class RuntimeData:
    """Runtime objects for one Google account."""

    api: GoogleHealthApi


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration domain."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Google Health API account."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
    oauth_session = OAuth2Session(hass, entry, implementation)
    entry.runtime_data = RuntimeData(
        api=GoogleHealthApi(aiohttp_client.async_get_clientsession(hass), oauth_session)
    )
    await async_setup_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Google Health API account."""
    return True
