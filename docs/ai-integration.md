# AI integration

The AI service explains sensor data and IoT concepts in language a Year 7
student understands. It is a **separate** service from the main API — that
keeps API key handling, rate limiting, and prompt logic in one place.

## 1. Provider strategy

- **Reference provider: Anthropic Claude** (see
  [ADR-003](architecture.md#adr-003-cloud-ai-apis-over-local-inference-claude-is-the-reference)).
- All access goes through a `Provider` interface (§3) so OpenAI, Gemini, or
  any other vendor can be added without touching call sites.
- **No local inference.** Don't entertain Ollama in v1.

## 2. Default model

```
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-opus-4-7         # Latest Opus at time of writing.
ANTHROPIC_MAX_OUTPUT_TOKENS=512
ANTHROPIC_TIMEOUT_S=20
```

Model ID lives in env, not in code, so we can move to `claude-sonnet-4-6` for
cost reasons or to a newer model without a deploy.

## 3. Provider interface

```python
# services/ai/app/providers/base.py

from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class CompletionRequest:
    system: str
    user: str
    max_output_tokens: int = 512
    temperature: float = 0.3

@dataclass(frozen=True)
class CompletionResult:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str
    latency_ms: int

class Provider(Protocol):
    name: str
    async def complete(self, req: CompletionRequest) -> CompletionResult: ...
```

Implementations:

- `providers/claude.py` — uses the `anthropic` SDK with prompt caching on the
  system prompt (templates rarely change; `cache_control` saves cost).
- `providers/echo.py` — returns a deterministic stub for tests and demos when
  the API key is absent. Selected automatically when `ANTHROPIC_API_KEY` is
  unset; never used in production.

## 4. Prompt templates

Templates are versioned files under `services/ai/app/prompts/`:

```
prompts/
  explain-sensors-v1.md
  summarise-trend-v1.md
  generate-question-v1.md
```

Each template has:

- a YAML front-matter block (id, audience, expected variables, model overrides),
- a system section,
- a user section with `{{ variable }}` placeholders rendered by Jinja2 with
  autoescape disabled (we're rendering plain text, not HTML).

Example — `explain-sensors-v1.md`:

```markdown
---
id: explain-sensors-v1
audience: year-7
required: [readings, audience]
---

## system
You are a friendly science teacher explaining sensor readings to
{{ audience }} students. Use British English. Be concise (2–3 sentences),
concrete, and avoid jargon. Never invent values. If a reading looks
unusual, say so plainly.

## user
Here are the latest readings:
{% for r in readings -%}
- {{ r.metric }}: {{ r.value }} {{ r.unit }} (from {{ r.source }})
{% endfor %}

Explain what the readings mean and whether anything looks unusual.
```

Templates are content. Loading them at startup and validating the front
matter is part of the AI service boot sequence — a malformed template should
fail boot loudly, not at request time.

## 5. Request flow

Two entry points; same path through the service.

### 5.1 REST (UI-driven)

```
Vue component
  → POST /api/ai/explain        (FastAPI proxy)
  → POST /ai/complete           (AI service)
  → ProviderRegistry.select()   (Claude by default)
  → Provider.complete()
  → persistence.save_prompt_response()
  → return {text, correlation_id, ...}
```

### 5.2 MQTT (event-driven)

```
publisher
  → publish ai/request          (JSON, includes correlation_id)
  → AI service subscriber
  → render template
  → Provider.complete()
  → persistence.save_prompt_response()
  → publish ai/response/<correlation_id>
```

Either path persists the prompt and response in `ai_prompts` /
`ai_responses` (see [`database-design.md`](database-design.md)).

## 6. Persistence

Every completion produces:

1. One `ai_prompts` row (rendered text + context that produced it).
2. One `ai_responses` row (provider, model, text, tokens, latency, status).

This is non-negotiable. The history view, cost tracking, and "show me what we
asked the model" debug surface all read from these tables.

## 7. Failure handling

| Failure | Behaviour |
| --- | --- |
| Missing API key at boot | Service starts, `echo` provider takes over, log a warning. UI shows a banner. |
| Provider HTTP 429 / 5xx | Retry with exponential backoff, max 3 attempts, then return `status=error`. |
| Provider timeout (`ANTHROPIC_TIMEOUT_S`) | One retry, then `status=timeout`. |
| Template render error | Fail closed: don't call the provider, log to `system_logs`, return 500 to caller. |
| Output exceeds `max_output_tokens` | Truncate is acceptable; the UI shows a "cut off" hint. |

Retries go through one place (`providers/_retry.py`), not in every provider.

## 8. Cost control

- **Cache the system section** of each template using Anthropic's prompt
  cache (`cache_control: {type: "ephemeral"}` on the system block). System
  text is constant per template, so this turns most calls into cache hits and
  cuts cost meaningfully.
- **Cap `max_output_tokens`** at 512 by default. Classroom explanations don't
  need more.
- **Throttle**: a per-process semaphore of 4 concurrent requests is enough
  for a Pi 4B. Anything more piles up.
- **Log token usage** to `ai_responses.input_tokens` / `output_tokens`. A
  weekly tally query lives in the Phase 6 admin view.

## 9. Security and secrets

- API keys are loaded from environment variables via Pydantic settings.
- `.env` is **never** committed. `.env.example` lists the variables with
  placeholder values.
- The Vue frontend **never** holds an AI API key. All AI calls go through the
  AI service, which is the only thing with the key.
- Outbound HTTPS only. No proxy unless a school requires one (a Phase 6
  setting if it comes up).

## 10. Worked example

Input on `ai/request`:

```json
{
  "ts": "2026-05-10T13:45:12.123Z",
  "source": "frontend",
  "schema": "v1",
  "data": {
    "correlation_id": "01J...",
    "template": "explain-sensors-v1",
    "context": {
      "readings": [
        {"source": "microbit-01", "metric": "temperature", "value": 24, "unit": "celsius"},
        {"source": "microbit-01", "metric": "humidity",    "value": 70, "unit": "percent"},
        {"source": "probe-a",     "metric": "moisture",    "value": 18, "unit": "percent"}
      ],
      "audience": "Year 7"
    }
  }
}
```

Output on `ai/response/01J...`:

```json
{
  "ts": "2026-05-10T13:45:13.401Z",
  "source": "ai-service",
  "schema": "v1",
  "data": {
    "correlation_id": "01J...",
    "provider": "claude",
    "model": "claude-opus-4-7",
    "text": "The soil moisture is low at 18%, so the plant may need watering. The air is warm at 24 °C and moderately humid at 70%.",
    "tokens": {"input": 412, "output": 47}
  }
}
```
