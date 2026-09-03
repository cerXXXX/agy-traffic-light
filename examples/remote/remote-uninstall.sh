#!/bin/bash
# Script to uninstall Antigravity Traffic Light hook from a remote SSH server.

set -e

PLUGIN_DIR="$HOME/.gemini/config/plugins/agy-traffic-light"

echo "=== Uninstalling Antigravity Traffic Light Remote Hook ==="

if [ -e "$PLUGIN_DIR" ]; then
    rm -rf "$PLUGIN_DIR"
    echo "✓ Remote hook removed from $PLUGIN_DIR"
else
    echo "• Remote hook not found at $PLUGIN_DIR (already uninstalled)"
fi

echo "=== Remote Hook Uninstallation Complete! ==="
