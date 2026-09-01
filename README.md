# 🚦 Antigravity Traffic Light (`agy-traffic-light`)

A sleek, real-time status indicator widget for **Google Antigravity (AGY)** agents. Designed for **Dank Material Shell (DMS)**, **Waybar**, **Niri**, **Hyprland**, **KDE Plasma**, and **System Tray**.

Displays the real-time activity of all your running agents (local and remote) right in your top bar.

---

## 🎨 Traffic Light States

| State | Indicator | Description | Animation |
| :--- | :---: | :--- | :--- |
| **Needs Approval** | 🔴 **Red** | Agent is waiting for user confirmation before executing a tool/command | Fast Alert Pulse (0.5s) |
| **Working** | 🟡 **Yellow** | Agent is thinking, planning, or actively executing a command/tool | Smooth Breathing Glow (1.0s) |
| **Idle / Done** | 🟢 **Green** | Agent has finished the task and is waiting for your next prompt | Solid Neon Glow |
| **Offline** | ⚪ **Grey** | No active agent sessions detected | Subtle outline |

---

## 🌟 Key Features

* **Multi-Agent Aggregation**: Tracks multiple concurrent agents across different workspaces and servers.
  * Priority logic: `🔴 Attention Required > 🟡 Working > 🟢 Idle`.
* **Native Dank Material Shell (DMS) Plugin**: Native QML bar pill that fits seamlessly into DankBar alongside CPU, RAM, battery, and clipboard monitors.
* **Waybar / System Tray Support**: Standard JSON stream for Waybar, plus AppIndicator / StatusNotifierItem for KDE/GNOME/etc.
* **Remote Agents Support**: Stream status from remote servers / VPS over **SSH reverse tunnel** or **Tailscale** with zero latency.
* **Interactive Popout**: Click the pill to see a detailed card of all active sessions, current tool/command execution, and a button to clear finished sessions.
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
│  • Aggregates all active sessions                      │
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

## ⚙️ Panel Configurations

### A. Dank Material Shell (DMS) / Niri

DMS plugin is included in [`examples/dms/`](examples/dms/).

To install or update the DMS plugin:
```bash
./examples/dms/install-dms-plugin.sh
```
This adds `"agyTraffic"` directly to `rightWidgets` in your DankBar configuration.

### B. Waybar Integration

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
