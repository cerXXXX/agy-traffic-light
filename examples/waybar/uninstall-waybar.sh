#!/bin/bash
# Uninstall Antigravity Traffic Light module from Waybar

set -e

WAYBAR_CONFIG_DIR="$HOME/.config/waybar"
CONFIG_FILE=""

echo "=== Uninstalling Antigravity Traffic Light Waybar Module ==="

if [ -f "$WAYBAR_CONFIG_DIR/config.jsonc" ]; then
    CONFIG_FILE="$WAYBAR_CONFIG_DIR/config.jsonc"
elif [ -f "$WAYBAR_CONFIG_DIR/config" ]; then
    CONFIG_FILE="$WAYBAR_CONFIG_DIR/config"
fi

# 1. Remove from Waybar JSON/JSONC config
if [ -n "$CONFIG_FILE" ] && [ -f "$CONFIG_FILE" ]; then
    python3 -c "
import json, re, os, sys

config_path = os.path.expanduser('$CONFIG_FILE')

def strip_comments(text):
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text

if os.path.exists(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            raw = f.read().strip()
        
        if raw:
            data = json.loads(strip_comments(raw))
            modified = False

            def remove_module(bar_dict):
                nonlocal modified
                if 'custom/agy-traffic' in bar_dict:
                    del bar_dict['custom/agy-traffic']
                    modified = True
                for sec in ('modules-right', 'modules-center', 'modules-left'):
                    arr = bar_dict.get(sec, [])
                    if 'custom/agy-traffic' in arr:
                        bar_dict[sec] = [m for m in arr if m != 'custom/agy-traffic']
                        modified = True

            if isinstance(data, list):
                for bar in data:
                    if isinstance(bar, dict):
                        remove_module(bar)
            elif isinstance(data, dict):
                remove_module(data)

            if modified:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                print(f'✓ Removed custom/agy-traffic from {config_path}')
            else:
                print(f'• custom/agy-traffic was not found in {config_path}')
    except Exception as e:
        print(f'! Warning: Could not clean Waybar config ({e})')
"
else
    echo "• No Waybar config file found (skipped)"
fi

# 2. Remove CSS from style.css
STYLE_PATH="$WAYBAR_CONFIG_DIR/style.css"
if [ -f "$STYLE_PATH" ]; then
    python3 -c "
import re, os

style_path = os.path.expanduser('$STYLE_PATH')
if os.path.exists(style_path):
    try:
        with open(style_path, 'r', encoding='utf-8') as f:
            css = f.read()

        pattern = r'(?:\n* /\* Antigravity Traffic Light \*/)?\s*#custom-agy-traffic[^{]*\{[^}]*\}(?:\s*#custom-agy-traffic\.[^{]*\{[^}]*\})*(?:\s*@keyframes agy-[a-zA-Z0-9_-]+\s*\{[^}]*\{[^}]*\}[^}]*\})*'
        new_css = re.sub(pattern, '', css, flags=re.DOTALL)

        # Fallback: remove any leftover #custom-agy-traffic or @keyframes agy- blocks
        new_css = re.sub(r'#custom-agy-traffic[^{]*\{[^}]*\}', '', new_css)
        new_css = re.sub(r'@keyframes agy-[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}', '', new_css)
        new_css = re.sub(r'/\* Antigravity Traffic Light \*/', '', new_css)

        if new_css != css:
            with open(style_path, 'w', encoding='utf-8') as f:
                f.write(new_css)
            print(f'✓ Removed traffic light styles from {style_path}')
        else:
            print(f'• No traffic light styles found in {style_path}')
    except Exception as e:
        print(f'! Warning: Could not clean Waybar style.css ({e})')
"
fi

# 3. Reload Waybar if running
if pgrep -x waybar >/dev/null 2>&1; then
    echo "Reloading Waybar..."
    killall -SIGUSR2 waybar 2>/dev/null || pkill -SIGUSR2 waybar 2>/dev/null || true
    echo "✓ Waybar reloaded."
fi

echo "=== Waybar Module Uninstallation Complete! ==="
