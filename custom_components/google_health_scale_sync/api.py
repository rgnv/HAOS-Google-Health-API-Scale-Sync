"""Google Health API v4 write client."""

from __future__ import annotations

import aiohttp
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .models import Measurement, body_fat_payload, weight_payload

BASE_URL = "https://health.googleapis.com/v4/users/me/dataTypes"


class GoogleHealthApiError(RuntimeError):
    """Raised when Google rejects a write."""


class GoogleHealthApi:
    """Write supported measurements using Home Assistant OAuth."""

    def __init__(self, websession: aiohttp.ClientSession, oauth_session: OAuth2Session) -> None:
        self.websession = websession
        self.oauth_session = oauth_session

    async def _post(self, data_type: str, payload: dict) -> dict:
        await self.oauth_session.async_ensure_token_valid()
        token = self.oauth_session.token.get("access_token")
        if not token:
            raise GoogleHealthApiError("Google OAuth session has no access token")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        url = f"{BASE_URL}/{data_type}/dataPoints"
        async with self.websession.post(url, json=payload, headers=headers) as response:
            if response.status >= 400:
                detail = await response.text()
                raise GoogleHealthApiError(f"Google Health API HTTP {response.status}: {detail}")
            if response.status == 204:
                return {"_http_status": response.status}
            result = await response.json()
            if not isinstance(result, dict):
                raise GoogleHealthApiError("Google Health API returned a non-object response")
            result["_http_status"] = response.status
            return result

    async def create_weight(self, measurement: Measurement) -> dict:
        """Create a weight data point."""
        return await self._post("weight", weight_payload(measurement))

    async def create_body_fat(self, measurement: Measurement) -> dict:
        """Create a body-fat data point."""
        return await self._post("body-fat", body_fat_payload(measurement))
