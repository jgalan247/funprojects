# Database design

SQLite is the v1 store (see [ADR-001](architecture.md#adr-001-sqlite-for-v1-behind-a-repository-abstraction)).
This document defines the schema, the repository abstraction, and the path to
swap SQLite for PostgreSQL / TimescaleDB / InfluxDB later without rewriting
business logic.

## 1. File location

```
data/sqlite/platform.db
```

- Mounted into FastAPI and the AI service via Compose.
- WAL mode enabled (`PRAGMA journal_mode=WAL`) for concurrent reads.
- `PRAGMA foreign_keys=ON` set on every connection.
- `PRAGMA synchronous=NORMAL` is acceptable for v1; revisit if we see
  corruption on power loss (the portable use case makes this a real risk —
  document it but accept it for v1).

## 2. Tables

DDL is shown for clarity. The actual schema is created and managed by Alembic
migrations under `services/api/app/db/migrations/`.

### 2.1 `devices`

A physical or logical thing that publishes data — a Micro:bit, an ESP32, a
weather station head unit.

```sql
CREATE TABLE devices (
  id            TEXT PRIMARY KEY,            -- e.g. 'microbit-01'
  display_name  TEXT NOT NULL,
  kind          TEXT NOT NULL,               -- 'microbit' | 'esp32' | 'pi' | 'virtual' | ...
  module_id     TEXT REFERENCES modules(id) ON DELETE SET NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',  -- free-form JSON.
  created_at    TEXT NOT NULL,               -- ISO-8601 UTC.
  last_seen_at  TEXT
);
```

### 2.2 `sensors`

A single measurable channel on a device. `temperature` on `microbit-01` is a
sensor; so is `humidity` on the same device. This separation keeps readings
keyed by sensor, not by `(device, metric)` pairs.

```sql
CREATE TABLE sensors (
  id          TEXT PRIMARY KEY,              -- e.g. 'microbit-01.temperature'
  device_id   TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  metric      TEXT NOT NULL,                 -- 'temperature' | 'humidity' | 'moisture' | ...
  unit        TEXT NOT NULL,                 -- 'celsius' | 'percent' | 'pascal' | ...
  topic       TEXT NOT NULL UNIQUE,          -- MQTT topic this sensor publishes on.
  display_name TEXT,
  created_at  TEXT NOT NULL,
  UNIQUE (device_id, metric)
);
```

### 2.3 `sensor_readings`

The hot path. Append-only.

```sql
CREATE TABLE sensor_readings (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  sensor_id   TEXT NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
  ts          TEXT NOT NULL,                 -- ISO-8601 UTC, ms precision.
  value       REAL NOT NULL,
  quality     TEXT NOT NULL DEFAULT 'good'   -- 'good' | 'stale' | 'suspect' | 'error'
);

CREATE INDEX ix_sensor_readings_sensor_ts
  ON sensor_readings (sensor_id, ts DESC);
```

The `(sensor_id, ts DESC)` index covers the most common query: "give me the
last N readings for this sensor for the dashboard graph".

**Retention.** A nightly job (Phase 4) deletes rows older than 30 days from
`sensor_readings`. Anything older that matters can be aggregated into a
`sensor_readings_daily` rollup; deferred until needed.

### 2.4 `ai_prompts` and `ai_responses`

Two tables, joined by `prompt_id`. We keep them separate so that retrying a
prompt against a different provider doesn't duplicate the prompt content.

```sql
CREATE TABLE ai_prompts (
  id            TEXT PRIMARY KEY,            -- ULID.
  template_id   TEXT NOT NULL,               -- e.g. 'explain-sensors-v1'
  context_json  TEXT NOT NULL,               -- JSON of the prompt context.
  rendered_text TEXT NOT NULL,               -- Final prompt sent to the model.
  created_at    TEXT NOT NULL
);

CREATE TABLE ai_responses (
  id            TEXT PRIMARY KEY,            -- ULID.
  prompt_id     TEXT NOT NULL REFERENCES ai_prompts(id) ON DELETE CASCADE,
  provider      TEXT NOT NULL,               -- 'claude' | 'openai' | ...
  model         TEXT NOT NULL,
  text          TEXT NOT NULL,
  input_tokens  INTEGER,
  output_tokens INTEGER,
  latency_ms    INTEGER,
  status        TEXT NOT NULL,               -- 'ok' | 'error' | 'timeout'
  error         TEXT,
  created_at    TEXT NOT NULL
);

CREATE INDEX ix_ai_responses_prompt ON ai_responses (prompt_id);
```

### 2.5 `modules`

The registry of installed modules. Populated from `module.yaml` manifests at
startup.

```sql
CREATE TABLE modules (
  id            TEXT PRIMARY KEY,            -- 'classroom-sensor-hub'
  display_name  TEXT NOT NULL,
  version       TEXT NOT NULL,
  description   TEXT,
  enabled       INTEGER NOT NULL DEFAULT 1,
  manifest_json TEXT NOT NULL,
  installed_at  TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);
```

### 2.6 `system_logs`

Structured platform events — module starts, config changes, AI errors,
operator actions. Not a replacement for stdout logs.

```sql
CREATE TABLE system_logs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ts            TEXT NOT NULL,
  level         TEXT NOT NULL,               -- 'info' | 'warn' | 'error'
  source        TEXT NOT NULL,               -- service / component name.
  event         TEXT NOT NULL,               -- short event code.
  detail_json   TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX ix_system_logs_ts ON system_logs (ts DESC);
```

## 3. Repository abstraction

Business code never touches `sqlite3`, never writes raw SQL, and never imports
SQLAlchemy directly. It uses repository classes:

```
services/api/app/db/
  engine.py           # SQLAlchemy async engine factory.
  models.py           # ORM models mirroring §2.
  repositories/
    base.py           # Generic Repository[T] with get/list/upsert/delete.
    devices.py
    sensors.py
    readings.py
    ai_history.py
    modules.py
    system_logs.py
```

Each repository takes an `AsyncSession` in its constructor and exposes
**intent-named** methods, not CRUD-named methods. Examples:

```python
class ReadingsRepository:
    async def append(self, sensor_id: str, ts: datetime, value: float,
                     quality: str = "good") -> None: ...

    async def latest_for_sensor(self, sensor_id: str, limit: int = 50
                                ) -> list[Reading]: ...

    async def latest_per_sensor(self, device_id: str) -> dict[str, Reading]: ...

    async def delete_older_than(self, cutoff: datetime) -> int: ...
```

This is the seam that makes the storage layer swappable.

## 4. Migrations

- **Tool:** Alembic.
- **Location:** `services/api/app/db/migrations/`.
- **Policy:** Forward-only. We don't keep `downgrade()` bodies for v1 — they
  encourage destructive recovery paths and we have backups.
- **Naming:** `0001_initial.py`, `0002_add_modules.py`, etc. Sequential
  integers, not timestamps. Easier to read in PRs.

## 5. Migration path off SQLite (when, not if)

Triggers that would force a migration:

- More than ~50 readings/second sustained (SQLite handles bursts but write
  amplification under WAL becomes a tax).
- Need for time-bucket queries that are awkward in SQLite (`time_bucket`,
  continuous aggregates, retention policies).
- Need for multi-host access.

Target depending on trigger:

| Trigger | Target | Why |
| --- | --- | --- |
| Multi-host / multi-Pi deployments | PostgreSQL | General-purpose, easy ops. |
| Heavy time-series / aggregate queries | TimescaleDB (Postgres extension) | Same SQL, time-aware features. |
| Massive append-only sensor volume | InfluxDB | Built for this; pay the operational cost. |

Because business code only sees repositories, the swap is:

1. Add a new SQLAlchemy engine config (or InfluxDB client) under `engine.py`.
2. Add a parallel set of repository implementations.
3. Toggle via env var `DB_BACKEND=sqlite|postgres|timescale`.
4. Run a one-off export → import script (sketch lives in `scripts/` when we
   need it; not pre-built).

No router, no service, no Vue code changes.

## 6. What we deliberately don't store

- Raw MQTT payloads. We extract what we need at ingest; the broker is the
  source of truth for in-flight messages.
- Per-user data. v1 has no user accounts.
- Long-lived audit trails for compliance. Out of scope.
