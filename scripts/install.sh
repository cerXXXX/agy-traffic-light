#!/bin/bash
# Antigravity Traffic Light - Local Installer

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_TARGET="$HOME/.gemini/config/plugins/agy-traffic-light"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=========================================="
echo "Installing Antigravity Traffic Light"
echo "=========================================="

# 1. Install / Link Plugin
echo "[1/4] Linking plugin to $PLUGIN_TARGET..."
mkdir -p "$HOME/.gemini/config/plugins"
rm -rf "$PLUGIN_TARGET"
ln -s "$REPO_DIR/plugin" "$PLUGIN_TARGET"
echo "✓ Plugin linked."

# 2. Install python package locally
echo "[2/4] Installing Python package (editable mode)..."
python3 -m pip install -e "$REPO_DIR" --break-system-packages 2>/dev/null || python3 -m pip install -e "$REPO_DIR" 2>/dev/null || echo "! Note: Python package can also be run directly from repo."

# 3. Setup systemd user service
echo "[3/4] Setting up systemd user service..."
mkdir -p "$SYSTEMD_USER_DIR"
cp "$REPO_DIR/systemd/agy-traffic.service" "$SYSTEMD_USER_DIR/"
systemctl --user daemon-reload
systemctl --user enable --now agy-traffic.service
echo "✓ agy-traffic.service enabled and started."

# 4. Verification
echo "[4/4] Verifying daemon..."
sleep 1
if curl -s http://127.0.0.1:9876/health | grep -q "ok"; then
    echo "✓ Daemon is running and healthy at http://127.0.0.1:9876"
else
    echo "! Daemon did not respond immediately, please check: systemctl --user status agy-traffic.service"
fi

echo ""
echo "=========================================="
echo "Installation Successful!"
echo "=========================================="
echo "Next steps:"
echo "1. Add the Waybar module to ~/.config/waybar/config.jsonc (see examples/waybar/)"
echo "2. Add CSS styles to ~/.config/waybar/style.css"
echo "3. Run simulation test: python3 scripts/simulate.py"
echo "=========================================="
