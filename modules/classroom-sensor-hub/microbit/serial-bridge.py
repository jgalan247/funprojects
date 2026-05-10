#!/usr/bin/env python3
"""Micro:bit USB serial → platform MQTT bridge.

The Micro:bit prints JSON lines like
    {"device": "microbit-01", "metric": "temperature", "value": 22, "unit": "celsius"}
over USB serial. This script reads them on the Pi and republishes as
v1-envelope MQTT messages on the platform's broker.

Usage:
    pip install pyserial paho-mqtt
    python3 serial-bridge.py [/dev/ttyACM0]

Required environment variables:
    MQTT_PASSWORD   the platform's MQTT password (from .env)

Optional:
    MQTT_HOST       default: 127.0.0.1
    MQTT_USER       default: platform
    DOMAIN          default: classroom (used as the first topic segment)
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
    import serial
except ImportError:  # pragma: no cover
    sys.exit("missing deps — run: pip install pyserial paho-mqtt")


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
            "data": {"value": value, "unit": unit, "quality": "good"},
        }
    )


def main() -> None:
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
    baud = 115200

    host = os.environ.get("MQTT_HOST", "127.0.0.1")
    user = os.environ.get("MQTT_USER", "platform")
    password = os.environ.get("MQTT_PASSWORD")
    domain = os.environ.get("DOMAIN", "classroom")

    if not password:
        sys.exit("set MQTT_PASSWORD environment variable")

    print(f"→ opening serial {port} @ {baud}")
    ser = serial.Serial(port, baud, timeout=2)

    print(f"→ connecting to MQTT {host}:1883 as {user}")
    client = mqtt.Client(client_id=f"microbit-bridge-{os.getpid()}")
    client.username_pw_set(user, password)
    client.connect(host, 1883, keepalive=30)
    client.loop_start()

    print("✓ bridge running. Ctrl-C to stop.\n")
    try:
        while True:
            raw = ser.readline()
            if not raw:
                continue
            try:
                line = raw.decode("utf-8", errors="replace").strip()
            except UnicodeDecodeError:
                continue
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                # Some boot messages from the Micro:bit aren't JSON.
                # Print them so the operator sees what's happening, then
                # skip.
                print(f"  · {line}")
                continue

            device = msg.get("device")
            metric = msg.get("metric")
            value = msg.get("value")
            unit = msg.get("unit")

            if not all([device, metric, isinstance(value, (int, float)), unit]):
                print(f"  ! incomplete: {msg}")
                continue

            topic = f"{domain}/sensor/{device}/{metric}"
            client.publish(topic, envelope(device, value, unit), qos=0)
            print(f"  → {topic}: {value} {unit}")
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        client.loop_stop()
        client.disconnect()
        print("\nstopped.")


if __name__ == "__main__":
    main()
