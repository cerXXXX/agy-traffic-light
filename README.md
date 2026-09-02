# 🚦 Antigravity Traffic Light

Real-time traffic light status indicator widget for **Google Antigravity (AGY)** agents. Designed for **Dank Material Shell (DMS)**, **Waybar**, **Niri**, **Hyprland**, **KDE Plasma**, and **System Tray**.

Displays the real-time activity of all your running agents (local and remote) right in your top or side bar.

---

## 🎨 Traffic Light States

| State | Indicator | Description | Animation |
| :--- | :---: | :--- | :--- |
| **Needs Approval** | 🔴 **Red** | Agent waiting for user confirmation before executing tool | Fast Alert Pulse (0.5s) |
| **Working** | 🟡 **Yellow** | Agent thinking, planning, or executing a tool/command | Smooth Breathing Glow (1.0s) |
| **Idle / Ready** | 🟢 **Green** | Agent finished turn and is ready for next prompt | Solid Neon Glow |
| **Offline** | ⚪ **Grey** | No active agent sessions (or terminal closed) | Dim Outline |

---

## 🚀 Quick Start (Automated Setup)

```bash
git clone https://github.com/cerXXXX/agy-traffic-light.git
cd agy-traffic-light
./scripts/install.sh
```

**What `./scripts/install.sh` sets up for ALL desktop environments:**
1. Links the Antigravity hook plugin to `~/.gemini/config/plugins/agy-traffic-light`.
2. Starts the core status daemon background service (`systemctl --user enable --now agy-traffic.service`).
3. Pre-installs user systemd units and auto-detects your desktop integration.

<details>
<summary><b>🛠️ Manual Installation (Without <code>install.sh</code>)</b></summary>

If you configure manually (e.g. for custom Waybar setups), you must set up the **Hook** and **Daemon**:

1. **Install Python package:**
   ```bash
   pip install -e .
   ```
2. **Link Antigravity Hook Plugin:**
   ```bash
   mkdir -p ~/.gemini/config/plugins
   ln -s "$(pwd)/plugin" ~/.gemini/config/plugins/agy-traffic-light
   ```
3. **Enable Background Status Daemon:**
   ```bash
   mkdir -p ~/.config/systemd/user
   cp systemd/*.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now agy-traffic.service
   ```
4. **Configure your panel / UI** from the sections below.
</details>

---

## 🖥️ Desktop Integrations & Background Services

> [!NOTE]
> **Tested & Verified:** The widget design and behavior are verified on **Niri + Dank Material Shell (DMS)**.
> Integrations for other environments (Waybar, System Tray, Standalone GTK) are fully implemented, but require community testing.

### A. Dank Material Shell (DMS) / Niri *(Verified)*
Installed automatically via `./scripts/install.sh` (or `./examples/dms/install-dms-plugin.sh`).
* Native QML bar pill in DankBar with neon double-ring styling.
* Interactive popout card with active sessions and configurable width (default 260px in DMS settings).
* Automatic direction-aware opening on horizontal (top/bottom) and vertical (left/right) bars.

### B. Waybar *(Requires Community Testing)*
Add to your `~/.config/waybar/config.jsonc`:
```jsonc
"custom/agy-traffic": {
    "format": "{text}",
    "return-type": "json",
    "interval": 1,
    "exec": "curl -s http://127.0.0.1:9876/waybar",
    "on-click-right": "curl -s -X POST http://127.0.0.1:9876/clear",
    "tooltip": true
}
```
Add styles from [`examples/waybar/style.css`](examples/waybar/style.css) into your `~/.config/waybar/style.css`.

### C. System Tray Applet *(Requires Community Testing)*
For KDE Plasma, GNOME (AppIndicator), XFCE, Cinnamon:
* **Primary background service:**
  ```bash
  systemctl --user enable --now agy-traffic-tray.service
  ```
* *Manual test launch:* `python3 -m agy_traffic_light.tray`

### D. Standalone Wayland GTK Widget *(Requires Community Testing)*
For Sway, Hyprland, River, Wayfire without DMS/Waybar:
* **Primary background service:**
  ```bash
  systemctl --user enable --now agy-traffic-widget.service
  ```
* *Manual test launch (with automatic popout direction):*
  ```bash
  # Top bar (popout opens downwards):
  python3 -m agy_traffic_light.widget --position top-right --margin-bar 4 --margin-side 280

  # Bottom bar (popout opens upwards):
  python3 -m agy_traffic_light.widget --position bottom-right --margin-bar 4 --margin-side 280

  # Left vertical bar (popout opens to the right):
  python3 -m agy_traffic_light.widget --position left-top --margin-bar 4 --margin-side 100

  # Right vertical bar (popout opens to the left):
  python3 -m agy_traffic_light.widget --position right-top --margin-bar 4 --margin-side 100
  ```

---

## 🌐 Remote Agents Setup (SSH / VPS)

To monitor an agent running on a remote server:

1. **Install hook on remote server**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/cerXXXX/agy-traffic-light/main/examples/remote/remote-install.sh | bash
   ```
2. **Connect via SSH with reverse port forwarding**:
   ```bash
   ssh -R 9876:localhost:9876 user@remote-server
   ```
Agent state changes forward securely over the SSH tunnel to your local traffic light.

---

## 🧪 Testing & Simulation

Simulate local agent lifecycle (🟡 Thinking -> 🟡 Running -> 🔴 Approval -> 🟢 Done):
```bash
python3 scripts/simulate.py --name "my-project"
```

Simulate a remote server agent:
```bash
python3 scripts/simulate.py --name "prod-api" --remote
```

---

## 📄 License

MIT License.

