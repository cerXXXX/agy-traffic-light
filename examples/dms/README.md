# Dank Material Shell (DMS) Plugin Integration

This directory contains the first-class native QML plugin for **Dank Material Shell (DMS)** / Quickshell.

## Features in DMS
- **Native DankBar Pill**: Sits as a first-class citizen widget directly in the bar alongside battery, clipboard, CPU/RAM monitors, etc.
- **Dynamic Proportional Scaling**: Adapts to any bar thickness and monitor scaling without clipping.
- **Interactive Material Popout**: Clicking the pill opens a Material Design popup showing:
  - Active local & remote sessions
  - Currently executing tool / command
  - Button to clear completed sessions
- **Neon Double-Ring Design**: Smooth glowing animated status indicators.

## Installation

### Automatic (1-Click)
```bash
./examples/dms/install-dms-plugin.sh
```

### Manual Installation
1. Copy the plugin directory to DMS plugins folder:
   ```bash
   mkdir -p ~/.config/DankMaterialShell/plugins/
   cp -r examples/dms/agyTraffic ~/.config/DankMaterialShell/plugins/
   ```
2. Enable the plugin in `~/.config/DankMaterialShell/plugin_settings.json`:
   ```json
   {
     "agyTraffic": {
       "enabled": true
     }
   }
   ```
3. Add `"agyTraffic"` to `rightWidgets`, `centerWidgets`, or `leftWidgets` in `~/.config/DankMaterialShell/settings.json` (or use the DMS Settings GUI under *DankBar -> Widgets*).
4. Restart DMS:
   ```bash
   systemctl --user restart dms.service
   ```
