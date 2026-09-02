# 🚦 Antigravity Traffic Light

Real-time traffic light status indicator widget for **Google Antigravity (AGY)** agents.
Native cross-platform support for **Linux** (Dank Material Shell / Niri, Waybar, System Tray, Wayland Layer-Shell), **macOS** (Menu Bar), and **Windows** (Taskbar System Tray).

Displays the real-time activity of all your running agents (local and remote) right in your top bar, menu bar, or system tray.

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

### Linux
```bash
git clone https://github.com/cerXXXX/agy-traffic-light.git
cd agy-traffic-light
./scripts/install.sh
```

### macOS
```bash
git clone https://github.com/cerXXXX/agy-traffic-light.git
cd agy-traffic-light
./scripts/install-macos.sh
```
* Sets up hook plugin, installs dependencies, and enables `launchd` background LaunchAgent (`com.antigravity.traffic-light.plist`).
* Run `agy-traffic-tray` to display the real-time indicator in the macOS Menu Bar.

### Windows
Open PowerShell as your current user:
```powershell
git clone https://github.com/cerXXXX/agy-traffic-light.git
cd agy-traffic-light
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```
* Automatically creates NTFS plugin junction, installs package dependencies, and places background VBS runners in your Startup folder for seamless background operation without console windows.

---

## 🖥️ Desktop Integrations

> [!NOTE]
> **Reference Implementation:** Developed and verified on **Niri + Dank Material Shell (DMS)**.
> All other environments (macOS Menu Bar, Windows System Tray, Waybar, Standalone GTK) are fully implemented, but require community testing.

### 1. Dank Material Shell (DMS) / Niri *(Verified)*
* Native QML bar pill in DankBar with neon double-ring styling.
* Direction-aware popout card with active session details and configurable width.

### 2. System Tray & Menu Bar (macOS, Windows, Linux) *(Requires Testing)*
* Unified cross-platform applet via `agy-traffic-tray` (powered by `pystray`, with Ayatana fallback on Linux).
* Displays the live glowing indicator dot and active sessions menu in macOS Menu Bar, Windows Taskbar, and desktop trays (KDE, GNOME, XFCE).

### 3. Waybar & Standalone Wayland Overlays (Linux) *(Requires Testing)*
* **Waybar**: Native JSON module auto-configured into `config.jsonc` & `style.css`.
* **Standalone GTK Widget**: Floating layer-shell overlay for Sway, Hyprland, River, etc. (`--position top-right/bottom-right/etc.`).

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

