# Classroom Sensor Hub — Micro:bit V2 program
#
# Reads the Micro:bit's built-in temperature and light sensors and
# prints them as JSON over USB serial, once per second. The Pi runs
# serial-bridge.py which forwards each line as an MQTT message.
#
# To install:
#   1. Download the latest Mu Editor (https://codewith.mu).
#   2. Plug the Micro:bit into your laptop with a USB cable.
#   3. In Mu, set Mode to BBC micro:bit, paste this file, click "Flash".
#
# Change DEVICE_ID to a unique name for each board (e.g. microbit-02).

from microbit import *
import json


DEVICE_ID = "microbit-01"
PUBLISH_INTERVAL_MS = 1000


def report(metric, value, unit):
    """Print one JSON line. The serial bridge on the Pi parses these."""
    print(json.dumps({
        "device": DEVICE_ID,
        "metric": metric,
        "value": value,
        "unit": unit,
    }))


# Show a heart on the LED matrix while we boot, then clear.
display.show(Image.HEART)
sleep(500)
display.clear()


while True:
    # Built-in sensors:
    #   temperature() -> integer Celsius, ~5 °C accuracy.
    #   display.read_light_level() -> 0-255, brightness from the LEDs
    #     used backwards as photodiodes.
    temp_c = temperature()
    light = display.read_light_level()

    report("temperature", temp_c, "celsius")
    report("light", light, "lux")

    # Visual heartbeat — single-pixel toggle so students can see the
    # board is alive without crowding the LED matrix.
    display.set_pixel(2, 2, 9)
    sleep(50)
    display.set_pixel(2, 2, 0)

    sleep(PUBLISH_INTERVAL_MS - 50)
