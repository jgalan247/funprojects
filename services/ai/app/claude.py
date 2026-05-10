"""Anthropic Claude wrapper.

Single-purpose: take a rendered (system, user) pair, return a
:class:`Completion`. Retries on 429/5xx with exponential back-off, max 3
attempts. One retry on timeout, then surfaces ``status='timeout'``.

When ``ANTHROPIC_API_KEY`` is unset, :func:`run` is replaced with a
deterministic stub via :func:`make_runner` so the service still serves
``/ai/explain`` (with a clear UI banner driven by the response shape).
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

from anthropic import APIStatusError, APITimeoutError, AsyncAnthropic

from app.config import Settings

logger = logging.getLogger("iot.ai.claude")


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    model: str
    provider: str
    latency_ms: int
    status: str          # "ok" | "error" | "timeout"
    error: str | None


Runner = Callable[[str, str], Awaitable[Completion]]


def make_runner(settings: Settings) -> Runner:
    """Choose between the real Claude client and the offline stub."""
    if settings.has_api_key:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return _make_real_runner(client, settings)
    return _make_stub_runner(settings)


# ---------------------------------------------------------------------------
# Real runner
# ---------------------------------------------------------------------------

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _make_real_runner(client: AsyncAnthropic, settings: Settings) -> Runner:
    async def run(system: str, user: str) -> Completion:
        started = time.perf_counter()
        attempt = 0
        last_error: Exception | None = None
        while attempt < 3:
            try:
                msg = await client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=settings.anthropic_max_output_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                    timeout=settings.anthropic_timeout_s,
                )
                latency_ms = int((time.perf_counter() - started) * 1000)
                text = "".join(
                    block.text for block in msg.content if block.type == "text"
                )
                return Completion(
                    text=text,
                    input_tokens=msg.usage.input_tokens,
                    output_tokens=msg.usage.output_tokens,
                    model=msg.model,
                    provider="claude",
                    latency_ms=latency_ms,
                    status="ok",
                    error=None,
                )
            except APITimeoutError as e:
                last_error = e
                if attempt >= 1:
                    break
                attempt += 1
                logger.warning("Claude timeout (attempt %d) — retrying", attempt)
            except APIStatusError as e:
                last_error = e
                if e.status_code not in _RETRYABLE_STATUS or attempt >= 2:
                    break
                attempt += 1
                wait = 0.5 * (2 ** (attempt - 1))
                logger.warning(
                    "Claude %d (attempt %d) — backing off %.1fs",
                    e.status_code, attempt, wait,
                )
                await asyncio.sleep(wait)
            except Exception as e:  # noqa: BLE001
                last_error = e
                break

        latency_ms = int((time.perf_counter() - started) * 1000)
        is_timeout = isinstance(last_error, APITimeoutError)
        return Completion(
            text="",
            input_tokens=None,
            output_tokens=None,
            model=settings.anthropic_model,
            provider="claude",
            latency_ms=latency_ms,
            status="timeout" if is_timeout else "error",
            error=str(last_error) if last_error else "unknown",
        )

    return run


# ---------------------------------------------------------------------------
# Offline stub — used when ANTHROPIC_API_KEY is missing.
# ---------------------------------------------------------------------------

def _make_stub_runner(settings: Settings) -> Runner:
    async def run(system: str, user: str) -> Completion:  # noqa: ARG001 — kept for parity
        # Deterministic, useful for demos. Mentions the missing key so the
        # operator can see why explanations look canned.
        line_with_metric = next(
            (line for line in user.splitlines() if line.strip().startswith("- ")),
            "",
        )
        text = (
            "AI explanations are disabled — no Anthropic API key configured. "
            f"Sample reading: {line_with_metric.lstrip('- ').strip() or 'unknown'}."
        )
        return Completion(
            text=text,
            input_tokens=0,
            output_tokens=0,
            model="echo-stub",
            provider="echo",
            latency_ms=1,
            status="ok",
            error=None,
        )

    return run
