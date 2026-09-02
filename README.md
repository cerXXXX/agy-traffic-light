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
> **Reference implementation:** Verified & tested primarily on **Niri + Dank Material Shell (DMS)**.
> All desktop environments (Linux Waybar/DMS/Tray, macOS Menu Bar, Windows System Tray) are fully supported.

### A. Dank Material Shell (DMS) / Niri *(Reference Implementation)*
* Native QML bar pill in DankBar with neon double-ring styling.
* Interactive popout card with active sessions and configurable width (default 260px in DMS settings).
* Direction-aware opening on horizontal (top/bottom) and vertical (left/right) bars.

### B. macOS Menu Bar *(Native)*
* Built-in cross-platform status indicator via `agy-traffic-tray` (pystray).
* Shows colored glowing traffic light dot in the top macOS Menu Bar with a clickable menu showing active agent sessions.
* Auto-managed in background via `launchd` (`~/Library/LaunchAgents/com.antigravity.traffic-light.plist`).

### C. Windows System Tray *(Native)*
* Displays the live indicator icon right in the Windows Taskbar Notification Area (System Tray).
* Right/left-click context menu displays active agent sessions, workspace names, and status.
* Starts silently on login via Windows Startup runner.

### D. Waybar (Linux)
* Auto-configured into `config.jsonc` and `style.css` by `./scripts/install.sh`.
* Native Waybar JSON module with live status tooltip and right-click to clear sessions.

### E. System Tray Applet (KDE, GNOME, XFCE, Cinnamon)
* Cross-platform tray via `pystray` with native `AyatanaAppIndicator` fallback.
* StatusNotifierItem with live dynamic sessions menu and neon icons.

### F. Standalone Wayland GTK Widget
* For Sway, Hyprland, River, Wayfire without DMS/Waybar.
* Floating layer-shell overlay with an interactive popout window.
* Position (top/bottom/left/right) is selected during installation or customizable via `--position`.

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

