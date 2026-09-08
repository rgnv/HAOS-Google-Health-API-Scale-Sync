# Existing Google Health API implementations reviewed

This project was started after reviewing the available public options. The goal is to document the decision boundary, not to copy code from another project.

## Official Home Assistant integration

Home Assistant 2026.8 includes the [`google_health`](https://www.home-assistant.io/integrations/google_health/) integration. It reads Google Health cloud data into Home Assistant and exposes body sensors such as weight and body fat. It does not provide the HA-to-Google write action needed for a scale source that originates in Home Assistant.

## Community projects

- [`vinodmishra/ha-googlehealthscalesync`](https://github.com/vinodmishra/ha-googlehealthscalesync) is the closest match: a small HACS-style custom component that posts weight and body fat. At review time it had one star, no declared repository license, and no container deployment or durable per-metric deduplication.
- [`allenporter/python-google-health-api`](https://github.com/allenporter/python-google-health-api) is an asynchronous Python client library. It is useful reference material, but it is not a Home Assistant write integration.
- [`Google-Health-API/google-health-cli`](https://github.com/Google-Health-API/google-health-cli) is an official Google command-line tool for API exploration and authorization. It does not watch Home Assistant entities.

## Decision

Build a small independent MIT-licensed sidecar rather than fork or embed an existing project. The sidecar owns the HA REST polling loop, write-only Google OAuth scope, payload unit conversion, and SQLite dedupe state. This keeps the Google API dependency replaceable and avoids requiring a custom Home Assistant core patch.

The Google Fit REST API was not selected because Google says its APIs are supported only through the end of 2026 and recommends Google Health API for cloud integrations.
