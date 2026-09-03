#!/usr/bin/env python3
"""
Antigravity Traffic Light - Cross-Platform Uninstaller CLI
Removes Antigravity hook plugins, stops background services,
cleans desktop environment integrations, and uninstalls the package.
"""

import sys
import os
import shutil
import subprocess
import argparse
import platform
from pathlib import Path


def get_plugin_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("USERPROFILE", "~"))
    else:
        base = Path.home()
    return (base / ".gemini" / "config" / "plugins" / "agy-traffic-light").resolve()


def remove_plugin_link(plugin_dir: Path) -> bool:
    print(f"[1/4] Removing Antigravity hook plugin at {plugin_dir}...")
    if not plugin_dir.exists() and not plugin_dir.is_symlink():
        print("• Antigravity hook plugin not found (already removed).")
        return False

    try:
        if plugin_dir.is_symlink() or plugin_dir.is_file():
            plugin_dir.unlink()
        elif plugin_dir.is_dir():
            shutil.rmtree(plugin_dir)
        print("✓ Antigravity hook plugin removed.")
        return True
    except Exception as e:
        print(f"! Failed to remove plugin link: {e}")
        return False


def stop_linux_services():
    print("[2/4] Stopping and removing systemd user services...")
    services = ["agy-traffic-widget.service", "agy-traffic-tray.service", "agy-traffic.service"]
    user_systemd = Path.home() / ".config" / "systemd" / "user"

    for s in services:
        subprocess.run(["systemctl", "--user", "stop", s], capture_output=True)
        subprocess.run(["systemctl", "--user", "disable", s], capture_output=True)
        unit_file = user_systemd / s
        if unit_file.exists():
            try:
                unit_file.unlink()
            except Exception:
                pass

    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    subprocess.run(["systemctl", "--user", "reset-failed"], capture_output=True)
    subprocess.run(["pkill", "-f", "agy_traffic_light"], capture_output=True)
    subprocess.run(["pkill", "-f", "agy-traffic"], capture_output=True)
    print("✓ Background services stopped and unit files removed.")


def stop_macos_services():
    print("[2/4] Stopping launchd background service...")
    agent_plist = Path.home() / "Library" / "LaunchAgents" / "com.antigravity.traffic-light.plist"
    if agent_plist.exists():
        subprocess.run(["launchctl", "unload", "-w", str(agent_plist)], capture_output=True)
        try:
            agent_plist.unlink()
        except Exception:
            pass
        print(f"✓ Removed LaunchAgent {agent_plist}")
    subprocess.run(["pkill", "-f", "agy_traffic_light"], capture_output=True)
    subprocess.run(["pkill", "-f", "agy-traffic"], capture_output=True)
    print("✓ Background processes terminated.")


