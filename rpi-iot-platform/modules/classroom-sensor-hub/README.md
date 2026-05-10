# Classroom Sensor Hub

A first IoT module for Year 7–9 students. Pair a Micro:bit (over USB)
or an ESP32 (over Wi-Fi) with the platform, watch readings stream to
the dashboard, ask Claude what they mean, and capture snapshots for
class discussion.

## What's in this folder

```
classroom-sensor-hub/
├── module.yaml                # Manifest (id, version, MQTT topics, hardware)
├── README.md                  # This file
├── microbit/
│   ├── main.py                # MicroPython program for the Micro:bit V2
│   └── serial-bridge.py       # Pi-side: USB serial -> MQTT
└── esp32/
    └── sensor-hub.ino         # Arduino sketch with Wi-Fi + DHT22
```

## Lesson plan (60 minutes)

| Time | What | Who |
| --- | --- | --- |
| 0–5 min | Recap: what's an MQTT message? Show the dashboard with the test publisher running. | Whole class |
| 5–15 min | Flash a Micro:bit (Mu Editor) **or** an ESP32 (Arduino IDE) with the provided program. | Pairs |
| 15–25 min | Plug it in. The teacher runs `serial-bridge.py` on the Pi (or each pair's ESP32 connects on Wi-Fi). | Pairs + teacher |
| 25–35 min | Watch your sensor's card appear on the dashboard. Tap it for the chart. Compare with another pair's readings. | Pairs |
| 35–45 min | Tap "Explain" — Claude writes a sentence. Discuss as a class: was Claude right? Anything surprising? | Whole class |
| 45–55 min | Take three snapshots through the lesson — start, middle, end. Compare them in Settings. | Whole class |
| 55–60 min | Put the kit away. | Pairs |

## Path A — Micro:bit (recommended for Year 7)

The Micro:bit V2 has a built-in temperature sensor and uses its LED matrix
to read light levels. It connects to the Pi over USB and a small Python
script on the Pi forwards each reading to MQTT.

### 1. Flash the program

1. Install [Mu Editor](https://codewith.mu) on the laptop.
2. Plug the Micro:bit V2 in via USB.
3. In Mu, set Mode to "BBC micro:bit".
4. Open `microbit/main.py` from this folder.
5. Edit `DEVICE_ID` to a unique name (e.g. `microbit-03` for pair 3).
6. Click **Flash**. The Micro:bit's yellow LED flickers, then a heart
   appears briefly on the matrix.

### 2. Run the serial bridge on the Pi

The Micro:bit prints JSON over USB; the Pi has to forward it as MQTT.

```bash
# On the Pi, one-off install:
pip install pyserial paho-mqtt

# Then, with the Micro:bit plugged in to the Pi:
cd /opt/iot-platform/modules/classroom-sensor-hub/microbit
export MQTT_PASSWORD="<your MQTT password from .env>"
python3 serial-bridge.py /dev/ttyACM0
```

(If `/dev/ttyACM0` doesn't exist, run `ls /dev/tty*` to find the right
device — usually `/dev/ttyACM0` on Linux, `/dev/cu.usbmodem*` on macOS.)

You should see lines tick by:

```
✓ bridge running. Ctrl-C to stop.
  → classroom/sensor/microbit-03/temperature: 22 celsius
  → classroom/sensor/microbit-03/light: 45 lux
```

The dashboard should show two new cards within a second.

## Path B — ESP32 (recommended for Year 8–9)

The ESP32 has Wi-Fi, so it talks MQTT directly — no Pi-side bridge.
You'll need a DHT22 temperature/humidity sensor wired to GPIO 4.

### 1. Wire the DHT22

```
DHT22 pin     ESP32 pin
---------     ---------
VCC      ->   3V3
DATA     ->   GPIO 4
GND      ->   GND
```

(A 10 kΩ pull-up resistor between DATA and 3V3 is recommended but the
DHT22's internal pull-up is usually sufficient.)

### 2. Flash the sketch

1. Install the Arduino IDE.
2. Add ESP32 board support: Preferences → Additional Board Manager URLs →
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`,
   then Tools → Board Manager → install "esp32".
3. Install libraries (Tools → Manage Libraries):
   - **PubSubClient** by Nick O'Leary
   - **DHT sensor library** by Adafruit
   - **Adafruit Unified Sensor**
4. Open `esp32/sensor-hub.ino`.
5. Edit the configuration block at the top:
   - `WIFI_SSID`, `WIFI_PASS` — your school Wi-Fi
   - `MQTT_HOST` — your Pi's hostname (e.g. `pi-iot-01.local`)
   - `MQTT_PASS` — the MQTT password from the Pi's `.env`
   - `DEVICE_ID` — unique per board
6. Plug the ESP32 in. Tools → Board → "ESP32 Dev Module". Tools → Port →
   the new serial device.
7. Click **Upload**.
8. Tools → Serial Monitor (115200 baud) to watch it boot:
   ```
   Classroom Sensor Hub — ESP32 booting
   WiFi: connecting to YourSchoolWiFi
   ...
   WiFi: ip=192.168.1.42
   NTP: ok
   MQTT: connecting… ok
     → classroom/sensor/esp32-01/temperature: 21.30 celsius
     → classroom/sensor/esp32-01/humidity: 58.40 percent
   ```

The dashboard should show the new sensor cards within a second.

## Troubleshooting

### Nothing on the dashboard

Walk the chain backwards:

1. **Is the publisher publishing?** Watch the serial monitor (ESP32) or
   the bridge output (Micro:bit) — you should see lines printed each
   second.
2. **Is MQTT delivering?** On the Pi:
   ```
   mosquitto_sub -h localhost -u platform -P "<password>" -t '+/sensor/+/+'
   ```
   Messages should appear. If not, the publisher can't reach the broker
   (Wi-Fi? credentials?).
3. **Is the API ingesting?**
   ```
   docker compose logs api | tail
   ```
   You should see no `dropped bad message` lines. If you do, the
   payload doesn't match the v1 envelope.
4. **Is the WebSocket up?** The dashboard's connection pill should say
   `connected`. If it says `disconnected`, restart the API
   (`docker compose restart api`).

### Wrong values

The Micro:bit's built-in temperature sensor reads the **chip
temperature** of the CPU, which runs warmer than the room — typically
2–4 °C above ambient. Mention this to the class as a teaching moment
about real-world sensors.

### "Hub" hostname doesn't resolve from a laptop

Some school Wi-Fi networks block mDNS. Use the Pi's IP address instead:
`ip addr` on the Pi shows it.

## Extending the module

- **Add a metric**: in the Micro:bit program, call `report("acceleration",
  accelerometer.get_x(), "millig")`. The platform auto-registers it on
  first sight — no schema changes.
- **Add a new device**: just change `DEVICE_ID` and run a second board.
  Each gets its own card.
- **Different unit**: stick to lowercase SI names from
  `docs/mqtt-conventions.md` §2.1 (`pascal`, `lux`, `metres-per-second`,
  `ppm` …).
