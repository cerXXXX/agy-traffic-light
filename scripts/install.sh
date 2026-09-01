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

# 3. Setup systemd user service for background daemon
echo "[3/4] Enabling systemd user service (agy-traffic.service)..."
mkdir -p "$SYSTEMD_USER_DIR"
cp "$REPO_DIR/systemd/agy-traffic.service" "$SYSTEMD_USER_DIR/"
systemctl --user daemon-reload
systemctl --user enable --now agy-traffic.service
echo "✓ agy-traffic.service enabled and running."

# 4. Detect and configure Desktop Environment / Panel
echo "[4/4] Checking desktop panel integrations..."
if [ -d "$HOME/.config/DankMaterialShell" ] || which dms >/dev/null 2>&1; then
    echo "-> Detected Dank Material Shell (DMS). Installing native DMS QML bar plugin..."
    bash "$REPO_DIR/examples/dms/install-dms-plugin.sh"
else
    echo "-> For Waybar, add the module from examples/waybar/ into ~/.config/waybar/config.jsonc"
fi

echo ""
echo "=========================================="
echo "Installation Successful!"
echo "=========================================="
echo "✓ Daemon: http://127.0.0.1:9876"
echo "✓ Simulation test: python3 scripts/simulate.py"
echo "=========================================="
