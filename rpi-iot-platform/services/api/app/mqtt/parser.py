"""Parse the v1 MQTT envelope into a :class:`Reading`.

Topic shape:  <domain>/sensor/<device_id>/<metric>
Payload:      JSON with {ts, source, schema, data: {value, unit, quality?}}

Anything off-spec raises :class:`ParseError` and the caller logs+drops it.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app.state import Reading


class ParseError(ValueError):
    """The message did not match the v1 envelope."""


def split_topic(topic: str) -> tuple[str, str]:
    """Returns (device_id, metric) for a v1 sensor topic."""
    parts = topic.split("/")
    if len(parts) != 4 or parts[1] != "sensor":
        raise ParseError(
            f"topic does not match <domain>/sensor/<device>/<metric>: {topic!r}"
        )
    return parts[2], parts[3]


def _parse_ts(raw: str) -> datetime:
    # Accept a trailing 'Z' (which fromisoformat doesn't, on older Pythons).
    cleaned = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError as e:
        raise ParseError(f"invalid 'ts': {e}") from e


def parse_envelope(topic: str, payload: bytes | str) -> Reading:
    device_id, metric = split_topic(topic)

    raw = payload.decode() if isinstance(payload, (bytes, bytearray)) else payload
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ParseError(f"payload is not JSON: {e}") from e
    if not isinstance(body, dict):
        raise ParseError("payload is not a JSON object")

    schema = body.get("schema")
    if schema != "v1":
        raise ParseError(f"unsupported schema: {schema!r} (expected 'v1')")

    ts_raw = body.get("ts")
    if not isinstance(ts_raw, str):
        raise ParseError("missing or non-string 'ts'")
    ts = _parse_ts(ts_raw)

    data = body.get("data")
    if not isinstance(data, dict):
        raise ParseError("missing or non-object 'data'")

    value = data.get("value")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ParseError(f"data.value must be a number, got {value!r}")

    unit = data.get("unit")
    if not isinstance(unit, str) or not unit:
        raise ParseError("missing or empty data.unit")

    quality = data.get("quality", "good")
    if quality not in {"good", "stale", "suspect", "error"}:
        raise ParseError(f"unknown data.quality: {quality!r}")

    return Reading(
        sensor_id=f"{device_id}.{metric}",
        device_id=device_id,
        metric=metric,
        value=float(value),
        unit=unit,
        quality=quality,
        ts=ts,
        received_at=datetime.now(timezone.utc),
    )