def stop_windows_services():
    print("[2/4] Stopping Windows background processes and removing startup runners...")
    startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    for vbs in ["agy-traffic-daemon.vbs", "agy-traffic-tray.vbs"]:
        p = startup / vbs
        if p.exists():
            try:
                p.unlink()
                print(f"✓ Removed {p}")
            except Exception:
                pass

    try:
        subprocess.run(
            ["powershell", "-Command", "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'agy_traffic_light' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
            capture_output=True
        )
    except Exception:
        pass
    print("✓ Stopped Windows background processes.")


def clean_dms_integration():
    dms_dir = Path.home() / ".config" / "DankMaterialShell"
    if not dms_dir.exists():
        return

    plugin_dir = dms_dir / "plugins" / "agyTraffic"
    if plugin_dir.exists():
        try:
            shutil.rmtree(plugin_dir)
            print("✓ Removed DMS plugin folder.")
        except Exception as e:
            print(f"! Warning removing DMS plugin folder: {e}")

    settings_file = dms_dir / "plugin_settings.json"
    if settings_file.exists():
        try:
            import json
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "agyTraffic" in data:
                del data["agyTraffic"]
                with open(settings_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print("✓ Cleaned DMS plugin_settings.json.")
        except Exception:
            pass

    bar_settings_file = dms_dir / "settings.json"
    if bar_settings_file.exists():
        try:
            import json
            with open(bar_settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            modified = False
            for bar in data.get("barConfigs", []):
                for sec in ("rightWidgets", "centerWidgets", "leftWidgets"):
                    widgets = bar.get(sec, [])
                    if "agyTraffic" in widgets:
                        bar[sec] = [w for w in widgets if w != "agyTraffic"]
                        modified = True
            if modified:
                with open(bar_settings_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print("✓ Removed agyTraffic from DankBar settings.json.")
        except Exception:
            pass

    subprocess.run(["systemctl", "--user", "restart", "dms.service"], capture_output=True)


def clean_waybar_integration():
    waybar_dir = Path.home() / ".config" / "waybar"
    if not waybar_dir.exists():
        return

    config_file = None
    for cand in ["config.jsonc", "config"]:
        p = waybar_dir / cand
        if p.exists():
            config_file = p
            break

    if config_file:
        try:
            import json, re
            with open(config_file, "r", encoding="utf-8") as f:
                raw = f.read()
            clean_json_str = re.sub(r"//.*", "", raw)
            clean_json_str = re.sub(r"/\*.*?\*/", "", clean_json_str, flags=re.DOTALL)
            if clean_json_str.strip():
                data = json.loads(clean_json_str)
                modified = False

                def clean_bar(bar):
                    nonlocal modified
                    if "custom/agy-traffic" in bar:
                        del bar["custom/agy-traffic"]
                        modified = True
                    for sec in ("modules-right", "modules-center", "modules-left"):
                        arr = bar.get(sec, [])
                        if "custom/agy-traffic" in arr:
                            bar[sec] = [m for m in arr if m != "custom/agy-traffic"]
                            modified = True

                if isinstance(data, list):
                    for b in data:
                        if isinstance(b, dict):
                            clean_bar(b)
                elif isinstance(data, dict):
                    clean_bar(data)

                if modified:
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"✓ Removed custom/agy-traffic from {config_file.name}.")
        except Exception:
            pass

    style_file = waybar_dir / "style.css"
    if style_file.exists():
        try:
            import re
            with open(style_file, "r", encoding="utf-8") as f:
                css = f.read()
            new_css = re.sub(r"#custom-agy-traffic[^{]*\{[^}]*\}", "", css)
            new_css = re.sub(r"@keyframes agy-[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}", "", new_css)
            new_css = re.sub(r"/\* Antigravity Traffic Light \*/", "", new_css)
            if new_css != css:
                with open(style_file, "w", encoding="utf-8") as f:
                    f.write(new_css)
                print("✓ Removed traffic light styles from style.css.")
        except Exception:
            pass

    subprocess.run(["pkill", "-SIGUSR2", "waybar"], capture_output=True)


def clean_desktop_integrations():
    print("[3/4] Cleaning desktop environment integrations...")
    if sys.platform.startswith("linux"):
        clean_dms_integration()
        clean_waybar_integration()
    print("✓ Desktop integrations cleanup complete.")


def uninstall_pip_package():
    print("[4/4] Uninstalling Python package (agy-traffic-light)...")
    res = subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "agy-traffic-light", "--break-system-packages"], capture_output=True)
    if res.returncode != 0:
        res = subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "agy-traffic-light"], capture_output=True)
    if res.returncode == 0:
        print("✓ Python package uninstalled.")
    else:
        print("• Python package uninstall completed.")


def main():
    parser = argparse.ArgumentParser(description="Antigravity Traffic Light Uninstaller")
    parser.add_argument("--plugin-only", action="store_true", help="Only unlink the Antigravity hook plugin")
    parser.add_argument("--keep-package", action="store_true", help="Remove plugin and services, but keep Python package")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip interactive confirmation")
    args = parser.parse_args()

    print("==========================================")
    print("Uninstalling Antigravity Traffic Light")
    print("==========================================")

    if not args.yes and sys.stdin.isatty():
        target_desc = "the Antigravity hook plugin" if args.plugin_only else "Antigravity Traffic Light (plugin, services, and integrations)"
        response = input(f"Are you sure you want to remove {target_desc}? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print("Uninstallation cancelled.")
            sys.exit(0)

    plugin_dir = get_plugin_dir()
    remove_plugin_link(plugin_dir)

    if args.plugin_only:
        print("\n==========================================")
        print("Plugin Removal Complete!")
        print("==========================================")
        return

    system = platform.system()
    if system == "Linux":
        stop_linux_services()
        clean_desktop_integrations()
    elif system == "Darwin":
        stop_macos_services()
    elif system == "Windows":
        stop_windows_services()

    if not args.keep_package:
        uninstall_pip_package()
    else:
        print("[4/4] Keeping Python package as requested (--keep-package).")

    print("\n==========================================")
    print("Uninstallation Successful!")
    print("==========================================")


if __name__ == "__main__":
    main()
