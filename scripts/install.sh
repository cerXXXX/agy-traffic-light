#!/bin/bash
# Antigravity Traffic Light - Local Installer

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_TARGET="$HOME/.gemini/config/plugins/agy-traffic-light"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=========================================="
echo "Installing Antigravity Traffic Light"
echo "=========================================="

# 1. Install / Link Antigravity Plugin
echo "[1/4] Linking Antigravity hook plugin to $PLUGIN_TARGET..."
mkdir -p "$HOME/.gemini/config/plugins"
rm -rf "$PLUGIN_TARGET"
ln -s "$REPO_DIR/plugin" "$PLUGIN_TARGET"
echo "✓ Antigravity hook plugin linked."

# 2. Setup Python package
echo "[2/4] Setting up Python package..."
python3 -m pip install -e "$REPO_DIR" --break-system-packages 2>/dev/null || python3 -m pip install -e "$REPO_DIR" 2>/dev/null || echo "! Note: Python package runnable directly."

# 3. Setup systemd user services
echo "[3/4] Installing systemd user background services..."
mkdir -p "$SYSTEMD_USER_DIR"
cp "$REPO_DIR/systemd/agy-traffic.service" "$SYSTEMD_USER_DIR/"
cp "$REPO_DIR/systemd/agy-traffic-tray.service" "$SYSTEMD_USER_DIR/"
cp "$REPO_DIR/systemd/agy-traffic-widget.service" "$SYSTEMD_USER_DIR/"
systemctl --user daemon-reload
systemctl --user enable --now agy-traffic.service
echo "✓ Core daemon background service (agy-traffic.service) active."

# 4. Detect and configure Desktop Environment / Panel
echo "[4/4] Configuring desktop environment integration..."
INSTALLED_PANEL=false
DESKTOP_LOWER="$(echo "${XDG_CURRENT_DESKTOP:-$DESKTOP_SESSION}" | tr '[:upper:]' '[:lower:]')"

# A. Dank Material Shell (DMS)
if [ -d "$HOME/.config/DankMaterialShell" ] || which dms >/dev/null 2>&1; then
    echo "-> Detected Dank Material Shell (DMS). Installing native DMS QML bar plugin..."
    bash "$REPO_DIR/examples/dms/install-dms-plugin.sh"
    INSTALLED_PANEL=true
fi

# B. Waybar
if [ -d "$HOME/.config/waybar" ] || which waybar >/dev/null 2>&1; then
    echo "-> Detected Waybar. Auto-installing Waybar module and styles..."
    bash "$REPO_DIR/examples/waybar/install-waybar.sh"
    INSTALLED_PANEL=true
fi

# C. Traditional Desktop Environments (KDE, GNOME, XFCE, Cinnamon, MATE, LXQt) -> System Tray
if [ "$INSTALLED_PANEL" = false ]; then
    if [[ "$DESKTOP_LOWER" =~ (kde|plasma|gnome|xfce|cinnamon|mate|lxqt|deepin|dde|pantheon|unity) ]]; then
        echo "-> Detected desktop environment ($XDG_CURRENT_DESKTOP). Auto-enabling background System Tray service..."
        systemctl --user enable --now agy-traffic-tray.service
        echo "✓ agy-traffic-tray.service enabled and running in your system tray."
        INSTALLED_PANEL=true
    fi
fi

# D. Standalone Wayland Compositors (Hyprland, Sway, River, Wayfire) without DMS/Waybar
if [ "$INSTALLED_PANEL" = false ]; then
    if [ "$XDG_SESSION_TYPE" = "wayland" ] || [[ "$DESKTOP_LOWER" =~ (hyprland|sway|river|wayfire|niri|labwc) ]]; then
        echo "-> Detected Wayland compositor ($XDG_CURRENT_DESKTOP). Auto-enabling standalone GTK overlay widget..."
        systemctl --user enable --now agy-traffic-widget.service
        echo "✓ agy-traffic-widget.service enabled and running."
        INSTALLED_PANEL=true
    fi
fi

# Fallback
if [ "$INSTALLED_PANEL" = false ]; then
    echo "-> Pre-installed background services in ~/.config/systemd/user/:"
    echo "   • System Tray:    systemctl --user enable --now agy-traffic-tray.service"
    echo "   • Wayland Widget: systemctl --user enable --now agy-traffic-widget.service"
fi

echo ""
echo "=========================================="
echo "Installation Successful!"
echo "=========================================="
echo "✓ Core Daemon: http://127.0.0.1:9876 (running in background)"
echo "✓ Test State: python3 scripts/simulate.py"
echo "=========================================="
