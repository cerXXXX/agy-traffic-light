#!/bin/bash
# Install Antigravity Traffic Light module into Waybar

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAYBAR_CONFIG_DIR="$HOME/.config/waybar"
CONFIG_FILE=""

echo "=== Installing Antigravity Traffic Light Waybar Module ==="

mkdir -p "$WAYBAR_CONFIG_DIR"

if [ -f "$WAYBAR_CONFIG_DIR/config.jsonc" ]; then
    CONFIG_FILE="$WAYBAR_CONFIG_DIR/config.jsonc"
elif [ -f "$WAYBAR_CONFIG_DIR/config" ]; then
    CONFIG_FILE="$WAYBAR_CONFIG_DIR/config"
else
    CONFIG_FILE="$WAYBAR_CONFIG_DIR/config.jsonc"
    echo "{}" > "$CONFIG_FILE"
fi

# 1. Update Waybar JSON/JSONC config
python3 -c "
import json, re, os, sys

config_path = os.path.expanduser('$CONFIG_FILE')
style_path = os.path.expanduser('$WAYBAR_CONFIG_DIR/style.css')
script_dir = '$SCRIPT_DIR'

def strip_comments(text):
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text

data = {}
raw_text = ''
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        raw_text = f.read().strip()
    if raw_text:
        try:
            data = json.loads(strip_comments(raw_text))
        except Exception as e:
            print(f'! Warning: Could not parse {config_path} as JSON ({e}). Creating backup and starter config.')
            os.rename(config_path, config_path + '.backup')
            data = {}

agy_module = {
    'format': '{text}',
    'return-type': 'json',
    'interval': 1,
    'exec': 'curl -s http://127.0.0.1:9876/waybar',
    'on-click-right': 'curl -s -X POST http://127.0.0.1:9876/clear',
    'tooltip': True
}

def inject_module(bar_dict):
    bar_dict['custom/agy-traffic'] = agy_module
    right = bar_dict.get('modules-right', [])
    if 'custom/agy-traffic' not in right and 'custom/agy-traffic' not in bar_dict.get('modules-left', []) and 'custom/agy-traffic' not in bar_dict.get('modules-center', []):
        if 'tray' in right:
            idx = right.index('tray')
            right.insert(idx, 'custom/agy-traffic')
        else:
            right.append('custom/agy-traffic')
        bar_dict['modules-right'] = right

if isinstance(data, list):
    for bar in data:
        if isinstance(bar, dict):
            inject_module(bar)
else:
    inject_module(data)

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print(f'✓ Added custom/agy-traffic to {config_path}')

# 2. Append CSS style if not already present
style_src = os.path.join(script_dir, 'style.css')
if os.path.exists(style_src):
    with open(style_src, 'r', encoding='utf-8') as f:
        css_to_add = f.read().strip()
    
    current_css = ''
    if os.path.exists(style_path):
        with open(style_path, 'r', encoding='utf-8') as f:
            current_css = f.read()
    
    if '#custom-agy-traffic' not in current_css:
        with open(style_path, 'a', encoding='utf-8') as f:
            f.write('\n\n/* Antigravity Traffic Light */\n' + css_to_add + '\n')
        print(f'✓ Appended traffic light CSS styles to {style_path}')
    else:
        print(f'✓ CSS styles already present in {style_path}')
"

# 3. Reload Waybar if running
if pgrep -x waybar >/dev/null 2>&1; then
    echo "Reloading Waybar..."
    killall -SIGUSR2 waybar 2>/dev/null || pkill -SIGUSR2 waybar 2>/dev/null || true
    echo "✓ Waybar reloaded."
fi

echo "=== Waybar Configuration Complete! ==="
