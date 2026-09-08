# HAOS Google Health API Scale Sync

A small, self-hosted sidecar that reads body measurements from Home Assistant and writes supported metrics to the Google Health API. It is designed for cloud sync without an Android runtime.

## Scope

The initial release writes:

- `weight` from a Home Assistant weight sensor
- `body-fat` from an optional Home Assistant body-fat sensor

Other smart-scale values remain in Home Assistant until Google publishes a directly compatible data type and its units are validated. Health Connect is a separate on-device Android API and is not used by this project.

## Why this is separate from Home Assistant's built-in integration

Home Assistant 2026.8 includes a `Google Health` integration that reads cloud data into Home Assistant. This project adds the opposite direction: Home Assistant measurements to the Google Health API.

A small community custom component also exists for this use case. This project is independent, MIT-licensed, uses a sidecar rather than patching Home Assistant internals, and includes a durable deduplication store and container deployment.

## HACS installation

This repository includes a HACS-installable Home Assistant custom integration in `custom_components/google_health_scale_sync/`.

1. In HACS, open **Integrations** and choose **Custom repositories**.
2. Add this repository URL and select **Integration**.
3. Install **Google Health API Scale Sync** and restart Home Assistant.
4. Add the integration from **Settings → Devices & services → Add integration**.
5. Complete Google OAuth and grant the health-metrics write permission.
6. Import `blueprints/google_health_scale_sync_body_scale_logger.yaml` to trigger a write on each new measurement ID.

The sidecar CLI and the HACS integration use the same Google Health API data model. Use one write path for a given measurement source, not both.

## Architecture

```text
ESPHome scale device -> Home Assistant sensors -> this sidecar -> Google Health API v4
```

The sidecar polls the measurement-ID sensor. A new measurement ID is the event boundary, so equal consecutive weights are still distinct measurements. Each metric is deduplicated independently in SQLite so a transient body-fat failure does not cause a duplicate weight write on retry.

## Google Cloud setup

1. Create a Google Cloud project.
2. Enable the [Google Health API](https://console.cloud.google.com/apis/library/health.googleapis.com).
3. Configure the OAuth consent screen and add the Google account as a test user while the app is in testing mode.
4. Create OAuth credentials. A desktop client is the simplest choice for the one-time `auth` command; a web client with a loopback redirect also works.
5. Download the client-secrets JSON to a private host. Never commit it.
6. Request only the health-metrics write scope used by this project:

   ```text
   https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.writeonly
   ```

The API's write-only scope can create and manage data written by this client; it is not a substitute for read access to other sources. The HACS integration records the HTTP status for each data type in the Home Assistant log; a successful `204` response has an empty body and is still an accepted write. Read-back requires the separate readonly scope and an explicit reauthorization.

See the official [setup guide](https://developers.google.com/health/setup), [data types](https://developers.google.com/health/data-types), and [data point create method](https://developers.google.com/health/reference/rest/v4/users.dataTypes.dataPoints/create).

## Home Assistant prerequisites

The default entity IDs are intentionally generic and can be changed through environment variables:

- measurement ID: `sensor.ge_fit_plus_ln_measurement_id`
- weight: `sensor.ge_fit_plus_ln_weight`
- body fat: `sensor.ge_fit_plus_ln_body_fat` (optional)

The sidecar needs a Home Assistant long-lived access token with permission to read those entities. Keep that token in an environment file or container secret.

## Quick start with Docker Compose

Copy the example environment file and fill it with local values:

```bash
cp .env.example .env
```

Place the Google OAuth client-secrets file at the path configured by `GOOGLE_CLIENT_SECRETS`. The token file is created locally by the authentication step.

Run the one-time browser authorization:

```bash
docker compose --env-file .env -f compose.example.yaml run --rm sync auth
```

The OAuth callback is available at `http://127.0.0.1:8765/`. If the container host is remote, forward that port over SSH and open the printed authorization URL in your local browser:

```bash
ssh -N -L 8765:127.0.0.1:8765 user@container-host
```

Then test one synchronization pass:

```bash
docker compose --env-file .env -f compose.example.yaml run --rm sync sync-once
```

Run continuously:

```bash
docker compose --env-file .env -f compose.example.yaml up -d
```

The container is intentionally stateless except for the mounted token and SQLite directories. Back them up as private data; do not put either file in Git.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `HA_URL` | required | Home Assistant base URL |
| `HA_TOKEN` | required | Home Assistant long-lived access token |
| `HA_MEASUREMENT_ID_ENTITY` | `sensor.ge_fit_plus_ln_measurement_id` | Event boundary sensor |
| `HA_WEIGHT_ENTITY` | `sensor.ge_fit_plus_ln_weight` | Weight in kilograms |
| `HA_BODY_FAT_ENTITY` | `sensor.ge_fit_plus_ln_body_fat` | Optional body-fat percentage |
| `SYNC_SOURCE` | `home-assistant` | Stable source label in the local dedupe key |
| `POLL_SECONDS` | `60` | Daemon polling interval |
| `GOOGLE_CLIENT_SECRETS` | `/data/client_secret.json` | OAuth client-secrets file |
| `GOOGLE_TOKEN_FILE` | `/data/google-token.json` | OAuth token file |
| `SYNC_DB` | `/data/sync.sqlite3` | SQLite dedupe database |

## Data mapping

Google Health API payloads use grams for weight and percentage points for body fat. The sidecar converts kilograms to grams and uses the measurement-ID state's `last_changed` timestamp as the sample time.

| Home Assistant | Google Health API |
| --- | --- |
| weight in kg | `users/me/dataTypes/weight/dataPoints` / `weight.weightGrams` |
| body fat in % | `users/me/dataTypes/body-fat/dataPoints` / `bodyFat.percentage` |

## Security and privacy

- OAuth client secrets, refresh tokens, Home Assistant tokens, and SQLite state are local-only.
- The project contains no household names, device addresses, or personal health profiles.
- The sidecar requests write-only health-metrics permission and does not request broad read scopes.
- Use HTTPS for the Home Assistant URL when the sidecar is outside the trusted local network.

## Research notes

Google's migration guidance says the legacy Google Fit APIs, including REST, are supported only through the end of 2026 and recommends Google Health API for cloud integrations. Health Connect remains Android-only and device-centric. This sidecar therefore targets the supported cloud API directly.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m compileall src
pytest -q
```

## License

MIT. See [LICENSE](LICENSE).
