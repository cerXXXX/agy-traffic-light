#!/usr/bin/env python3
"""
Antigravity Traffic Light - System Tray Applet
Native StatusNotifierItem / AppIndicator for KDE Plasma, GNOME, XFCE, Cinnamon, etc.
"""

import sys
import os
import time
import json
import argparse
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

    # 1. Header Item
    header_item = Gtk.MenuItem(label="Antigravity Agent: Initializing...")
    header_item.set_sensitive(False)
    menu.append(header_item)

    menu.append(Gtk.SeparatorMenuItem())

    # Dynamic session items holder
    dynamic_items = []

    empty_sessions_item = Gtk.MenuItem(label="No active sessions running")
    empty_sessions_item.set_sensitive(False)
    menu.append(empty_sessions_item)
    dynamic_items.append(empty_sessions_item)

    menu.append(Gtk.SeparatorMenuItem())

    # Clear sessions
    def on_clear(widget):
        try:
            req = urllib.request.Request(f"http://{host}:{port}/clear", method="POST")
            urllib.request.urlopen(req, timeout=1.0)
        except Exception:
            pass
        update_status()

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
                "idle": "🟢 Ready for Input",
                "offline": "⚪ Offline"
            }
            header_item.set_label(f"Antigravity Agent: {state_labels.get(state, state)}")

            # Remove old dynamic items
            for item in list(dynamic_items):
                menu.remove(item)
            dynamic_items.clear()

            # Re-insert dynamic session items right before clear_item separator
            # Index 2 is right after the first separator
            insert_idx = 2
            if sessions:
                count_item = Gtk.MenuItem(label=f"Active Sessions ({len(sessions)}):")
                count_item.set_sensitive(False)
                menu.insert(count_item, insert_idx)
                dynamic_items.append(count_item)
                insert_idx += 1

                for s in sessions:
                    workspace = s.get("workspace", "workspace")
                    sess_host = s.get("host", "localhost")
                    host_suffix = f"@{sess_host}" if sess_host not in ("localhost", "127.0.0.1") else ""
                    substatus = s.get("substatus", "")
                    sess_state = s.get("state", "idle")
                    emoji = "🔴" if sess_state == "ask" else ("🟡" if sess_state == "running" else "🟢")

                    sess_item = Gtk.MenuItem(label=f"{emoji} [{workspace}{host_suffix}]: {substatus}")
                    sess_item.set_sensitive(False)
                    menu.insert(sess_item, insert_idx)
                    dynamic_items.append(sess_item)
                    insert_idx += 1
            else:
                none_item = Gtk.MenuItem(label="No active sessions running")
                none_item.set_sensitive(False)
                menu.insert(none_item, insert_idx)
                dynamic_items.append(none_item)

            menu.show_all()

        except Exception:
            if current_state[0] != "offline":
                current_state[0] = "offline"
                indicator.set_icon_full(ICON_PATHS["offline"], "offline")
                header_item.set_label("Antigravity Agent: Daemon Offline")

        return True

    GLib.timeout_add(500, update_status)
    Gtk.main()


def main():
    parser = argparse.ArgumentParser(description="Antigravity Traffic Light System Tray Applet")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Daemon host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Daemon port (default: 9876)")
    args = parser.parse_args()

    try:
        run_ayatana_tray(host=args.host, port=args.port)
    except Exception as e:
        print(f"Failed to start tray applet: {e}")


if __name__ == "__main__":
    main()

