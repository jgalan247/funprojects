# Architecture

## 1. Purpose

A reusable, portable Raspberry Pi terminal for IoT and AI teaching. It serves
as classroom demo kit, STEM workshop tool, sensor monitor, and host for
multiple educational modules — all on the same software platform.

## 2. Principles

- **Modular over monolithic.** Every capability is an independent service that
  speaks MQTT or HTTP. Modules plug into the platform; the platform never
  hard-codes a module.
- **Reusable over reinvented.** Sensor hub, weather station, greenhouse, bike
  dashboard — all share the same MQTT bus, FastAPI backend, SQLite store, and
  Vue frontend.
- **Stability over novelty.** v1 prioritises boring, well-supported choices.
- **Touch-first UI.** The Vue frontend is designed for the official 5"
  touchscreen at typical classroom viewing distance.
- **Cloud AI, edge IoT.** The Pi is an IoT controller and dashboard server,
  not an inference machine.

## 3. Logical architecture

```
+---------------------+
|  Sensors / devices  |
|  (Micro:bit, ESP32, |
|   USB sensors, ...) |
+----------+----------+
           |
           | MQTT publish
           v
+----------+----------------+
|     Mosquitto (MQTT)      |
+----+-----------------+----+
     |                 |
     | subscribe       | subscribe
     v                 v
+----+--------+    +---+----------+        +-------------------+
|  Node-RED   |    |   FastAPI    |        |   Anthropic API   |
|  (automation|    |  (REST + WS) |        |    (Claude        |
|   admin UI, |    |              |        |     Haiku 4.5)    |
|   debug)    |    +---+----------+        +---------+---------+
+-------------+        |       \                     ^
                       |        \                    | HTTPS
                       v         \                   | (user-triggered)
                +------+-----+    \                  |
                |   SQLite   |     \      +----------+----------+
                | sensors,   |      ----->|     AI service      |
                | ai_prompts,|<-----------|  (Claude SDK,       |
                | logs, ...  |  persist   |   prompt log)       |
                +------+-----+            +---------------------+
                       |
                       v
              +--------+---------+
              |  Vue + Tailwind  |
              | (touchscreen UI, |
              |  module launcher,|
              |  "Explain" btn)  |
              +------------------+
```

## 4. Component responsibilities

