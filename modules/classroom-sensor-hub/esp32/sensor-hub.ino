// Classroom Sensor Hub — ESP32 sketch
//
// Reads temperature + humidity from a DHT22 once a second and publishes
// them as v1-envelope MQTT messages on the platform's broker.
//
// Hardware
//   - Any ESP32 dev board (ESP32-WROOM-32, NodeMCU-32S, etc).
//   - DHT22 sensor wired as: VCC -> 3V3, DATA -> GPIO 4, GND -> GND.
//
// Required libraries (Arduino IDE: Tools -> Manage Libraries):
//   - "PubSubClient" by Nick O'Leary
//   - "DHT sensor library" by Adafruit
//   - "Adafruit Unified Sensor"
//
// Before flashing
//   - Fill in WIFI_SSID, WIFI_PASS, MQTT_HOST, MQTT_PASS below.
//   - Change DEVICE_ID for each board (e.g. "esp32-02").

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <time.h>

// ---------- configuration --------------------------------------------------

const char* WIFI_SSID = "YourSchoolWiFi";
const char* WIFI_PASS = "yourwifipassword";

const char* MQTT_HOST = "pi-iot-XX.local";  // your Pi hostname
const int   MQTT_PORT = 1883;
const char* MQTT_USER = "platform";
const char* MQTT_PASS = "your-mqtt-password";

const char* DEVICE_ID = "esp32-01";
const char* DOMAIN    = "classroom";

const int DHT_PIN = 4;
#define DHT_TYPE DHT22

const unsigned long PUBLISH_INTERVAL_MS = 1000;

// ---------- internals ------------------------------------------------------

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

void connectWifi() {
  Serial.print("WiFi: connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nWiFi: ip=");
  Serial.println(WiFi.localIP());
}

void connectNtp() {
  // Sync the clock so our 'ts' field is real ISO-8601 UTC.
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("NTP: syncing");
  struct tm tm;
  while (!getLocalTime(&tm, 5000)) {
    Serial.print(".");
  }
  Serial.println("\nNTP: ok");
}

void connectMqtt() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);
  while (!mqtt.connected()) {
    Serial.print("MQTT: connecting…");
    if (mqtt.connect(DEVICE_ID, MQTT_USER, MQTT_PASS)) {
      Serial.println(" ok");
    } else {
      Serial.print(" failed rc=");
      Serial.println(mqtt.state());
      delay(2000);
    }
  }
}

void isoNow(char* buf, size_t buflen) {
  time_t now = time(nullptr);
  struct tm tm;
  gmtime_r(&now, &tm);
  // ISO 8601 with trailing Z, second precision.
  strftime(buf, buflen, "%Y-%m-%dT%H:%M:%SZ", &tm);
}

void publish(const char* metric, float value, const char* unit) {
  if (isnan(value)) {
    Serial.print("DHT: NaN for ");
    Serial.println(metric);
    return;
  }

  char topic[128];
  snprintf(topic, sizeof(topic), "%s/sensor/%s/%s", DOMAIN, DEVICE_ID, metric);

  char ts[32];
  isoNow(ts, sizeof(ts));

  char payload[384];
  snprintf(
    payload, sizeof(payload),
    "{\"ts\":\"%s\",\"source\":\"%s\",\"schema\":\"v1\","
    "\"data\":{\"value\":%.2f,\"unit\":\"%s\",\"quality\":\"good\"}}",
    ts, DEVICE_ID, value, unit
  );

  mqtt.publish(topic, payload);
  Serial.printf("  → %s: %.2f %s\n", topic, value, unit);
}

// ---------- Arduino lifecycle ----------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println("Classroom Sensor Hub — ESP32 booting");

  dht.begin();
  connectWifi();
  connectNtp();
  connectMqtt();
}

void loop() {
  if (!mqtt.connected()) {
    connectMqtt();
  }
  mqtt.loop();

  static unsigned long last = 0;
  unsigned long now = millis();
  if (now - last >= PUBLISH_INTERVAL_MS) {
    last = now;
    publish("temperature", dht.readTemperature(), "celsius");
    publish("humidity",    dht.readHumidity(),    "percent");
  }
}
