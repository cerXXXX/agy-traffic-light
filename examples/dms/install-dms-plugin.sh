#!/bin/bash
# Install Antigravity Traffic Light native widget plugin into Dank Material Shell (DMS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DMS_PLUGIN_DIR="$HOME/.config/DankMaterialShell/plugins/agyTraffic"
DMS_CONFIG_DIR="$HOME/.config/DankMaterialShell"

echo "=== Installing Antigravity Traffic Light DMS Plugin ==="

# 1. Copy plugin files
mkdir -p "$DMS_PLUGIN_DIR"
cp -r "$SCRIPT_DIR/agyTraffic/"* "$DMS_PLUGIN_DIR/"
echo "✓ Plugin copied to $DMS_PLUGIN_DIR"

# 2. Enable in plugin_settings.json
mkdir -p "$DMS_CONFIG_DIR"
python3 -c "
import json, os

path = os.path.expanduser('~/.config/DankMaterialShell/plugin_settings.json')
data = {}
if os.path.exists(path):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except Exception:
        data = {}

if 'agyTraffic' not in data:
    data['agyTraffic'] = {}
data['agyTraffic']['enabled'] = True

with open(path, 'w') as f:
    json.dump(data, f, indent=2)
print('✓ Enabled agyTraffic in plugin_settings.json')
"

# 3. Add to DankBar settings.json if not present
python3 -c "
import json, os

path = os.path.expanduser('~/.config/DankMaterialShell/settings.json')
if os.path.exists(path):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        modified = False
        for bar in data.get('barConfigs', []):
            right = bar.get('rightWidgets', [])
            if 'agyTraffic' not in right:
                if 'systemTray' in right:
                    idx = right.index('systemTray')
                    right.insert(idx, 'agyTraffic')
                else:
                    right.insert(0, 'agyTraffic')
                bar['rightWidgets'] = right
                modified = True
        
        if modified:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            print('✓ Added agyTraffic to DankBar rightWidgets')
        else:
            print('✓ agyTraffic is already present in barConfigs')
    except Exception as e:
        print(f'! Note: Could not auto-modify settings.json ({e}). You can add it in DMS settings UI.')
"

# 4. Restart DMS if running
if systemctl --user is-active --quiet dms.service 2>/dev/null; then
    echo "Restarting dms.service..."
    systemctl --user restart dms.service
    echo "✓ dms.service restarted."
fi

echo "=== DMS Plugin Installation Complete! ==="
