"""Config flow for Google Health API Scale Sync."""

from collections.abc import Mapping
from datetime import datetime
import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlowResult, OptionsFlow, SOURCE_REAUTH
from homeassistant.const import CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_AGE,
    CONF_BIRTH_DATE,
    CONF_HEIGHT_M,
    CONF_SEX,
    CONF_SYNC_BODY_FAT,
    DEFAULT_AGE,
    DEFAULT_HEIGHT_M,
    DEFAULT_SEX,
    DEFAULT_SYNC_BODY_FAT,
    DEFAULT_TITLE,
    DOMAIN,
    WRITE_SCOPE,
)

_LOGGER = logging.getLogger(__name__)

PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HEIGHT_M, default=DEFAULT_HEIGHT_M): vol.All(
            vol.Coerce(float), vol.Range(min=0.8, max=2.5)
        ),
        vol.Required(CONF_AGE, default=DEFAULT_AGE): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=120)
        ),
        vol.Required(CONF_SEX, default=DEFAULT_SEX): vol.In(
            {
                "male": "Male",
                "female": "Female",
                "unspecified": "Prefer not to say",
            }
        ),
        vol.Optional(
            CONF_BIRTH_DATE,
            default="",
        ): cv.string,
        vol.Required(CONF_SYNC_BODY_FAT, default=DEFAULT_SYNC_BODY_FAT): cv.boolean,
    }
)


def _profile_error(options: Mapping[str, Any]) -> str | None:
    """Validate profile fields that need a human-readable error."""
    birth_date = str(options.get(CONF_BIRTH_DATE, "")).strip()
    if birth_date:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", birth_date):
            return "invalid_birth_date"
        try:
            datetime.strptime(birth_date, "%Y-%m-%d")
        except ValueError:
            return "invalid_birth_date"
    return None


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle Google OAuth authorization and scale onboarding."""

    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Initialize the OAuth flow."""
        super().__init__()
        self._profile_options: dict[str, Any] = {}

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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the profile and sync options flow."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect profile settings before starting OAuth."""
        if user_input is not None:
            error = _profile_error(user_input)
            if error is None:
                self._profile_options = dict(user_input)
                return await self.async_step_pick_implementation()
            return self.async_show_form(
                step_id="user",
                data_schema=self.add_suggested_values_to_schema(
                    PROFILE_SCHEMA, user_input
                ),
                errors={"base": error},
            )

        suggested: Mapping[str, Any] = {}
        if self.source == SOURCE_REAUTH:
            suggested = self._get_reauth_entry().options
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(PROFILE_SCHEMA, suggested),
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Start reauthorization after an expired or revoked token."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthorization, then refresh profile settings."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create or update the entry after OAuth completes."""
        scopes = data.get(CONF_TOKEN, {}).get("scope", "").split()
        if WRITE_SCOPE not in scopes:
            return self.async_abort(reason="missing_write_scope")
        options = self._profile_options or {
            CONF_HEIGHT_M: DEFAULT_HEIGHT_M,
            CONF_AGE: DEFAULT_AGE,
            CONF_SEX: DEFAULT_SEX,
            CONF_BIRTH_DATE: "",
            CONF_SYNC_BODY_FAT: DEFAULT_SYNC_BODY_FAT,
        }
        if self.source == SOURCE_REAUTH:
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data=data, options=options
            )
        return self.async_create_entry(title=DEFAULT_TITLE, data=data, options=options)


class OptionsFlowHandler(OptionsFlow):
    """Handle profile and synchronization settings."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show and save profile settings."""
        if user_input is not None:
            error = _profile_error(user_input)
            if error is None:
                return self.async_create_entry(title="", data=user_input)
            return self.async_show_form(
                step_id="init",
                data_schema=self.add_suggested_values_to_schema(
                    PROFILE_SCHEMA, user_input
                ),
                errors={"base": error},
            )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                PROFILE_SCHEMA, self.config_entry.options
            ),
        )
