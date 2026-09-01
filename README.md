# 🚦 Antigravity Traffic Light (`agy-traffic-light`)

A sleek, real-time status indicator widget for **Google Antigravity (AGY)** agents. Designed for **Waybar**, **DMS (Dank Material Shell)**, **Niri**, **Hyprland**, **KDE Plasma**, and **System Tray**.

Displays the real-time activity of all your running agents (local and remote) right in your top bar.

---

## 🎨 Traffic Light States

| State | Indicator | Description |
| :--- | :---: | :--- |
| **Needs Approval** | 🔴 **Red** | Agent is waiting for user confirmation before executing a tool/command |
| **Working** | 🟡 **Yellow** | Agent is thinking, planning, or actively executing a command/tool |
| **Idle / Done** | 🟢 **Green** | Agent has finished the task and is waiting for your next prompt |
| **Offline** | ⚪ **Grey** | No active agent sessions detected |

---

## 🌟 Key Features

* **Multi-Agent Aggregation**: Tracks multiple concurrent agents across different workspaces.
  * Priority logic: `🔴 Attention Required > 🟡 Working > 🟢 Idle`.
* **Remote Agents Support**: Stream status from remote servers / VPS over **SSH reverse tunnel** or **Tailscale** with zero latency.
* **Rich Tooltips**: Hover over the circle to see a breakdown of all active sessions and what tool each agent is running.
* **AGY Ecosystem Ready**: Works identically with **Antigravity CLI**, **Antigravity 2.0**, and **Antigravity Desktop/IDE**.
* **Zero Bloat**: Core daemon runs on pure Python standard library (no heavy dependencies).
* **Multiple Output Formats**: Direct JSON polling for Waybar, SSE stream, or AppIndicator / StatusNotifierItem tray icon.

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
│  • Aggregates all active sessions                      │
│  • Calculates global state: 🔴 / 🟡 / 🟢                │
└────────────────────────────────────────────────────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │  Waybar / │ │  System   │ │  Desktop  │
       │    DMS    │ │   Tray    │ │  Notify   │
       │ (circle)  │ │ (applet)  │ │ (alerts)  │
       └───────────┘ └───────────┘ └───────────┘
```

---

## 🚀 Quick Start & Installation

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/agy-traffic-light.git
cd agy-traffic-light
./scripts/install.sh
```

The installer will:
1. Link the plugin into `~/.gemini/config/plugins/agy-traffic-light`
2. Enable and start the user systemd service (`agy-traffic.service`)

---

## ⚙️ Panel Configurations

### A. Waybar Integration

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

Add to your `~/.config/waybar/style.css`:

```css
#custom-agy-traffic {
    font-size: 14px;
    padding: 0 8px;
    margin: 0 4px;
}

#custom-agy-traffic.idle {
    color: #a6e3a1; /* Green */
    text-shadow: 0 0 6px rgba(166, 227, 161, 0.6);
}

#custom-agy-traffic.running {
    color: #f9e2af; /* Yellow */
    text-shadow: 0 0 8px rgba(249, 226, 175, 0.8);
    animation: agy-pulse 1.5s infinite;
}

#custom-agy-traffic.ask {
    color: #f38ba8; /* Red */
    text-shadow: 0 0 10px rgba(243, 139, 168, 0.9);
    animation: agy-blink 0.8s infinite;
}

#custom-agy-traffic.offline {
    color: #6c7086;
}

@keyframes agy-pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1.0; }
    100% { opacity: 0.6; }
}

@keyframes agy-blink {
    0% { opacity: 1.0; }
    50% { opacity: 0.2; }
    100% { opacity: 1.0; }
}
```

---

### B. Dank Material Shell (DMS) / Quickshell / Niri

Since DMS supports standard Wayland applets and system tray:
* The system tray applet will appear automatically in DMS when `agy-traffic-tray` is started:
```bash
pip install pystray pillow
python3 -m agy_traffic_light.tray &
```

---

## 🌐 Remote Agents Setup (SSH / VPS)

To monitor an agent running on a remote server:

1. **Install hook on the remote machine**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/yourusername/agy-traffic-light/main/examples/remote/remote-install.sh | bash
   ```
2. **Connect with SSH reverse port forwarding**:
   ```bash
   ssh -R 9876:localhost:9876 user@remote-server
   ```
Whenever Antigravity runs on the remote server, it forwards state changes over the encrypted SSH tunnel to your local traffic light!

---

## 🧪 Testing & Simulation

Test your traffic light transitions (🟡 Thinking -> 🟡 Running -> 🔴 Approval -> 🟢 Done):

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
