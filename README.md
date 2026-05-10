# Raspberry Pi IoT & AI Teaching Platform

A modular, reusable, portable terminal for classroom IoT and AI demonstrations,
built on a Raspberry Pi 4B with the official 5" touchscreen.

## Quick start (for adults)

Students should follow the walkthrough on the [Pi IoT Academy
website](website/index.html). For anyone who just wants the commands:

```bash
# On a fresh Pi with Raspberry Pi OS 64-bit:
cd /opt/iot-platform
git clone <this repo> .
./scripts/bootstrap-pi.sh        # installs Docker, adds user to docker group
# (log out + back in for the group change)

cp .env.example .env
nano .env                         # set MQTT_PASSWORD; ANTHROPIC_API_KEY can wait
./scripts/bootstrap-mqtt-passwd.sh

docker compose up -d
docker compose ps
```

When all five containers report healthy:

| URL                                | What |
| ---                                | ---  |
| `http://<pi>/`                     | Vue placeholder dashboard |
| `http://<pi>:1880/`                | Node-RED |
| `http://<pi>:8000/health`          | API health check |
| `http://<pi>:8001/health`          | AI service health check |
| `mqtt://<pi>:1883` (auth required) | Mosquitto MQTT broker |

## Goals

- A single reusable platform, not a collection of one-off projects.
- Stable, portable, lightweight, and classroom-friendly.
- Modular: future modules (sensor hub, weather station, greenhouse monitor,
  bike dashboard, AI assistant) all reuse the same MQTT bus, FastAPI backend,
  SQLite store, and Vue frontend.
- Realistic for Raspberry Pi 4B hardware — no exotic peripherals in v1.

## Non-goals (v1)

- No SIM, LTE, SMS, or smartphone integration.
- No flexible/foldable displays or custom display drivers.
- No local AI inference — cloud APIs only (Claude as reference provider).
- No multi-arch container builds — arm64 only.

## Documents

| Document | Purpose |
| --- | --- |
| [`docs/architecture.md`](docs/architecture.md) | System architecture and Architecture Decision Records (ADRs). |
| [`docs/hardware-runbook.md`](docs/hardware-runbook.md) | Step-by-step Phase 1 hardware setup (SD card, OS, touchscreen, networking, power). |
| [`docs/folder-layout.md`](docs/folder-layout.md) | Target repository folder structure for code, modules, and infrastructure. |
| [`docs/mqtt-conventions.md`](docs/mqtt-conventions.md) | MQTT topic naming, payload schema, QoS, and retention rules. |
| [`docs/database-design.md`](docs/database-design.md) | SQLite schema, repository abstraction, and migration path to Postgres / TimescaleDB / InfluxDB. |
| [`docs/ai-integration.md`](docs/ai-integration.md) | Claude Haiku integration: user-triggered "Explain" button, prompt template, and persistence. |
| [`docs/implementation-plan.md`](docs/implementation-plan.md) | Phased delivery plan from hardware bring-up through to the first classroom module. |

## Status

| Phase | Title | Status |
| --- | --- | --- |
| 1 | Core device (hardware, OS, touchscreen) | Runbook ready |
| 2 | Core services (Docker, MQTT, Node-RED, FastAPI, Vue) | Built |
| 3 | MQTT core | Built |
| 4 | Database core | Built |
| 5 | Dashboard core | Built |
| 6 | AI API integration (Claude Haiku, "Explain" button) | Built |
| 7 | First module — Classroom Sensor Hub | Built |

## Working language

British English throughout (e.g. *colour*, *organise*, *behaviour*).
