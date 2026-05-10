# Raspberry Pi IoT & AI Teaching Platform

A modular, reusable, portable terminal for classroom IoT and AI demonstrations,
built on a Raspberry Pi 4B with the official 5" touchscreen.

This directory currently contains **planning and design documents only** — no
code yet. Implementation begins once the hardware runbook in
[`docs/hardware-runbook.md`](docs/hardware-runbook.md) has been completed and
the architecture is approved.

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
| [`docs/ai-integration.md`](docs/ai-integration.md) | Claude API integration, provider abstraction, prompt templating, and persistence. |
| [`docs/implementation-plan.md`](docs/implementation-plan.md) | Phased delivery plan from hardware bring-up through to the first classroom module. |

## Status

| Phase | Title | Status |
| --- | --- | --- |
| 1 | Core device (hardware, OS, touchscreen) | Planned — runbook ready |
| 2 | Core services (Docker, MQTT, Node-RED, FastAPI, Vue) | Planned |
| 3 | MQTT core | Planned |
| 4 | Database core | Planned |
| 5 | Dashboard core | Planned |
| 6 | AI API integration (Claude) | Planned |
| 7 | First module — Classroom Sensor Hub | Planned |

## Working language

British English throughout (e.g. *colour*, *organise*, *behaviour*).
