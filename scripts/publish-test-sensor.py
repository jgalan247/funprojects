#!/usr/bin/env python3
"""Test sensor publisher.

Emits fake temperature and humidity readings to the platform's MQTT broker
once a second so students can see their dashboard light up before they have
real hardware.

Usage:
    pip install aiomqtt
    python3 scripts/publish-test-sensor.py [--host HOST] [--device NAME]

Required: MQTT_PASSWORD (env var or --password). Defaults assume a Pi at
``localhost`` and the standard credentials from ``.env``.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import random
import sys
from datetime import datetime, timezone

try:
    import aiomqtt
except ImportError:  # pragma: no cover
    sys.exit("missing aiomqtt — run: pip install aiomqtt")


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def envelope(source: str, value: float, unit: str) -> str:
    return json.dumps(
        {
            "ts": now_iso(),
            "source": source,
            "schema": "v1",
            "data": {"value": round(value, 2), "unit": unit, "quality": "good"},
        }
    )


async def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default=os.environ.get("MQTT_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", "1883")))
    p.add_argument("--user", default=os.environ.get("MQTT_USER", "platform"))
    p.add_argument("--password", default=os.environ.get("MQTT_PASSWORD"))
    p.add_argument("--device", default="microbit-test-01")
    p.add_argument("--domain", default="classroom")
    p.add_argument("--interval", type=float, default=1.0)
    args = p.parse_args()

    if not args.password:
        sys.exit("set MQTT_PASSWORD in env or pass --password")

    print(f"→ connecting to {args.host}:{args.port} as {args.user}")
    print(
        f"→ publishing as {args.device} on "
        f"{args.domain}/sensor/{args.device}/{{temperature,humidity}}"
    )

    t = 0.0
    async with aiomqtt.Client(
        hostname=args.host,
        port=args.port,
        username=args.user,
        password=args.password,
        identifier=f"test-publisher-{args.device}",
    ) as client:
        print("✓ connected. Publishing 1 Hz. Ctrl-C to stop.")
        while True:
            # Slowly varying signal + small noise — looks alive on a chart.
            temperature = 22.0 + 2.0 * math.sin(t / 60.0) + random.uniform(-0.2, 0.2)
            humidity = 60.0 + 5.0 * math.cos(t / 90.0) + random.uniform(-1.0, 1.0)

            await client.publish(
                f"{args.domain}/sensor/{args.device}/temperature",
                payload=envelope(args.device, temperature, "celsius"),
                qos=0,
            )
            await client.publish(
                f"{args.domain}/sensor/{args.device}/humidity",
                payload=envelope(args.device, humidity, "percent"),
                qos=0,
            )
            print(
                f"  t={t:6.1f}s  "
                f"temperature={temperature:6.2f} °C  "
                f"humidity={humidity:5.1f} %"
            )
            t += args.interval
            await asyncio.sleep(args.interval)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nstopped.")
