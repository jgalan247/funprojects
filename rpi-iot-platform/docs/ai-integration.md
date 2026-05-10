# AI integration

The AI service explains a single sensor reading in language a Year 7 student
understands. It is a separate service from the main API so that the
Anthropic API key, retries, and prompt logic live in one place.

## 1. Scope

- **One vendor: Anthropic Claude.** No provider abstraction, no OpenAI/Gemini
  hedging. The whole codebase calls Claude directly via the `anthropic` SDK.
- **One model: Claude Haiku 4.5** (`claude-haiku-4-5-20251001`). Cheap, fast,
  and more than capable for 2–3 sentence explanations. Opus would be ~15×
  the cost per token for no audible improvement on this task.
- **One trigger: a button.** The user taps "Explain" on a sensor card; that
  is the only path that calls Claude. No automatic calls, no MQTT triggers,
  no background jobs.
- **One payload shape: the latest reading only.** No trend windows, no
  cross-sensor snapshots. (Both are easy to add later if a teacher asks; we
  just don't pay the token cost or design cost up front.)

If any of those four lines change, this document changes first.

## 2. Configuration

```env
# .env (never committed)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
ANTHROPIC_MAX_OUTPUT_TOKENS=256
ANTHROPIC_TIMEOUT_S=15
```

- Model ID lives in env so we can move to a newer Haiku without redeploying.
- 256 output tokens is plenty for a 2–3 sentence answer; cap stops a runaway
  response.
- 15 s timeout matches the UI expectation ("Explain" should feel snappy).

## 3. Request flow

```
Vue: tap "Explain" on a sensor card
  → POST /api/ai/explain    { sensor_id }                 [main API]
  → POST /ai/explain        { sensor_id, reading }        [AI service]
  → render template (system + user)
  → anthropic.messages.create(...)
  → persist ai_prompts + ai_responses rows
  → 200 { text, latency_ms, tokens }
  → Vue renders the text under the card
```

The main API is a thin proxy: it looks up the sensor's latest reading from
SQLite (one indexed query), forwards it to the AI service, returns the text.
That keeps the AI service unaware of the database schema.

## 4. The prompt template

One template under `services/ai/app/prompts/`:

```
prompts/
  explain-sensor-v1.md
```

`explain-sensor-v1.md`:

```markdown
---
id: explain-sensor-v1
audience: year-7
required: [metric, value, unit, source]
---

## system
You are a friendly science teacher explaining a single sensor reading to
Year 7 students. Use British English. Be concise: 2–3 sentences. Be concrete.
Avoid jargon. Never invent values. If a reading looks unusual for normal
classroom or outdoor conditions, say so plainly.

## user
A sensor called "{{ source }}" has just measured:
- {{ metric }}: {{ value }} {{ unit }}

Explain what this reading means and whether it looks normal.
```

The template is loaded and validated at AI service boot. A malformed template
fails boot loudly — better than failing on the first user request.

## 5. Calling Claude

```python
# services/ai/app/claude.py

from anthropic import AsyncAnthropic

client = AsyncAnthropic()  # picks up ANTHROPIC_API_KEY from env

async def explain(rendered_system: str, rendered_user: str) -> Completion:
    msg = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=settings.anthropic_max_output_tokens,
        system=[
            {
                "type": "text",
                "text": rendered_system,
                "cache_control": {"type": "ephemeral"},   # cache the system block
            }
        ],
        messages=[{"role": "user", "content": rendered_user}],
        timeout=settings.anthropic_timeout_s,
    )
    return Completion(
        text=msg.content[0].text,
        input_tokens=msg.usage.input_tokens,
        output_tokens=msg.usage.output_tokens,
        model=msg.model,
    )
```

Notes:

- **Prompt caching** is enabled on the system block. The system text is
  identical for every call, so after the first request it becomes a cache
  hit and the per-call input cost drops sharply.
- We do **not** pass conversation history. Every call is one-shot.
- Retries go through one helper (`_retry.py`): exponential backoff, max 3
  attempts on 429/5xx, one retry on timeout. No retries on 4xx.

## 6. Offline / no-key fallback

If `ANTHROPIC_API_KEY` is unset at boot, the service replaces the Claude
call with a deterministic stub that returns:

> "Sample reading: {metric} is {value} {unit} from {source}. (AI explanations
> are disabled — no API key configured.)"

The frontend shows a one-line banner ("AI explanations disabled") so the
teacher knows. The platform never crashes for this reason.

## 7. Persistence

Every successful and every failed call writes:

1. One `ai_prompts` row — template id, context JSON, rendered text.
2. One `ai_responses` row — model, text (or error), input/output tokens,
   latency, status.

Schema lives in [`database-design.md`](database-design.md) §2.4. Keeping
this is non-negotiable: it powers the cost view, the "show what we asked
the model" debug surface, and any future audit needs.

## 8. Failure handling

| Failure | Behaviour |
| --- | --- |
| `ANTHROPIC_API_KEY` unset at boot | Fallback stub takes over. UI banner. |
| Anthropic returns 429 / 5xx | Exponential backoff, max 3 attempts, then `status=error`. UI shows "Couldn't reach Claude — try again". |
| Timeout (`ANTHROPIC_TIMEOUT_S`) | One retry, then `status=timeout`. Same UI message. |
| Template render error | Don't call Claude. Log to `system_logs`. Return 500. |
| Sensor has no readings yet | Main API returns 409 before calling the AI service. UI button is disabled until a reading exists. |

## 9. Cost control

- **Cap output tokens** at 256.
- **Cache the system block** (see §5).
- **Concurrency cap**: an asyncio semaphore of 4 in the AI service. The Pi
  4B doesn't need more.
- **Track usage**: `input_tokens` / `output_tokens` per call land in
  `ai_responses`. Phase 6 ships a simple weekly tally view in `/settings`.
- **No streaming.** The answer is short; one HTTP response is fine and the
  UI is simpler.

## 10. Security

- API key only in environment variables, only on the AI service container.
- The Vue frontend never sees the key. All calls go through the API → AI
  service.
- `.env` is gitignored; `.env.example` is committed with placeholders.
- Outbound HTTPS only. No proxy unless a school requires one.

## 11. Worked example

User taps "Explain" on the temperature card for `microbit-01`.

API forwards to the AI service:

```json
{
  "sensor_id": "microbit-01.temperature",
  "reading": {
    "source": "microbit-01",
    "metric": "temperature",
    "value": 24.3,
    "unit": "celsius",
    "ts": "2026-05-10T13:45:12.123Z"
  }
}
```

AI service responds:

```json
{
  "text": "The temperature from microbit-01 is 24.3 °C, which is a comfortable, mildly warm classroom temperature. Nothing unusual — typical of a heated room on a spring day.",
  "model": "claude-haiku-4-5-20251001",
  "tokens": {"input": 178, "output": 41},
  "latency_ms": 612,
  "status": "ok"
}
```

The Vue card shows the text. The same prompt and response sit in
`ai_prompts` / `ai_responses` for the cost and history views.
