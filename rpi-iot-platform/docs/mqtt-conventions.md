# MQTT conventions

Mosquitto is the only broker. Every service that wants to talk to another
service in real time goes through it. This document is binding for v1.

## 1. Topic structure

```
<domain>/<entity>/<id>/<measurement-or-action>
```

- All segments **lowercase**, **kebab-case**, ASCII only.
- No spaces, no leading/trailing slashes, no `+` or `#` in publish topics.
- Maximum five segments. If you need more, you've modelled it wrong.

### 1.1 Reserved domains

| Domain | Purpose |
| --- | --- |
| `classroom/` | Classroom sensor hub readings (the first module). |
| `weather/` | Weather station module. |
| `greenhouse/` | Greenhouse / soil module. |
| `bike/` | Bike dashboard module. |
| `system/` | Platform health, status, audit. |
| `module/` | Module lifecycle (registered, started, stopped). |
| `dev/` | Development / scratch — never read by production code. |

A new domain requires updating this table and the
[`architecture.md`](architecture.md) ADR list if it's structurally novel.

### 1.2 Examples

| Topic | Direction | Notes |
| --- | --- | --- |
| `classroom/sensor/microbit-01/temperature` | sensor → broker | Single reading. |
| `classroom/sensor/microbit-01/humidity`    | sensor → broker | |
| `greenhouse/soil/probe-a/moisture`         | sensor → broker | |
| `weather/station/main/pressure`            | sensor → broker | |
| `system/status/api`                        | service → broker | Heartbeat. |
| `system/status/mosquitto`                  | broker → broker | Mosquitto's own `$SYS` is separate. |
| `module/lifecycle/sensor-hub`              | service → broker | Module up/down. |

## 2. Payload schema

All payloads are **UTF-8 JSON**. Binary payloads are not allowed in v1.

Every payload includes:

```json
{
  "ts": "2026-05-10T13:45:12.123Z",
  "source": "microbit-01",
  "schema": "v1",
  "data": { ... }
}
```

| Field | Required | Notes |
| --- | --- | --- |
| `ts` | yes | ISO-8601 UTC, millisecond precision. |
| `source` | yes | Stable device or service identifier. |
| `schema` | yes | Payload schema version, currently `v1`. Bump when shape changes. |
| `data`   | yes | The actual payload — shape depends on the topic. |

### 2.1 Sensor reading shape

```json
{
  "ts": "2026-05-10T13:45:12.123Z",
  "source": "microbit-01",
  "schema": "v1",
  "data": {
    "value": 24.3,
    "unit": "celsius",
    "quality": "good"
  }
}
```

- `unit` uses lowercase SI names: `celsius`, `pascal`, `percent`,
  `metres-per-second`, `lux`, `ppm`. No symbols (`°C`, `%`).
- `quality` is one of `good`, `stale`, `suspect`, `error`. Defaults to `good`.

> **AI is not on the bus.** The "Explain" feature is user-triggered and goes
> over HTTP only (see [`ai-integration.md`](ai-integration.md)). MQTT carries
> sensor data and platform status — nothing else.

## 3. QoS and retention

| Use case | QoS | Retained? |
| --- | --- | --- |
| High-frequency sensor readings | 0 | No |
| Critical alerts (e.g. `system/alert/*`) | 1 | No |
| Last-known status (`system/status/*`, `module/lifecycle/*`) | 1 | **Yes** |

Rule of thumb: **retained = "the latest value belongs on the dashboard the
moment it loads"**. Anything ephemeral or high-volume is not retained.

## 4. Wildcards (subscribers only)

- `+` matches one segment.
- `#` matches the rest of the topic.

Common subscriber patterns:

| Pattern | Used by |
| --- | --- |
| `classroom/sensor/+/+` | Sensor hub backend, Vue dashboard. |
| `+/sensor/+/+` | Cross-module sensor view. |
| `system/#` | Admin / Node-RED debug flows. |

## 5. Authentication and ACLs

v1:

- Mosquitto runs with `allow_anonymous false`.
- One credential per service (`api`, `ai`, `node-red`) and one shared
  classroom credential for student devices (Micro:bit / ESP32).
- Passwords come from `.env` and are written to `infra/mosquitto/passwd` by
  a one-shot bootstrap script.
- ACLs (when added in Phase 3): students can publish only under their domain
  (e.g. `classroom/#`), services can subscribe broadly.
- TLS is **deferred**. The platform runs on a school LAN. Add TLS the moment
  any traffic leaves the LAN.

## 6. Client IDs

`<service>-<instance>-<short-uuid>`, e.g. `api-1-7f2a`. Static IDs cause
"client took over my session" disconnect storms — never use a fixed client ID
across multiple instances.

## 7. Anti-patterns

- ❌ Embedding JSON in the topic (`classroom/sensor/{"id":"x"}`).
- ❌ Using `#` in a publish topic.
- ❌ Mixing measurement and identity (`classroom/temperature/microbit-01`)
  — keep identity before measurement.
- ❌ Publishing without `ts` and `schema` — every consumer assumes both.
- ❌ Sending unit-less numeric values. Always include `unit`.
- ❌ Reusing one topic for many measurements (`classroom/sensor/microbit-01`
  carrying everything). One topic per measurement.
