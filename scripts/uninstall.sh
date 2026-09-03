#!/bin/bash
# Antigravity Traffic Light - Local Uninstaller

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Auto-detect macOS
if [ "$(uname -s)" = "Darwin" ]; then
    echo "-> Detected macOS environment. Running macOS uninstaller..."
    exec bash "$REPO_DIR/scripts/uninstall-macos.sh" "$@"
fi

PLUGIN_TARGET="$HOME/.gemini/config/plugins/agy-traffic-light"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

PLUGIN_ONLY=false
KEEP_PACKAGE=false
AUTO_CONFIRM=false

for arg in "$@"; do
    case "$arg" in
        --plugin-only)
            PLUGIN_ONLY=true
            ;;
        --keep-package)
            KEEP_PACKAGE=true
            ;;
        -y|--yes)
            AUTO_CONFIRM=true
            ;;
        -a|--all)
            PLUGIN_ONLY=false
            KEEP_PACKAGE=false
            ;;
        -h|--help)
            echo "Usage: ./scripts/uninstall.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --plugin-only    Only remove the Antigravity hook plugin (~/.gemini/config/plugins/agy-traffic-light)"
            echo "  --keep-package   Remove plugin, services, and desktop integrations, but keep Python package"
            echo "  -a, --all        Perform complete uninstallation (default)"
            echo "  -y, --yes        Skip interactive confirmation"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
    esac
done

echo "=========================================="
echo "Uninstalling Antigravity Traffic Light"
echo "=========================================="

# Interactive prompt if no explicit flags provided and running in interactive terminal
if [ "$PLUGIN_ONLY" = false ] && [ "$KEEP_PACKAGE" = false ] && [ "$AUTO_CONFIRM" = false ] && [ -t 0 ]; then
    echo ""
    echo "Choose an uninstallation mode:"
    echo "  1) Full Uninstall (Plugin, systemd services, desktop integrations, Python package) [default]"
    echo "  2) Plugin only (Unlink Antigravity hook plugin, keep services & package)"
    echo "  3) Services & Plugin (Remove plugin & services, keep Python package installed)"
    echo "  4) Cancel"
    echo ""
    read -r -p "Select option [1-4, default: 1]: " choice
    case "$choice" in
        2)
            PLUGIN_ONLY=true
            ;;
        3)
            KEEP_PACKAGE=true
            ;;
        4)
            echo "Uninstallation cancelled."
            exit 0
            ;;
        *)
            # Full uninstall
            ;;
    esac
fi

# 1. Remove Antigravity Plugin Link
echo "[1/4] Removing Antigravity hook plugin link..."
if [ -e "$PLUGIN_TARGET" ] || [ -L "$PLUGIN_TARGET" ]; then
    rm -rf "$PLUGIN_TARGET"
    echo "✓ Antigravity hook plugin link removed ($PLUGIN_TARGET)."
else
    echo "• Antigravity hook plugin link not found (skipped)."
fi

# Exit early if plugin-only
if [ "$PLUGIN_ONLY" = true ]; then
    echo ""
    echo "=========================================="
    echo "Plugin Removal Complete!"
    echo "=========================================="
    echo "The Antigravity hook plugin has been unlinked."
    echo "Traffic light background daemon/widgets are untouched."
    exit 0
fi

# 2. Stop and remove systemd background services
echo "[2/4] Stopping and removing systemd user background services..."
if command -v systemctl >/dev/null 2>&1; then
    systemctl --user stop agy-traffic-widget.service agy-traffic-tray.service agy-traffic.service 2>/dev/null || true
    systemctl --user disable agy-traffic-widget.service agy-traffic-tray.service agy-traffic.service 2>/dev/null || true
    rm -f "$SYSTEMD_USER_DIR/agy-traffic.service"
    rm -f "$SYSTEMD_USER_DIR/agy-traffic-tray.service"
    rm -f "$SYSTEMD_USER_DIR/agy-traffic-widget.service"
    systemctl --user daemon-reload 2>/dev/null || true
    systemctl --user reset-failed 2>/dev/null || true
    echo "✓ systemd user services stopped and removed."
fi

# Stop any lingering processes
pkill -f "agy_traffic_light.daemon" 2>/dev/null || true
pkill -f "agy_traffic_light.tray" 2>/dev/null || true
pkill -f "agy_traffic_light.widget" 2>/dev/null || true
echo "✓ Background processes terminated."

# 3. Clean up Desktop Environment / Panel Integrations
echo "[3/4] Cleaning desktop environment integrations..."

# A. Dank Material Shell (DMS)
if [ -d "$HOME/.config/DankMaterialShell/plugins/agyTraffic" ] || \
   grep -q "agyTraffic" "$HOME/.config/DankMaterialShell/plugin_settings.json" 2>/dev/null || \
   grep -q "agyTraffic" "$HOME/.config/DankMaterialShell/settings.json" 2>/dev/null; then
    echo "-> Detected Dank Material Shell integration. Cleaning up DMS..."
    bash "$REPO_DIR/examples/dms/uninstall-dms-plugin.sh" || true
fi

# B. Waybar
if [ -f "$HOME/.config/waybar/config.jsonc" ] || [ -f "$HOME/.config/waybar/config" ] || [ -f "$HOME/.config/waybar/style.css" ]; then
    if grep -q "custom/agy-traffic" "$HOME/.config/waybar/config.jsonc" "$HOME/.config/waybar/config" 2>/dev/null || \
       grep -q "custom-agy-traffic" "$HOME/.config/waybar/style.css" 2>/dev/null; then
        echo "-> Detected Waybar integration. Cleaning up Waybar..."
        bash "$REPO_DIR/examples/waybar/uninstall-waybar.sh" || true
    fi
fi

# 4. Uninstall Python Package
if [ "$KEEP_PACKAGE" = false ]; then
    echo "[4/4] Uninstalling Python package (agy-traffic-light)..."
    python3 -m pip uninstall -y agy-traffic-light --break-system-packages 2>/dev/null || python3 -m pip uninstall -y agy-traffic-light 2>/dev/null || true
    echo "✓ Python package uninstalled."
else
    echo "[4/4] Keeping Python package as requested (--keep-package)."
fi

echo ""
echo "=========================================="
echo "Uninstallation Successful!"
echo "=========================================="
echo "✓ Antigravity hook plugin removed."
echo "✓ Background services stopped and cleared."
echo "✓ Desktop integrations cleaned up."
if [ "$KEEP_PACKAGE" = false ]; then
    echo "✓ Python package uninstalled."
fi
echo "=========================================="
