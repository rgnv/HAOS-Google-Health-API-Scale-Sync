"""Command-line entry point."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from .auth import TokenProvider, authenticate
from .google_health import GoogleHealthApi
from .home_assistant import HomeAssistantClient
from .store import SyncStore
from .sync import sync_once


def _path_env(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser()


def _client() -> tuple[HomeAssistantClient, GoogleHealthApi, SyncStore]:
    ha_url = os.environ.get("HA_URL")
    ha_token = os.environ.get("HA_TOKEN")
    if not ha_url or not ha_token:
        raise SystemExit("HA_URL and HA_TOKEN are required")
    provider = TokenProvider(_path_env("GOOGLE_TOKEN_FILE", "/data/google-token.json"))
    home_assistant = HomeAssistantClient(
        base_url=ha_url,
        token=ha_token,
        measurement_id_entity=os.environ.get(
            "HA_MEASUREMENT_ID_ENTITY", "sensor.ge_fit_plus_ln_measurement_id"
        ),
        weight_entity=os.environ.get("HA_WEIGHT_ENTITY", "sensor.ge_fit_plus_ln_weight"),
        body_fat_entity=os.environ.get("HA_BODY_FAT_ENTITY", "sensor.ge_fit_plus_ln_body_fat"),
        source=os.environ.get("SYNC_SOURCE", "home-assistant"),
    )
    google_health = GoogleHealthApi(provider)
    store = SyncStore(_path_env("SYNC_DB", "/data/sync.sqlite3"))
    return home_assistant, google_health, store


def _auth() -> None:
    authenticate(
        _path_env("GOOGLE_CLIENT_SECRETS", "/data/client_secret.json"),
        _path_env("GOOGLE_TOKEN_FILE", "/data/google-token.json"),
    )
    print("Google authorization completed")


async def _sync_loop(interval: int) -> None:
    while True:
        home_assistant, google_health, store = _client()
        try:
            print(await sync_once(home_assistant, google_health, store), flush=True)
        finally:
            store.close()
        await asyncio.sleep(interval)


async def _sync_one() -> None:
    home_assistant, google_health, store = _client()
    try:
        print(await sync_once(home_assistant, google_health, store))
    finally:
        store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("auth", help="run one-time Google OAuth authorization")
    subparsers.add_parser("sync-once", help="sync the newest Home Assistant measurement")
    subparsers.add_parser("daemon", help="poll Home Assistant continuously")
    args = parser.parse_args()

    if args.command == "auth":
        _auth()
    elif args.command == "sync-once":
        asyncio.run(_sync_one())
    elif args.command == "daemon":
        interval = max(15, int(os.environ.get("POLL_SECONDS", "60")))
        asyncio.run(_sync_loop(interval))
