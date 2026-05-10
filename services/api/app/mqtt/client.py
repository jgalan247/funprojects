"""Background MQTT subscriber.

Subscribes to ``+/sensor/+/+``, parses the v1 envelope, updates the in-memory
store, and fans out to connected WebSocket clients.

Reconnects automatically with a fixed back-off — students can stop and start
Mosquitto without restarting the API.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

import aiomqtt

from app.mqtt.parser import ParseError, parse_envelope
from app.state import Reading

logger = logging.getLogger("iot.mqtt")

OnReading = Callable[[Reading], Awaitable[None]]


async def run_subscriber(
    *,
    host: str,
    port: int,
    user: str,
    password: str,
    on_reading: OnReading,
    backoff_s: float = 5.0,
) -> None:
    """Run forever (until cancelled). Reconnects on any MQTT error.

    Each parsed reading is handed to ``on_reading``. The subscriber itself is
    storage-agnostic — persistence and broadcast live in the callback.
    """
    while True:
        try:
            async with aiomqtt.Client(
                hostname=host,
                port=port,
                username=user,
                password=password,
                identifier="iot-api-subscriber",
                keepalive=30,
            ) as client:
                logger.info("MQTT connected to %s:%d", host, port)
                await client.subscribe("+/sensor/+/+", qos=0)
                async for message in client.messages:
                    try:
                        reading = parse_envelope(
                            str(message.topic), message.payload
                        )
                    except ParseError as exc:
                        logger.warning(
                            "dropped bad message on %s: %s", message.topic, exc
                        )
                        continue
                    await on_reading(reading)
        except aiomqtt.MqttError as exc:
            logger.warning(
                "MQTT lost (%s) — reconnecting in %.0fs", exc, backoff_s
            )
            await asyncio.sleep(backoff_s)
