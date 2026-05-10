#!/usr/bin/env bash
# Configure Chromium kiosk autostart on the Pi.
#
# Drops an XDG autostart entry under ~/.config/autostart/ that launches
# Chromium full-screen pointing at http://localhost on every login.
#
# Idempotent — safe to re-run.

set -euo pipefail

URL="${1:-http://localhost}"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/iot-dashboard.desktop"

echo "→ Ensuring Chromium is installed…"
if ! command -v chromium-browser >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y chromium-browser
fi

# Pick whichever binary exists.
if command -v chromium-browser >/dev/null 2>&1; then
  CHROMIUM=chromium-browser
else
  CHROMIUM=chromium
fi

mkdir -p "$AUTOSTART_DIR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Pi IoT Dashboard
Comment=Launch the dashboard full-screen at login.
Exec=$CHROMIUM --kiosk --noerrdialogs --disable-translate --disable-features=TranslateUI --no-first-run --start-fullscreen --check-for-update-interval=31536000 $URL
X-GNOME-Autostart-enabled=true
Terminal=false
EOF

echo "✓ Wrote $DESKTOP_FILE"
echo
echo "Reboot or log out and back in for kiosk mode to take effect."
echo "To exit kiosk during a lesson: Ctrl+F4 closes the window, Alt+F4 quits Chromium."
