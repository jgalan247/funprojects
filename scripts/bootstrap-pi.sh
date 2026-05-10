#!/usr/bin/env bash
# One-shot setup for a fresh Raspberry Pi running Raspberry Pi OS 64-bit.
# Idempotent — safe to re-run.

set -euo pipefail

echo "→ Updating system packages…"
sudo apt update
sudo apt full-upgrade -y

echo "→ Installing useful tools…"
sudo apt install -y git curl mosquitto-clients

if ! command -v docker >/dev/null 2>&1; then
  echo "→ Installing Docker…"
  curl -fsSL https://get.docker.com | sudo sh
else
  echo "✓ Docker already installed."
fi

if ! id -nG "$USER" | grep -qw docker; then
  echo "→ Adding $USER to the docker group…"
  sudo usermod -aG docker "$USER"
  NEED_RELOGIN=1
else
  echo "✓ $USER is already in the docker group."
  NEED_RELOGIN=0
fi

echo
echo "Versions:"
docker --version 2>/dev/null || echo "  docker: not yet available"
docker compose version 2>/dev/null || echo "  docker compose: not yet available"

echo
if [[ $NEED_RELOGIN -eq 1 ]]; then
  echo "Almost there — log out and back in (or 'exit' your SSH and reconnect)"
  echo "for the docker group change to take effect, then run:"
  echo "    docker compose up -d"
else
  echo "Ready. Next:"
  echo "    cp .env.example .env && nano .env"
  echo "    ./scripts/bootstrap-mqtt-passwd.sh"
  echo "    docker compose up -d"
fi
