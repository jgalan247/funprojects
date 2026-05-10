# Implementation plan

Phased delivery from a clean Pi to a working classroom module. Each phase has
a single goal, hard exit criteria, and an estimated effort. Effort is
expressed in **focused half-days** (≈4 hours) for a single developer.

Don't skip phases. Don't merge two phases. The point of the gates is to keep
the platform stable as it grows.

## Phase 1 — Core device

| | |
| --- | --- |
| **Goal** | A stable, portable touchscreen Pi that boots reliably on USB-C battery. |
| **Effort** | 1–2 half-days. |
| **Runbook** | [`hardware-runbook.md`](hardware-runbook.md). |

**Exit criteria** — every box in `hardware-runbook.md` §10 is ticked.

## Phase 2 — Core services

| | |
| --- | --- |
| **Goal** | All platform services come up with `docker compose up -d` on the Pi. |
| **Effort** | 2–3 half-days. |

Tasks:

1. Create `rpi-iot-platform/docker-compose.yml` with services: `mosquitto`,
   `node-red`, `api`, `ai`, `frontend`. arm64 only.
2. Add minimal `infra/` configs (Mosquitto with auth enabled, Node-RED with
   default settings, nginx for the Vue build).
3. `services/api/` with FastAPI + a single `/health` route + SQLAlchemy +
   Alembic skeleton (no business endpoints yet).
4. `services/ai/` with FastAPI + a single `/health` route + the `echo`
   provider (Claude wired up but disabled until Phase 6).
5. `frontend/` with a Vite + Vue 3 + Tailwind app showing a placeholder home
   page.
6. `.env.example` committed; real `.env` ignored.
7. `scripts/bootstrap-pi.sh` installs Docker + Compose plugin on a fresh Pi.

**Exit criteria:**

- `docker compose ps` shows all five services healthy.
- `http://<pi>/` loads the Vue placeholder.
- `http://<pi>:1880/` shows Node-RED.
- `mosquitto_pub` / `mosquitto_sub` round-trips a message between two
  laptops on the LAN with auth.
- `curl http://<pi>:8000/health` and `:8001/health` return `{"status":"ok"}`.

## Phase 3 — MQTT core

| | |
| --- | --- |
| **Goal** | The bus is real: a test sensor publishes, the API stores, the dashboard renders. |
| **Effort** | 1–2 half-days. |

Tasks:

1. Implement the MQTT subscriber bridge in `services/api/app/mqtt/`.
   Subscribes to `+/sensor/+/+` with QoS 0; parses the v1 envelope; calls
   `ReadingsRepository.append`.
2. `scripts/publish-test-sensor.py` — a small async publisher that emits
   fake temperature/humidity at 1 Hz. Used for demos and CI.
3. Node-RED flow `flows/core.json` with debug nodes for `system/#` and
   `+/sensor/+/+`. Imported once, exported on change.
4. Vue: a single `SensorCard.vue` on the home page wired to a WebSocket
   from FastAPI that pushes the latest reading per sensor.

**Exit criteria:**

- Running `publish-test-sensor.py` from a laptop causes the Pi's home
  screen card to update within 1 second.
- Stopping the publisher leaves the card showing the last value with a
  visible "stale" badge after 30 s.
- Restarting Mosquitto does not crash any service (clients reconnect).

## Phase 4 — Database core

| | |
| --- | --- |
| **Goal** | Every reading is durable; the schema in [`database-design.md`](database-design.md) is real. |
| **Effort** | 1–2 half-days. |

Tasks:

1. First Alembic migration `0001_initial` covering all tables in
   [`database-design.md`](database-design.md) §2.
2. Repositories: `devices`, `sensors`, `readings`, `system_logs` (the rest
   come with later phases).
3. Auto-register devices and sensors on first reading (idempotent upsert in
   the MQTT bridge — keep the producer side dumb).
4. Nightly retention job (APScheduler in the API process) deleting
   `sensor_readings` older than 30 days.
5. `/api/sensors`, `/api/sensors/{id}/readings?limit=...` endpoints.

**Exit criteria:**

- Power-cycling the Pi loses no readings written before shutdown.
- `/api/sensors` lists every sensor that has ever published.
- Retention job runs at 03:00 and is observable in `system_logs`.

## Phase 5 — Dashboard core

| | |
| --- | --- |
| **Goal** | A polished Vue touchscreen UI that's pleasant to use in front of a class. |
| **Effort** | 3–4 half-days. |

Tasks:

1. Layout: top bar with platform status, sidebar with module tiles, main
   pane for the active module's view.