| Component | Responsibility | Out of scope |
| --- | --- | --- |
| **Mosquitto** | Single MQTT broker, central pub/sub bus. | Persistence, business logic. |
| **Node-RED** | Automation flows, MQTT debugging, admin tooling, rapid prototyping. | The primary user-facing UI. |
| **FastAPI** | REST + WebSocket API for the Vue frontend; orchestrates DB, AI, and MQTT bridge. | Real-time sensor ingestion (that's MQTT). |
| **AI service** | Calls Claude Haiku via the `anthropic` SDK, renders the prompt template, persists prompt/response pairs, exposes a single `/ai/explain` REST endpoint. | Local inference. MQTT triggers. Multi-provider support. |
| **SQLite** | Durable storage for sensors, readings, devices, AI history, logs, modules registry. | High-frequency time-series (deferred to InfluxDB/Timescale if needed). |
| **Vue + Tailwind** | Touchscreen dashboard, module launcher, settings, AI explainer surfaces. | Automation flows (those live in Node-RED). |
| **Docker Compose** | Service orchestration, single-command bring-up, version pinning. | Multi-host orchestration (no k8s, no swarm). |

## 5. Architecture Decision Records (ADRs)

ADRs are intentionally short. Each captures a decision, the alternatives, and
the reasoning so future contributors don't relitigate them.

### ADR-001: SQLite for v1, behind a repository abstraction

- **Status:** Accepted.
- **Context:** v1 must run on a Pi 4B with constrained RAM and storage. Sensor
  volumes in classroom use are low (tens of readings/second peak).
- **Decision:** Use SQLite as the v1 database. All access goes through a
  repository layer (`app/db/repositories/*`) that exposes async methods. No
  raw SQL in business logic.
- **Alternatives considered:**
  - PostgreSQL — overkill for v1, more memory.
  - InfluxDB / TimescaleDB — better for high-volume time series, but heavier
    and unnecessary for classroom data rates.
- **Consequences:** A future migration to Postgres or Timescale changes the
  repository implementations only, not the call sites. See
  [`database-design.md`](database-design.md).

### ADR-002: MQTT as the central communication bus

- **Status:** Accepted.
- **Context:** Sensors (Micro:bit, ESP32) and modules need to communicate
  without tight coupling.
- **Decision:** Mosquitto is the single broker. All inter-service real-time
  communication goes via MQTT topics defined in
  [`mqtt-conventions.md`](mqtt-conventions.md). FastAPI exposes a thin REST/
  WebSocket layer for the Vue UI.
- **Alternatives considered:**
  - Direct WebSockets between sensors and FastAPI — couples sensors to one
    service, no decoupled fan-out.
  - HTTP polling — wasteful, latency-sensitive on a touchscreen.
- **Consequences:** Every new module becomes "publish to this topic, subscribe
  to that topic" — a pattern students can learn and reuse.

### ADR-003: Anthropic Claude only, Haiku as default model, user-triggered

- **Status:** Accepted.
- **Context:** Local LLM inference on a Pi 4B 8GB is slow and low quality.
  We need short, friendly explanations of single sensor readings, on demand,
  when a student or teacher taps a button.
- **Decision:**
  - Cloud AI only. **Anthropic Claude only**, no provider abstraction.
  - Default model: **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`).
    Cheap, fast, sufficient. Model ID lives in env, not code.
  - **User-triggered only.** The single trigger is the "Explain" button on
    a sensor card. No MQTT-driven AI flow, no automatic explanations.
- **Alternatives considered:**
  - Ollama on-device — too slow and too poor for this use case.
  - Multi-provider abstraction — hedges against a future we don't want; pure
    overhead for v1.
  - Opus / Sonnet defaults — overkill and ~15× the per-token cost vs Haiku
    for no audible improvement on 2–3 sentence explanations.
  - MQTT-triggered AI calls — adds complexity for no current use case.
- **Consequences:** The API key sits in env vars on the AI service only. If
  the key is missing, a deterministic stub takes over and the UI shows a
  banner — the platform never crashes from a missing key. See
  [`ai-integration.md`](ai-integration.md).

### ADR-004: Vue + Tailwind is the primary UI; Node-RED is automation/admin

- **Status:** Accepted.
- **Context:** Node-RED Dashboard is excellent for prototyping but constrained
  for touch-first classroom UX.
- **Decision:** Vue 3 (Composition API) + Vite + Tailwind is the main frontend
  served on the touchscreen. Node-RED remains for flows, MQTT debugging, and
  admin tasks but is not the student-facing UI.
- **Alternatives considered:**
  - Node-RED Dashboard as the only UI — limits visual design and reuse.
  - React — fine, but Vue's templating maps better to a simple component model
    for a small project and a single maintainer.
- **Consequences:** Early phases use Node-RED Dashboard heavily for speed;
  later phases progressively migrate UI into Vue.

### ADR-005: Docker Compose for orchestration

- **Status:** Accepted.
- **Context:** The platform runs ~5 services (Mosquitto, Node-RED, FastAPI,
  AI service, frontend). Bring-up must be one command for classroom use.
- **Decision:** A single `docker-compose.yml` at the repo root. Each service
  has a pinned image tag or a local Dockerfile. Volumes for SQLite, Mosquitto
  config, and Node-RED flows persist in `./data/`.
- **Alternatives considered:**
  - systemd units per service — works but harder to demonstrate to students
    and harder to reset.
  - Kubernetes / k3s — wildly disproportionate for one Pi.
- **Consequences:** Compose pins us to one host. That's fine for v1.

### ADR-006: arm64-only, no multi-arch builds

- **Status:** Accepted (per session decision).
- **Context:** Target hardware is exclusively a Pi 4B running 64-bit Raspberry
  Pi OS.
- **Decision:** Compose images and Dockerfiles target `linux/arm64`. No
  buildx, no manifest lists.
- **Consequences:** Slightly less convenient for laptop development. Any dev
  on amd64 must rely on a remote Pi or cross-build manually; this is accepted.

### ADR-007: Pi 4B 8GB + official 5" touchscreen, no exotic hardware in v1

- **Status:** Accepted.
- **Context:** v1 must be cheap, replaceable, well-documented, and stable for
  classroom use.
- **Decision:** Standardise on Pi 4B 8GB and the official Raspberry Pi 5"
  touchscreen. Optional add-ons (camera, microphone, speaker, GPS, sensor HAT)
  are deferred and addressed by future modules.
- **Consequences:** All UI design assumes the official 5" panel's resolution
  and DPI. Future modules that need bigger displays are out of scope.

### ADR-008: British English in documentation and UI copy

- **Status:** Accepted.
- **Context:** Target audience is a Jersey (Channel Islands) school.
- **Decision:** All written content uses British English spelling and idiom.

## 6. Cross-cutting concerns

- **Configuration:** All secrets and environment-specific values come from
  environment variables, loaded by Compose from a `.env` file that is **never**
  committed. A `.env.example` is committed.
- **Logging:** Each service logs to stdout in JSON; Compose collects.
  Long-term log retention is out of scope for v1.
- **Time:** All timestamps stored as UTC ISO-8601. The UI converts to local
  time at the edge.
- **Networking:** Services live on a private Compose network. Only the Vue
  frontend (port 80 / 8080) and Node-RED admin (port 1880, on LAN only) are
  exposed to the host.
- **Security:** v1 runs on a school LAN. MQTT auth is enabled (username +
  password) but TLS is deferred. SSH key-only after first boot.
