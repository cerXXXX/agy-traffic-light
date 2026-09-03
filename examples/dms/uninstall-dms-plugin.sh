#!/bin/bash
# Uninstall Antigravity Traffic Light widget plugin from Dank Material Shell (DMS)

set -e

DMS_PLUGIN_DIR="$HOME/.config/DankMaterialShell/plugins/agyTraffic"
DMS_CONFIG_DIR="$HOME/.config/DankMaterialShell"

echo "=== Uninstalling Antigravity Traffic Light DMS Plugin ==="

# 1. Remove plugin directory
if [ -d "$DMS_PLUGIN_DIR" ]; then
    rm -rf "$DMS_PLUGIN_DIR"
    echo "✓ Removed plugin folder $DMS_PLUGIN_DIR"
else
    echo "• Plugin folder not present (skipped)"
fi

# 2. Remove agyTraffic from plugin_settings.json
python3 -c "
import json, os

path = os.path.expanduser('~/.config/DankMaterialShell/plugin_settings.json')
if os.path.exists(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'agyTraffic' in data:
            del data['agyTraffic']
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print('✓ Removed agyTraffic from plugin_settings.json')
    except Exception as e:
        print(f'! Warning: Could not update plugin_settings.json: {e}')
"

# 3. Remove agyTraffic from DankBar settings.json
python3 -c "
import json, os

path = os.path.expanduser('~/.config/DankMaterialShell/settings.json')
if os.path.exists(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        modified = False
        for bar in data.get('barConfigs', []):
            for section in ('rightWidgets', 'centerWidgets', 'leftWidgets'):
                widgets = bar.get(section, [])
                if 'agyTraffic' in widgets:
                    bar[section] = [w for w in widgets if w != 'agyTraffic']
                    modified = True
        
        if modified:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print('✓ Removed agyTraffic from DankBar widgets in settings.json')
        else:
            print('• agyTraffic was not present in barConfigs')
    except Exception as e:
        print(f'! Warning: Could not update settings.json: {e}')
"

# 4. Restart DMS if running
if systemctl --user is-active --quiet dms.service 2>/dev/null; then
    echo "Restarting dms.service..."
    systemctl --user restart dms.service
    echo "✓ dms.service restarted."
fi

echo "=== DMS Plugin Uninstallation Complete! ==="
