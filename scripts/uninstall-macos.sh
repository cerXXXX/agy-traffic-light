#!/usr/bin/env bash
# Antigravity Traffic Light - macOS Uninstaller

set -e

PLUGIN_TARGET="$HOME/.gemini/config/plugins/agy-traffic-light"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.antigravity.traffic-light.plist"

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
        -h|--help)
            echo "Usage: ./scripts/uninstall-macos.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --plugin-only    Only remove the Antigravity hook plugin"
            echo "  --keep-package   Remove plugin and background services, keep Python package"
            echo "  -y, --yes        Do not prompt for confirmation"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
    esac
done

echo "=========================================="
echo "Uninstalling Antigravity Traffic Light (macOS)"
echo "=========================================="

if [ "$AUTO_CONFIRM" = false ] && [ -t 0 ]; then
    if [ "$PLUGIN_ONLY" = true ]; then
        echo "This will remove the Antigravity hook plugin link."
    else
        echo "This will stop background services, remove LaunchAgent, and unlink the plugin."
    fi
    read -r -p "Are you sure you want to proceed? [y/N]: " confirm
    case "$confirm" in
        [yY][eE][sS]|[yY]) ;;
        *)
            echo "Uninstallation cancelled."
            exit 0
            ;;
    esac
fi

# 1. Remove Antigravity Plugin Link
echo "[1/4] Removing Antigravity hook plugin link..."
if [ -e "$PLUGIN_TARGET" ] || [ -L "$PLUGIN_TARGET" ]; then
    rm -rf "$PLUGIN_TARGET"
    echo "✓ Antigravity hook plugin link removed."
else
    echo "• Hook plugin link not found (skipped)."
fi

if [ "$PLUGIN_ONLY" = true ]; then
    echo ""
    echo "=========================================="
    echo "Plugin Removal Complete!"
    echo "=========================================="
    exit 0
fi

# 2. Stop and remove launchd LaunchAgent
echo "[2/4] Stopping and removing launchd background service..."
if [ -f "$LAUNCH_AGENTS_DIR/$PLIST_NAME" ]; then
    launchctl unload -w "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
    rm -f "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
    echo "✓ LaunchAgent ($PLIST_NAME) unloaded and removed."
else
    echo "• LaunchAgent plist not found (skipped)."
fi

# 3. Kill lingering processes
echo "[3/4] Stopping running processes..."
pkill -f "agy_traffic_light" 2>/dev/null || true
pkill -f "agy-traffic" 2>/dev/null || true
echo "✓ Stopped background processes."

# 4. Uninstall Python package
if [ "$KEEP_PACKAGE" = false ]; then
    echo "[4/4] Uninstalling Python package..."
    python3 -m pip uninstall -y agy-traffic-light 2>/dev/null || true
    echo "✓ Python package uninstalled."
else
    echo "[4/4] Keeping Python package as requested (--keep-package)."
fi

echo ""
echo "=========================================="
echo "Uninstallation Successful on macOS!"
echo "=========================================="
