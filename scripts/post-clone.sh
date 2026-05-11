#!/usr/bin/env bash
# Post-clone setup for a cloned Pi SD card.
#
# Run this once on each newly flashed Pi to give it a unique hostname
# and a fresh set of SSH host keys, so it can coexist on the same
# network as the Pi the image was cloned from.
#
# Optionally also wipes the runtime data folder (database, Mosquitto
# persistence, Node-RED state) so each kit starts clean.
#
# Idempotent — safe to re-run.
#
# Usage:
#     sudo ./scripts/post-clone.sh

set -euo pipefail

# --------------------------------------------------------------------------
# Safety checks
# --------------------------------------------------------------------------

if [[ $EUID -ne 0 ]]; then
  echo "This script needs root. Re-run with:  sudo $0" >&2
  exit 1
fi

if [[ -f /proc/cpuinfo ]] && ! grep -qE "^(Model|Hardware)" /proc/cpuinfo; then
  echo "Warning: /proc/cpuinfo doesn't mention a Raspberry Pi model." >&2
fi

CURRENT_HOSTNAME="$(hostname)"
echo "Current hostname: $CURRENT_HOSTNAME"
echo

# --------------------------------------------------------------------------
# 1. Hostname
# --------------------------------------------------------------------------

# Suggest "<prefix>-XX" so the user just has to swap the number.
DEFAULT_HOSTNAME="${CURRENT_HOSTNAME%-*}-XX"
read -rp "Enter new hostname (e.g. pi-iot-02) [default: $DEFAULT_HOSTNAME]: " NEW_HOSTNAME
NEW_HOSTNAME="${NEW_HOSTNAME:-$DEFAULT_HOSTNAME}"

if ! [[ "$NEW_HOSTNAME" =~ ^[a-z0-9][a-z0-9-]{0,62}$ ]]; then
  echo "✗ Invalid hostname: must be lowercase letters/digits/hyphens, 1-63 chars." >&2
  exit 1
fi

if [[ "$NEW_HOSTNAME" != "$CURRENT_HOSTNAME" ]]; then
  echo "→ setting hostname to $NEW_HOSTNAME"
  hostnamectl set-hostname "$NEW_HOSTNAME"
  # hostnamectl updates /etc/hostname but not /etc/hosts. Fix the
  # 127.0.1.1 line so name resolution stays sensible.
  sed -i "s/\b${CURRENT_HOSTNAME}\b/$NEW_HOSTNAME/g" /etc/hosts
else
  echo "✓ hostname unchanged"
fi
echo

# --------------------------------------------------------------------------
# 2. SSH host keys
# --------------------------------------------------------------------------

echo "→ regenerating SSH host keys"
rm -f /etc/ssh/ssh_host_*
ssh-keygen -A >/dev/null
# Restart sshd so new connections pick up the fresh keys. Existing
# sessions (e.g. yours, if you SSHed in to run this) stay alive — each
# has its own forked sshd that the restart doesn't touch.
systemctl restart ssh
echo "✓ new SSH host keys generated"
echo "  Note: next SSH connection will warn about a changed host key —"
echo "  that's expected. Remove the old line from your laptop's"
echo "  ~/.ssh/known_hosts and reconnect."
echo

# --------------------------------------------------------------------------
# 3. Optional: wipe runtime data
# --------------------------------------------------------------------------

PLATFORM_DIR="/opt/iot-platform"
if [[ -d "$PLATFORM_DIR/data" ]]; then
  read -rp "Wipe runtime data in $PLATFORM_DIR/data ? [y/N] " ans
  if [[ "${ans,,}" == "y" || "${ans,,}" == "yes" ]]; then
    echo "→ stopping platform"
    cd "$PLATFORM_DIR"
    docker compose down 2>/dev/null || true
    rm -rf "$PLATFORM_DIR"/data/*
    echo "→ restarting with a fresh database"
    docker compose up -d
    echo "✓ data wiped"
  else
    echo "✓ keeping existing data"
  fi
  echo
fi

# --------------------------------------------------------------------------
# 4. Reboot
# --------------------------------------------------------------------------

echo "✓ post-clone setup complete. A reboot is recommended so the new"
echo "  hostname propagates to every service."
read -rp "Reboot now? [Y/n] " ans
if [[ -z "$ans" || "${ans,,}" == "y" || "${ans,,}" == "yes" ]]; then
  reboot
fi