2. Components: `SensorCard`, `ModuleTile`, `LineChart` (Chart.js or
   ECharts; pick one and live with it), `MqttActivity`, `SettingsView`.
3. Navigation: Vue Router with `/`, `/modules`, `/settings`, `/about`.
4. Touch targets ≥ 48 px. Test with a finger on the actual 5" panel — no
   hover-only interactions.
5. Configure Chromium kiosk mode autostart (the Phase 1 deferred item).
6. Move any Node-RED Dashboard pages used during prototyping into Vue if
   they're now student-facing.

**Exit criteria:**

- Chromium boots full-screen into the dashboard with no chrome.
- All four pages render and all controls are reachable by touch.
- A class of 25 can stand 1.5 m away and read the active sensor card.

## Phase 6 — AI integration (Claude)

| | |
| --- | --- |
| **Goal** | The "Explain this" button works, costs are tracked, history is browsable. |
| **Effort** | 2–3 half-days. |
| **Design doc** | [`ai-integration.md`](ai-integration.md). |

Tasks:

1. Implement `providers/claude.py` using the `anthropic` SDK. Enable prompt
   caching on the system block.
2. Implement the `Provider` interface, the registry, and the retry helper.
3. Templates: `explain-sensors-v1.md`, `summarise-trend-v1.md`.
4. REST endpoint `/api/ai/explain` and MQTT `ai/request` subscriber both
   route through the same internal call.
5. `AiExplainer.vue` component on each sensor card: tap → 2-sentence
   explanation, with a "show prompt" debug toggle for teachers.
6. Persistence: prompts and responses written every call.
7. Cost view in `/settings`: weekly token usage, simple line chart.

**Exit criteria:**

- Tapping "Explain" on a sensor card returns a sensible Year 7 explanation
  in < 4 seconds at the 95th percentile.
- The API key being absent makes the platform fall back to the `echo`
  provider with a visible UI banner — no crashes.
- Every call appears in `ai_prompts` / `ai_responses` and is visible in the
  cost view.

## Phase 7 — First module: Classroom Sensor Hub

| | |
| --- | --- |
| **Goal** | A complete teachable module that a Year 7 class can use end-to-end. |
| **Effort** | 3–4 half-days. |

Tasks:

1. `modules/classroom-sensor-hub/module.yaml` manifest. Picked up at boot.
2. Optional Node-RED flow that simulates sensors when no Micro:bit is
   connected — useful for in-class demos and for testing.
3. Micro:bit MakeCode example program (publishes via `mqtt-microbit`
   bridge) committed under `modules/classroom-sensor-hub/microbit/`.
4. ESP32 example sketch (Arduino IDE) under `.../esp32/`.
5. Vue view: live readings, a 60-minute trend chart per sensor, an
   "Explain" button per card, a "Snapshot" button that captures the
   current readings into a saved snapshot for class discussion.
6. Lesson notes in `modules/classroom-sensor-hub/README.md`.

**Exit criteria:**

- A Year 7 student can, in one lesson:
  1. Flash a Micro:bit with the provided program.
  2. See its temperature appear on the Pi screen.
  3. Tap "Explain" and read a sentence about what the value means.
  4. Take a snapshot and discuss it with the class.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Power bank causes under-voltage warnings under load | Medium | Display flicker, SD corruption | Test in Phase 1 §6; reject inadequate banks early. |
| SQLite WAL corruption on hard power-off | Low | Data loss | WAL + `synchronous=NORMAL`; document the trade-off; nightly DB snapshot to a second file in `data/sqlite/backups/`. |
| Anthropic API outage in a live lesson | Low | "Explain" stops working | `echo` provider fallback + visible UI banner; lessons don't depend on AI as the critical path. |
| Wi-Fi unreliable in the classroom | Medium | No MQTT from Micro:bits | Pi can run a local Wi-Fi hotspot mode (Phase 5 stretch), Micro:bits join the Pi directly. |
| Scope creep (more modules, more features) | High | v1 never ships | Each module is post-Phase-7. No new ADRs without explicit review. |
| Vendor lock-in on Claude | Low | Cost / availability | Provider abstraction (Phase 6) means swapping vendors is a config change. |

## Out of scope for v1

To make these explicit so they don't drift in:

- Multi-user accounts, auth, or per-student profiles.
- Cloud sync of readings or AI history off-device.
- Offline AI / on-device inference.
- Mobile companion app.
- Multi-Pi clusters.
- TLS on MQTT (school LAN only for v1).
- CI/CD pipeline (added once code lands; not a v1 deliverable).
