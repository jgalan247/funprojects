# Target folder layout

The shape `rpi-iot-platform/` will take when Phase 2 begins. Directories are
created on demand — don't pre-create them.

```
rpi-iot-platform/
├── README.md
├── docs/                              # Planning + design docs (this folder).
│
├── docker-compose.yml                 # Single-host orchestration, arm64.
├── .env.example                       # Committed example. Real .env is gitignored.
├── .gitignore
│
├── infra/                             # Service-specific config + Dockerfiles.
│   ├── mosquitto/
│   │   ├── mosquitto.conf
│   │   └── passwd                     # Generated, gitignored.
│   ├── node-red/
│   │   └── settings.js
│   ├── api/
│   │   └── Dockerfile
│   ├── ai/
│   │   └── Dockerfile
│   └── frontend/
│       ├── Dockerfile
│       └── nginx.conf
│
├── services/
│   ├── api/                           # FastAPI: REST + WebSocket for the UI.
│   │   ├── pyproject.toml
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── api/                   # HTTP routers.
│   │   │   │   ├── sensors.py
│   │   │   │   ├── modules.py
│   │   │   │   └── ai.py              # Thin proxy to the AI service.
│   │   │   ├── ws/                    # WebSocket handlers.
│   │   │   ├── mqtt/                  # MQTT subscriber bridge -> DB.
│   │   │   ├── db/
│   │   │   │   ├── engine.py
│   │   │   │   ├── models.py          # SQLAlchemy models.
│   │   │   │   ├── migrations/        # Alembic.
│   │   │   │   └── repositories/      # Per-aggregate repository classes.
│   │   │   │       ├── sensors.py
│   │   │   │       ├── readings.py
│   │   │   │       ├── ai_history.py
│   │   │   │       └── modules.py
│   │   │   └── services/              # Application-layer services.
│   │   └── tests/
│   │
│   ├── ai/                            # AI service: thin Claude wrapper.
│   │   ├── pyproject.toml
│   │   ├── app/
│   │   │   ├── main.py                # FastAPI app exposing POST /ai/explain.
│   │   │   ├── claude.py              # anthropic SDK call + retries.
│   │   │   ├── prompts/
│   │   │   │   └── explain-sensor-v1.md
│   │   │   └── persistence.py         # Writes ai_prompts / ai_responses.
│   │   └── tests/
│   │
│   └── ingest-bridge/                 # Optional: standalone MQTT->DB worker.
│       └── (folded into api/ unless we hit perf issues)
│
├── frontend/                          # Vue 3 + Vite + Tailwind.
│   ├── package.json
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router.ts
│   │   ├── api/                       # Typed clients for FastAPI.
│   │   ├── composables/               # useMqtt, useReadings, useAi, ...
│   │   ├── components/                # Reusable touch-friendly components.
│   │   │   ├── SensorCard.vue
│   │   │   ├── ModuleTile.vue
│   │   │   └── AiExplainer.vue
│   │   └── views/                     # Pages: Home, Modules, Settings, AI.
│   └── tests/
│
├── modules/                           # Self-contained classroom modules.
│   ├── classroom-sensor-hub/
│   │   ├── module.yaml                # Manifest read by the platform.
│   │   ├── flows.json                 # Optional Node-RED flows.
│   │   ├── frontend/                  # Optional Vue components contributed by the module.
│   │   └── README.md
│   └── (future modules ...)
│
├── flows/                             # Shared Node-RED flow exports.
│   └── core.json
│
├── scripts/
│   ├── bootstrap-pi.sh                # Phase 2 service install on a fresh Pi.
│   ├── reset-data.sh                  # Wipes ./data after confirmation.
│   └── publish-test-sensor.py         # Mock MQTT publisher for demos.
│
└── data/                              # Persistent volumes. Gitignored.
    ├── sqlite/
    │   └── platform.db
    ├── mosquitto/
    │   ├── data/
    │   └── log/
    └── node-red/
```

## Conventions

- **Snake_case** for Python modules, **kebab-case** for directories at repo
  level, **PascalCase** for Vue components.
- Every service has its own `Dockerfile` under `infra/<service>/` and its own
  source tree under `services/<service>/`. Dockerfiles do not live next to
  source — that keeps the source tree clean and lets `infra/` be reviewed
  separately when DevOps changes.
- **Modules** are self-contained: a module brings its own optional Node-RED
  flow, its own Vue components, and a `module.yaml` manifest. The platform
  reads manifests at startup and registers tiles on the home screen.
- **`data/` is sacred** — never committed, never auto-deleted by code. Reset
  is a deliberate, scripted action (`scripts/reset-data.sh`).

## What deliberately doesn't exist

- No `lib/` or `common/` mega-package. Shared code between Python services
  belongs in a small published wheel later, or simply duplicated until a real
  pattern emerges. Premature abstraction is worse than duplication for v1.
- No top-level `tests/` — tests live next to the service they test.
- No CI directory until we have CI; planned location is `.github/workflows/`.
