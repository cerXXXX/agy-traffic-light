# 🚦 Antigravity Traffic Light (`agy-traffic-light`)

A sleek, real-time status indicator widget for **Google Antigravity (AGY)** agents. Designed for **Dank Material Shell (DMS)**, **Waybar**, **Niri**, **Hyprland**, **KDE Plasma**, and **System Tray**.

Displays the real-time activity of all your running agents (local and remote) right in your top bar.

---

## 🎨 Traffic Light States

| State | Indicator | Description | Animation |
| :--- | :---: | :--- | :--- |
| **Needs Approval** | 🔴 **Red** | Agent is waiting for user confirmation before executing a tool/command | Fast Alert Pulse (0.5s) |
| **Working** | 🟡 **Yellow** | Agent is thinking, planning, or actively executing a command/tool | Smooth Breathing Glow (1.0s) |
| **Idle / Ready** | 🟢 **Green** | Agent finished current turn and is ready for your next prompt | Solid Neon Glow |
| **Offline** | ⚪ **Grey** | No active agent sessions detected (or terminal closed) | Solid / Outline |

---

## 🌟 Key Features

* **Multi-Agent Aggregation**: Tracks multiple concurrent agents across different workspaces and servers.
  * Priority logic: `🔴 Attention Required > 🟡 Working > 🟢 Idle`.
* **Automatic Process Tracking**: Binds to terminal PID — closing the terminal tab immediately switches the light to offline.
* **Native Dank Material Shell (DMS) Plugin**: Native QML bar pill that scales dynamically with bar thickness and fits seamlessly into DankBar.
* **Waybar / System Tray Support**: Standard JSON stream for Waybar, plus AppIndicator / StatusNotifierItem for KDE/GNOME/etc.
* **Remote Agents Support**: Stream status from remote servers / VPS over **SSH reverse tunnel** or **Tailscale** with zero latency.
* **Interactive Popout**: Click the pill to see a detailed card of all active sessions and current tool/command execution.
* **AGY Ecosystem Ready**: Works identically with **Antigravity CLI**, **Antigravity 2.0**, and **Antigravity Desktop/IDE**.
* **Zero Bloat**: Core daemon runs on pure Python standard library (no heavy dependencies).

---

## 🏗 Architecture

```text
┌────────────────────────────────────────────────────────┐
│               Agents (Local & Remote)                  │
│                                                        │
│  [Local AGY CLI]    ──── (hooks.json) ────┐           │
│  [AGY Desktop]      ──── (hooks.json) ────┼───► POST  │
│  [Remote SSH VPS]   ──── (curl/hook)  ────┘   (9876)  │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Status Daemon (Local Hub)                  │
│  • Listens on http://127.0.0.1:9876                    │
│  • Tracks PID and prunes dead processes instantly      │
│  • Calculates global state: 🔴 / 🟡 / 🟢                │
└────────────────────────────────────────────────────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │ DMS / QML │ │  Waybar   │ │  System   │
       │ (DankBar) │ │ (module)  │ │   Tray    │
       └───────────┘ └───────────┘ └───────────┘
```

---

## 🚀 Quick Start & Installation

```bash
git clone https://github.com/cerXXXX/agy-traffic-light.git
cd agy-traffic-light
./scripts/install.sh
```

The installer automatically:
1. Links the Antigravity hook plugin to `~/.gemini/config/plugins/agy-traffic-light`
2. Enables and starts the user background daemon (`agy-traffic.service`)
3. Detects DMS and installs the native QML DankBar plugin (or provides Waybar configs)

---

## ⚙️ Panel Configurations & Environment Support

> [!NOTE]
> **Tested & Verified:** The widget design and behavior are currently tested and fully verified on **Niri + Dank Material Shell (DMS)**.
> Integrations for other desktop environments (Waybar, KDE Plasma, Hyprland, System Tray, Standalone GTK Overlay) are provided and implemented, but require user/community testing.

### A. Dank Material Shell (DMS) / Niri *(Tested & Verified)*

DMS plugin is included in [`examples/dms/`](examples/dms/).

To install or update the DMS plugin:
```bash
./examples/dms/install-dms-plugin.sh
```
This adds `"agyTraffic"` directly to `rightWidgets` in your DankBar configuration.

### B. Waybar Integration *(Requires Community Testing)*

Add to your `~/.config/waybar/config.jsonc`:

```jsonc
"custom/agy-traffic": {
    "format": "{text}",
    "return-type": "json",
    "interval": 1,
    "exec": "curl -s http://127.0.0.1:9876/waybar",
    "on-click": "curl -s -X POST http://127.0.0.1:9876/clear",
    "tooltip": true
}
```

Add CSS styles from [`examples/waybar/style.css`](examples/waybar/style.css) into your `~/.config/waybar/style.css`.

### C. System Tray Applet *(KDE Plasma, GNOME, XFCE, Cinnamon)*

Native StatusNotifierItem / AppIndicator with live dynamic menu, active sessions list, and neon icons:
```bash
python3 -m agy_traffic_light.tray
```
Or enable the user background service:
```bash
systemctl --user enable --now agy-traffic-tray.service
```

### D. Standalone Wayland GTK Widget *(Sway, Hyprland, River, Wayfire)*

Lightweight layer-shell overlay with an interactive details popout window that **automatically adapts its opening direction based on panel position** (top/bottom/left/right):
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
Or enable the user background service `systemd/agy-traffic-widget.service`.

---

## 🌐 Remote Agents Setup (SSH / VPS)

To monitor an agent running on a remote server:

1. **Install hook on the remote machine**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/cerXXXX/agy-traffic-light/main/examples/remote/remote-install.sh | bash
   ```
2. **Connect with SSH reverse port forwarding**:
   ```bash
   ssh -R 9876:localhost:9876 user@remote-server
   ```
Whenever Antigravity runs on the remote server, it forwards state changes over the encrypted SSH tunnel to your local traffic light!

---

## 🧪 Testing & Simulation

Test traffic light transitions (🟡 Thinking -> 🟡 Running -> 🔴 Approval -> 🟢 Done):

```bash
python3 scripts/simulate.py --name "my-project"
```

Simulate a remote server agent:
```bash
python3 scripts/simulate.py --name "prod-api" --remote
```

---

## 📄 License

MIT License. Contributions welcome!
