#!/usr/bin/env bash
# Antigravity Traffic Light - macOS Installer

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_TARGET="$HOME/.gemini/config/plugins/agy-traffic-light"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.antigravity.traffic-light.plist"

echo "=========================================="
echo "Installing Antigravity Traffic Light (macOS)"
echo "=========================================="

# 1. Install / Link Antigravity Plugin
echo "[1/4] Linking Antigravity hook plugin to $PLUGIN_TARGET..."
mkdir -p "$HOME/.gemini/config/plugins"
rm -rf "$PLUGIN_TARGET"
ln -sf "$REPO_DIR/plugin" "$PLUGIN_TARGET"
echo "✓ Antigravity hook plugin linked."

# 2. Setup Python package and dependencies
echo "[2/4] Installing Python package & dependencies (psutil, pystray, Pillow)..."
if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install -e "$REPO_DIR" --break-system-packages 2>/dev/null || \
    python3 -m pip install -e "$REPO_DIR" 2>/dev/null || \
    echo "! Note: Running with current Python environment."
else
    echo "Error: python3 not found. Please install Python 3 (e.g. via Homebrew: brew install python)."
    exit 1
fi

# 3. Setup launchd background service
echo "[3/4] Configuring launchd LaunchAgent for daemon background autostart..."
mkdir -p "$LAUNCH_AGENTS_DIR"
cp "$REPO_DIR/scripts/$PLIST_NAME" "$LAUNCH_AGENTS_DIR/"

# Replace python3 path in plist with actual current python3 path
PYTHON_PATH="$(command -v python3)"
sed -i '' "s|<string>python3</string>|<string>$PYTHON_PATH</string>|g" "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true

# Unload previous instance if loaded and load new
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
launchctl load -w "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
echo "✓ Core daemon LaunchAgent ($PLIST_NAME) loaded and active."

# 4. Status and Menu Bar Tray Info
echo "[4/4] Setting up Menu Bar Status Indicator..."
echo "✓ To start the Menu Bar indicator icon, run:"
echo "    agy-traffic-tray"
echo "  or in background:"
echo "    nohup python3 -m agy_traffic_light.tray >/dev/null 2>&1 &"

echo ""
echo "=========================================="
echo "Installation Successful on macOS!"
echo "=========================================="
echo "✓ Core Daemon: http://127.0.0.1:9876 (running in background)"
echo "✓ Test State: python3 scripts/simulate.py"
echo "💡 To uninstall at any time: ./scripts/uninstall-macos.sh (or agy-traffic-uninstall)"
echo "=========================================="
