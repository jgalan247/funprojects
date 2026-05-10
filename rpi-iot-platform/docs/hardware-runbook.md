# Phase 1 — Hardware runbook

Step-by-step setup for the core device. Follow this in order. Tick each
checkpoint before moving on.

## 1. Bill of materials

| Item | Notes |
| --- | --- |
| Raspberry Pi 4B, 8GB RAM | The only supported SBC for v1. |
| Official Raspberry Pi 5" DSI touchscreen | Connects via DSI ribbon + 4 jumper wires for power. |
| MicroSD card, 32GB minimum, A1/A2 rated | A2 preferred for random IO. SanDisk Extreme or Samsung Pro Endurance recommended. |
| Official Raspberry Pi 27W USB-C PSU | For bench setup. |
| USB-C power bank, ≥10,000 mAh, ≥3 A output | For portable use. See [§6 Power](#6-power-bank-selection). |
| MicroHDMI → HDMI cable | Backup display during initial setup. |
| USB keyboard + mouse | First-boot setup. SSH after that. |
| Ethernet cable | Optional but useful for the very first boot. |
| Sturdy case with touchscreen mount | A "SmartiPi Touch Pro" or equivalent. |

## 2. Flash Raspberry Pi OS 64-bit

Use **Raspberry Pi Imager** (latest, on a separate machine).

1. Choose device: **Raspberry Pi 4**.
2. Choose OS: **Raspberry Pi OS (64-bit)** — Bookworm, with desktop. *Not*
   Lite, because the touchscreen needs the desktop session for v1.
3. Choose storage: the microSD card.
4. Click the **gear / settings** icon and pre-configure:
   - Hostname: `pi-iot-01` (or your chosen scheme).
   - Username: e.g. `coderra`. Set a strong password.
   - Wireless LAN: SSID, passphrase, country = `GB` (or `JE` if available;
     `GB` works fine for the Channel Islands).
   - Locale: timezone `Europe/Jersey`, keyboard `gb`.
   - Enable **SSH** with **password authentication** for first boot. We'll
     swap to keys in §5.
5. Write image and verify.

✅ Checkpoint: card writes successfully; Imager confirms verification passed.

## 3. First boot (headless or HDMI)

**Option A — HDMI keyboard + mouse:** Plug in microHDMI, USB peripherals,
power. Boot to desktop, complete any first-run wizard if it appears.

**Option B — headless via Ethernet:**

1. Insert SD card, plug Ethernet, power on.
2. From a laptop on the same LAN:
   ```
   ssh coderra@pi-iot-01.local
   ```
   If `.local` resolution fails, find the IP from your router and use that.

Run:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

✅ Checkpoint: SSH reaches the Pi; `uname -m` reports `aarch64`; `apt` is
clean.

## 4. Install and configure the official 5" touchscreen

The official 5" DSI touchscreen needs the DSI ribbon connected to the Pi's
DSI1 connector and four jumper wires for 5V/GND/SDA/SCL (per the screen's
included guide). With Bookworm, it is detected automatically — no manual
overlay edits are required for the standard touchscreen.

1. Power off, connect the screen, power on.
2. Confirm desktop renders on the 5" panel.
3. Calibrate touch (settings shortcut on the desktop, or
   `~/.config/lxsession/...` if needed).
4. Test orientation. If the panel is mounted upside down, in
   `/boot/firmware/config.txt` add (under `[all]`):
   ```
   display_lcd_rotate=2
   ```
   Reboot.

✅ Checkpoint: desktop renders on the 5" panel; touch is responsive; tap
accuracy is acceptable.

## 5. Lock down SSH (key-only)

From your laptop:

```bash
ssh-keygen -t ed25519 -C "pi-iot-01" -f ~/.ssh/pi_iot_01
ssh-copy-id -i ~/.ssh/pi_iot_01.pub coderra@pi-iot-01.local
```

On the Pi, edit `/etc/ssh/sshd_config.d/99-iot.conf`:

```
PasswordAuthentication no
PermitRootLogin no
```

Then:

```bash
sudo systemctl restart ssh
```

Verify you can still log in with the key, and that password login is refused.

✅ Checkpoint: key login works; password login refused.

## 6. Power bank selection

The Pi 4B can draw up to ~15W under load with a touchscreen attached.

Minimum acceptable power bank:

- **USB-C output, 5V/3A** sustained (≥15W).
- **Pass-through charging** is ideal — lets the Pi keep running while the bank
  charges from a wall PSU.
- **Capacity ≥10,000 mAh** for ~2–3 hours of classroom use; **20,000 mAh** for
  a full lesson day with margin.
- Avoid power banks that auto-shutdown on low draw (some "smart" banks turn
  off if current dips below ~100 mA).

Test:

1. Charge bank fully.
2. Boot the Pi from the bank with the touchscreen on.
3. Run `vcgencmd get_throttled` after 5 minutes of normal use.
   - `0x0` = healthy.
   - Any non-zero value with the under-voltage bit set (`0x50000` etc.) means
     the bank or cable is inadequate.

✅ Checkpoint: Pi boots from the bank, touchscreen runs, no under-voltage
flags after 10 minutes of light use.

## 7. Networking and remote access

### Wi-Fi

Already configured by Imager. Verify:

```bash
nmcli device status
nmcli -t -f active,ssid dev wifi | grep '^yes'
```

### Bluetooth

```bash
bluetoothctl show
```

Should report `Powered: yes`.

### VNC (optional, for remote desktop)

```bash
sudo apt install -y realvnc-vnc-server
sudo raspi-config nonint do_vnc 0
```

Connect from a laptop with RealVNC Viewer to `pi-iot-01.local:5900`.

✅ Checkpoint: Wi-Fi connected; Bluetooth powered; VNC reachable from LAN.

## 8. Folder layout on the device

Create the working tree once:

```bash
sudo mkdir -p /opt/iot-platform
sudo chown $USER:$USER /opt/iot-platform
cd /opt/iot-platform
git init
```

The repository structure planned for this directory is documented in
[`folder-layout.md`](folder-layout.md). Don't pre-create directories yet —
they appear when Phase 2 begins.

✅ Checkpoint: `/opt/iot-platform` exists, owned by your user, initialised as
a git repo.

## 9. Auto-start strategy (deferred)

Auto-launching the Vue dashboard in kiosk mode on boot is a Phase 5 concern.
For Phase 1 we only need the desktop to come up reliably. The current plan
(documented here so it is not forgotten) is:

- A `wayfire`/`labwc` autostart entry that launches Chromium in kiosk mode
  pointing at `http://localhost:8080`.
- Or a systemd user service with the same effect.

Do **not** configure auto-start until Phase 5.

## 10. Phase 1 verification checklist

- [ ] OS: 64-bit Raspberry Pi OS Bookworm, fully updated.
- [ ] Hostname set; user account created.
- [ ] SSH: key-only, password auth disabled.
- [ ] Wi-Fi: connected and persistent across reboots.
- [ ] Bluetooth: powered.
- [ ] Touchscreen: renders and responds to touch.
- [ ] Power bank: boots and runs without under-voltage warnings for ≥10 min.
- [ ] `/opt/iot-platform` exists and is git-initialised.
- [ ] No additional services installed yet — clean slate for Phase 2.

Once every box is ticked, proceed to
[`implementation-plan.md`](implementation-plan.md) §Phase 2.
