"""Google OAuth token management."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.writeonly",
]


class TokenProvider:
    """Load and refresh a Google authorized-user token."""

    def __init__(self, token_file: Path) -> None:
        self.token_file = token_file
        self._credentials: Credentials | None = None

    def _load(self) -> Credentials:
        if self._credentials is None:
            if not self.token_file.exists():
                raise RuntimeError(
                    f"Google token file does not exist: {self.token_file}; run the auth command first"
                )
            self._credentials = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
        return self._credentials

    async def access_token(self) -> str:
        """Return a current access token, refreshing it when needed."""
        credentials = self._load()
        if not credentials.valid:
            if not credentials.refresh_token:
                raise RuntimeError("Google token has no refresh token; run auth again")
            await asyncio.to_thread(credentials.refresh, Request())
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            self.token_file.write_text(credentials.to_json() + "\n", encoding="utf-8")
        if not credentials.token:
            raise RuntimeError("Google OAuth did not return an access token")
        return credentials.token


def authenticate(client_secrets: Path, token_file: Path) -> None:
    """Run the one-time local browser OAuth flow."""
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
    credentials = flow.run_local_server(
        host=os.environ.get("OAUTH_BIND_HOST", "0.0.0.0"),
        port=int(os.environ.get("OAUTH_PORT", "8765")),
        access_type="offline",
        prompt="consent",
        open_browser=False,
    )
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(credentials.to_json() + "\n", encoding="utf-8")
    try:
        token_file.chmod(0o600)
    except PermissionError:
        pass
