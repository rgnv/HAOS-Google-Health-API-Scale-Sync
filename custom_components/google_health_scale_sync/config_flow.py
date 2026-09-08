"""Config flow for Google Health API Scale Sync."""

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.config_entries import ConfigFlowResult, SOURCE_REAUTH
from homeassistant.const import CONF_TOKEN
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DEFAULT_TITLE, DOMAIN, WRITE_SCOPE

_LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle Google OAuth authorization."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return the config-flow logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Request only the write scope required by this integration."""
        return {
            "scope": WRITE_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Start reauthorization after an expired or revoked token."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthorization."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create the config entry after OAuth completes."""
        scopes = data.get(CONF_TOKEN, {}).get("scope", "").split()
        if WRITE_SCOPE not in scopes:
            return self.async_abort(reason="missing_write_scope")
        if self.source == SOURCE_REAUTH:
            return self.async_update_reload_and_abort(self._get_reauth_entry(), data=data)
        return self.async_create_entry(title=DEFAULT_TITLE, data=data)
