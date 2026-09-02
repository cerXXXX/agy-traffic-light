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


COLORS = {
    "ask": "#ff1744",      # 🔴 Red
    "running": "#ffdd00",  # 🟡 Yellow
    "idle": "#00ff88",     # 🟢 Green
    "offline": "#6c7086",  # ⚪ Grey
}

STATE_LABELS = {
    "ask": "🔴 Attention Required",
    "running": "🟡 Agent Working",
    "idle": "🟢 Ready for Input",
    "offline": "⚪ Offline",
}


def create_circle_icon(color_hex: str, size: int = 64):
    """Draw a clean glowing traffic light icon using Pillow."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer glow ring
    draw.ellipse([4, 4, size - 4, size - 4], outline=color_hex, width=3)
    # Inner solid dot
    draw.ellipse([16, 16, size - 16, size - 16], fill=color_hex)
    return img


def run_pystray_app(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """
    Run native cross-platform system tray applet using pystray.
    Works natively on Windows, macOS (Menu Bar), and Linux desktops.
    """
    # Parse CLI arguments if invoked directly as script entry point
    if len(sys.argv) > 1 and ("--host" in sys.argv or "--port" in sys.argv):
        parser = argparse.ArgumentParser(description="Antigravity Traffic Light System Tray Applet")
        parser.add_argument("--host", default=DEFAULT_HOST)
        parser.add_argument("--port", type=int, default=DEFAULT_PORT)
        parsed, _ = parser.parse_known_args()
        host = parsed.host
        port = parsed.port

    import pystray

    # Pre-generate icon images
    cached_icons = {state: create_circle_icon(color) for state, color in COLORS.items()}

    current_state = ["offline"]
    current_sessions = []
    stop_event = threading.Event()

    def on_clear(icon, item):
        try:
            req = urllib.request.Request(f"http://{host}:{port}/clear", method="POST")
            urllib.request.urlopen(req, timeout=1.0)
        except Exception:
            pass

    def on_quit(icon, item):
        stop_event.set()
        icon.stop()

    def build_menu():
        state = current_state[0]
        header_text = STATE_LABELS.get(state, state.title())
        items = [
            pystray.MenuItem(f"Antigravity: {header_text}", None, enabled=False),
            pystray.Menu.SEPARATOR,
        ]

        if current_sessions:
            items.append(pystray.MenuItem(f"Active Sessions ({len(current_sessions)}):", None, enabled=False))
            for s in current_sessions:
                workspace = s.get("workspace", "workspace")
                sess_host = s.get("host", "localhost")
                host_suffix = f"@{sess_host}" if sess_host not in ("localhost", "127.0.0.1") else ""
                substatus = s.get("substatus", "")
                sess_state = s.get("state", "idle")
                emoji = "🔴" if sess_state == "ask" else ("🟡" if sess_state == "running" else "🟢")
                items.append(pystray.MenuItem(f"{emoji} [{workspace}{host_suffix}]: {substatus}", None, enabled=False))
        else:
            items.append(pystray.MenuItem("No active sessions running", None, enabled=False))

        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Clear Sessions", on_clear))
        items.append(pystray.MenuItem("Quit", on_quit))
        return pystray.Menu(*items)

    icon = pystray.Icon(
        "agy-traffic-light",
        cached_icons["offline"],
        title="Antigravity: Initializing...",
        menu=build_menu()
    )

    def poll_status():
        while not stop_event.is_set():
            try:
                url = f"http://{host}:{port}/status"
                req = urllib.request.urlopen(url, timeout=1.0)
                data = json.loads(req.read().decode("utf-8"))
                new_state = data.get("state", "offline")
                new_sessions = data.get("sessions", [])

                state_changed = (new_state != current_state[0])
                sessions_changed = (len(new_sessions) != len(current_sessions) or
                                   [s.get("substatus") for s in new_sessions] != [s.get("substatus") for s in current_sessions])

                if state_changed or sessions_changed:
                    current_state[0] = new_state
                    current_sessions.clear()
                    current_sessions.extend(new_sessions)

                    icon.icon = cached_icons.get(new_state, cached_icons["offline"])
                    icon.title = f"Antigravity: {STATE_LABELS.get(new_state, new_state)}"
                    icon.menu = build_menu()
                    if hasattr(icon, "update_menu"):
                        icon.update_menu()
            except Exception:
                if current_state[0] != "offline":
                    current_state[0] = "offline"
                    current_sessions.clear()
                    icon.icon = cached_icons["offline"]
                    icon.title = "Antigravity: Daemon Offline"
                    icon.menu = build_menu()
                    if hasattr(icon, "update_menu"):
                        icon.update_menu()

            stop_event.wait(0.5)

    poller = threading.Thread(target=poll_status, daemon=True)
    poller.start()

    icon.run()


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

            header_item.set_label(f"Antigravity Agent: {STATE_LABELS.get(state, state)}")

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
    parser.add_argument(
        "--backend",
        choices=["auto", "pystray", "ayatana"],
        default="auto",
        help="Tray backend (default: auto)"
    )
    args = parser.parse_args()

    if args.backend == "ayatana":
        run_ayatana_tray(host=args.host, port=args.port)
    elif args.backend == "pystray":
        run_pystray_app(host=args.host, port=args.port)
    else:  # auto
        try:
            import pystray
            run_pystray_app(host=args.host, port=args.port)
        except Exception as e:
            if sys.platform.startswith("linux"):
                try:
                    run_ayatana_tray(host=args.host, port=args.port)
                except Exception as inner_e:
                    print(f"Failed to start system tray (pystray: {e}, ayatana: {inner_e})")
            else:
                print(f"Failed to start system tray applet: {e}")


if __name__ == "__main__":
    main()

