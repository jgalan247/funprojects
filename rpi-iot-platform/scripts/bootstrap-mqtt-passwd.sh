#!/usr/bin/env bash
# Generate infra/mosquitto/passwd from MQTT_USER and MQTT_PASSWORD in .env.
# Re-runnable. Uses the eclipse-mosquitto Docker image to hash the password
# so nothing extra needs to be installed on the host.

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "✗ .env not found. Copy .env.example to .env first:" >&2
  echo "    cp .env.example .env && nano .env" >&2
  exit 1
fi

# Load .env into the environment.
set -a
# shellcheck disable=SC1091
source .env
set +a

: "${MQTT_USER:?MQTT_USER must be set in .env}"
: "${MQTT_PASSWORD:?MQTT_PASSWORD must be set in .env}"

PASSWD_FILE="infra/mosquitto/passwd"
mkdir -p "$(dirname "$PASSWD_FILE")"

# Write plain-text user:password, then hash in place using the mosquitto image.
printf '%s:%s\n' "$MQTT_USER" "$MQTT_PASSWORD" > "$PASSWD_FILE"

docker run --rm \
  -v "$(pwd)/$PASSWD_FILE:/tmp/passwd" \
  eclipse-mosquitto:2 \
  mosquitto_passwd -U /tmp/passwd

chmod 600 "$PASSWD_FILE"
echo "✓ Wrote $PASSWD_FILE for user '$MQTT_USER'."
