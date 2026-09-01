#!/usr/bin/env python3
"""
Antigravity Traffic Light - System Tray Applet
Native StatusNotifierItem / AppIndicator for DMS, KDE, GNOME, Waybar, XFCE.
"""

import sys
import os
import time
import json
import urllib.request
import threading

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))

ICON_PATHS = {
    "ask": os.path.join(ASSETS_DIR, "dot-red.svg"),
    "running": os.path.join(ASSETS_DIR, "dot-yellow.svg"),
    "idle": os.path.join(ASSETS_DIR, "dot-green.svg"),
    "offline": os.path.join(ASSETS_DIR, "dot-grey.svg"),
}

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876


def run_ayatana_tray(host=DEFAULT_HOST, port=DEFAULT_PORT):
    import gi
    gi.require_version('Gtk', '3.0')
    try:
        gi.require_version('AyatanaAppIndicator3', '0.1')
        from gi.repository import AyatanaAppIndicator3 as AppIndicator
    except (ValueError, ImportError):
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3 as AppIndicator

    from gi.repository import Gtk, GLib

    indicator = AppIndicator.Indicator.new(
        "agy-traffic-light",
        ICON_PATHS["offline"],
        AppIndicator.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()

    # Header Item
    header_item = Gtk.MenuItem(label="Antigravity: Initializing...")
    header_item.set_sensitive(False)
    menu.append(header_item)

    menu.append(Gtk.SeparatorMenuItem())

    # Sessions container submenu / item
    sessions_item = Gtk.MenuItem(label="No active sessions")
    sessions_item.set_sensitive(False)
    menu.append(sessions_item)

    menu.append(Gtk.SeparatorMenuItem())

    # Clear sessions
    def on_clear(widget):
        try:
            req = urllib.request.Request(f"http://{host}:{port}/clear", method="POST")
            urllib.request.urlopen(req, timeout=1.0)
        except Exception:
            pass

    clear_item = Gtk.MenuItem(label="Clear Sessions")
    clear_item.connect("activate", on_clear)
    menu.append(clear_item)

    # Quit
    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect("activate", lambda w: Gtk.main_quit())
    menu.append(quit_item)

    menu.show_all()
    indicator.set_menu(menu)

    current_state = ["offline"]

    def update_status():
        try:
            url = f"http://{host}:{port}/status"
            req = urllib.request.urlopen(url, timeout=1.0)
            data = json.loads(req.read().decode("utf-8"))
            state = data.get("state", "offline")
            sessions = data.get("sessions", [])

            if state != current_state[0]:
                current_state[0] = state
                icon_path = ICON_PATHS.get(state, ICON_PATHS["offline"])
                indicator.set_icon_full(icon_path, state)

            # Update header label
            state_labels = {
                "ask": "🔴 Attention Required",
                "running": "🟡 Agent Working",
                "idle": "🟢 Agent Done / Idle",
                "offline": "⚪ Offline"
            }
            header_item.set_label(f"Antigravity: {state_labels.get(state, state)}")

            if sessions:
                lines = []
                for s in sessions:
                    lines.append(f"[{s.get('workspace')}]: {s.get('substatus')}")
                sessions_item.set_label("\n".join(lines[:3]))
            else:
                sessions_item.set_label("No active sessions")

        except Exception:
            if current_state[0] != "offline":
                current_state[0] = "offline"
                indicator.set_icon_full(ICON_PATHS["offline"], "offline")
                header_item.set_label("Antigravity: Daemon Offline")
                sessions_item.set_label("Cannot reach daemon")

        return True  # Keep GLib timer running

    GLib.timeout_add(500, update_status)
    Gtk.main()


def main():
    try:
        run_ayatana_tray()
    except Exception as e:
        print(f"Failed to start tray applet: {e}")


if __name__ == "__main__":
    main()
