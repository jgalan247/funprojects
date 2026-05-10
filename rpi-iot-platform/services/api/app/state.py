"""In-memory state for Phase 3.

Phase 4 swaps :class:`LatestReadingsStore` for a SQLite-backed repository
without changing call sites. Until then we hold the latest reading per sensor
in process memory; readings are lost on restart.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Reading:
    sensor_id: str        # "<device_id>.<metric>"
    device_id: str
    metric: str
    value: float
    unit: str
    quality: str
    ts: datetime          # the wall-clock the publisher claims
    received_at: datetime # the wall-clock the API actually received it
    topic: str            # the originating MQTT topic — needed to register sensors


def reading_to_dict(r: Reading) -> dict:
    return {
        "sensor_id": r.sensor_id,
        "device_id": r.device_id,
        "metric": r.metric,
        "value": r.value,
        "unit": r.unit,
        "quality": r.quality,
        "ts": r.ts.isoformat(),
        "received_at": r.received_at.isoformat(),
    }


class LatestReadingsStore:
    """Last-value cache, one entry per sensor.

    Single-threaded asyncio means dict operations between awaits are atomic;
    no lock needed.
    """

    def __init__(self) -> None:
        self._readings: dict[str, Reading] = {}

    def put(self, reading: Reading) -> None:
        self._readings[reading.sensor_id] = reading

    def get(self, sensor_id: str) -> Optional[Reading]:
        return self._readings.get(sensor_id)

    def list_all(self) -> list[Reading]:
        return list(self._readings.values())
