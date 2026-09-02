#!/usr/bin/env python3
"""
Antigravity Traffic Light - Standalone Wayland Overlay Widget
Renders an eye-catching, vibrant traffic light circle directly on any panel or desktop bar.
Clicking the circle opens an interactive details popout window that automatically adapts
its opening direction based on panel position (top/bottom/left/right).
"""

import sys
import os
import time
import json
import argparse
import urllib.request
import threading

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib, Pango

CSS_TEXT = """
window {
    background-color: transparent;
}

.traffic-pill {
    background-color: rgba(15, 15, 24, 0.90);
    border: 1.5px solid rgba(255, 255, 255, 0.20);
    border-radius: 9999px;
    padding: 1px 7px;
    margin: 0px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
}

.traffic-pill:hover {
    background-color: rgba(24, 24, 37, 0.98);
    border-color: rgba(255, 255, 255, 0.45);
}

.dot-label {
    font-size: 24px;
    font-weight: 900;
    padding: 0px 1px;
}

.text-label {
    font-size: 13px;
    font-weight: bold;
    font-family: sans-serif;
    color: #ffffff;
    padding-left: 6px;
    padding-right: 4px;
}

/* Green - Idle / Ready */
.state-idle .dot-label {
    color: #00ff88;
    text-shadow: 0 0 14px rgba(0, 255, 136, 0.95);
}
.state-idle {
    border-color: rgba(0, 255, 136, 0.5);
}

/* Yellow - Running / Thinking */
.state-running .dot-label {
    color: #ffdd00;
    text-shadow: 0 0 16px rgba(255, 221, 0, 0.95);
}
.state-running {
    border-color: rgba(255, 221, 0, 0.6);
}

/* Red - Needs Approval / Attention */
.state-ask .dot-label {
    color: #ff1744;
    text-shadow: 0 0 18px rgba(255, 23, 68, 1.0);
}
.state-ask {
    border-color: rgba(255, 23, 68, 0.9);
    background-color: rgba(255, 23, 68, 0.35);
}

/* Grey - Offline */
.state-offline .dot-label {
    color: #6c7086;
}
.state-offline {
    border-color: rgba(255, 255, 255, 0.15);
}

/* Popout Details Window */
.popout-window {
    background-color: rgba(17, 17, 27, 0.96);
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    border-radius: 14px;
    padding: 10px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
}

.popout-header {
    font-size: 14px;
    font-weight: bold;
    color: #cdd6f4;
}

.close-btn {
    background: transparent;
    border: none;
    border-radius: 10px;
    color: #a6adc8;
    font-size: 13px;
    padding: 2px 6px;
    margin: 0;
}

.close-btn:hover {
    background-color: rgba(243, 139, 168, 0.25);
    color: #f38ba8;
}

.popout-card {
    background-color: rgba(30, 30, 46, 0.90);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px;
}

.session-header {
    font-size: 12px;
    font-weight: 600;
    color: #a6adc8;
}

.session-item {
    font-size: 12px;
    color: #cdd6f4;
}

.clear-btn {
    font-size: 11px;
    font-weight: 600;
    background-color: rgba(49, 50, 68, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 6px;
    color: #bac2de;
    padding: 4px 10px;
}

.clear-btn:hover {
    background-color: rgba(69, 71, 90, 0.95);
    color: #ffffff;
}
"""

STATE_EMOJIS = {
    "ask": "●",
    "running": "●",
    "idle": "●",
    "offline": "●",
}


def apply_layer_shell_position(window, position, margin_bar, margin_side, is_popout=False, popout_offset=38):
    """
    Configure GtkLayerShell anchors and margins.
    Ensures the popout opens in the natural direction based on panel position:
    - Top panel: popout opens DOWNWARDS.
    - Bottom panel: popout opens UPWARDS.
    - Left panel: popout opens to the RIGHT.
    - Right panel: popout opens to the LEFT.
    """
    GtkLayerShell.init_for_window(window)
    GtkLayerShell.set_layer(window, GtkLayerShell.Layer.OVERLAY)
    GtkLayerShell.set_namespace(window, "agy-traffic-popout" if is_popout else "agy-traffic-light")
    GtkLayerShell.set_exclusive_zone(window, -1)

    # Clear all anchors
    for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM, GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
        GtkLayerShell.set_anchor(window, edge, False)

    pos_parts = position.lower().split("-")
    primary = pos_parts[0]
    secondary = pos_parts[1] if len(pos_parts) > 1 else ("right" if primary in ("top", "bottom") else "top")

    if primary == "top":
        eff_top = margin_bar + popout_offset if is_popout else margin_bar
        GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, eff_top)
        if secondary == "left":
            GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_margin(window, GtkLayerShell.Edge.LEFT, margin_side)
        elif secondary == "center":
            pass
        else:  # right
            GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_margin(window, GtkLayerShell.Edge.RIGHT, margin_side)

    elif primary == "bottom":
        eff_bottom = margin_bar + popout_offset if is_popout else margin_bar
        GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, eff_bottom)
        if secondary == "left":
            GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_margin(window, GtkLayerShell.Edge.LEFT, margin_side)
        elif secondary == "center":
            pass
        else:  # right
            GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_margin(window, GtkLayerShell.Edge.RIGHT, margin_side)

    elif primary == "left":
        eff_left = margin_bar + popout_offset if is_popout else margin_bar
        GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_margin(window, GtkLayerShell.Edge.LEFT, eff_left)
        if secondary == "top":
            GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, margin_side)
        elif secondary == "bottom":
            GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.BOTTOM, True)
            GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, margin_side)

    elif primary == "right":
        eff_right = margin_bar + popout_offset if is_popout else margin_bar
        GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(window, GtkLayerShell.Edge.RIGHT, eff_right)
        if secondary == "top":
            GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, margin_side)
        elif secondary == "bottom":
            GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.BOTTOM, True)
            GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, margin_side)


class DetailsPopout(Gtk.Window):
    def __init__(self, host="127.0.0.1", port=9876, position="top-right", margin_bar=4, margin_side=280, width=260):
        super().__init__()
        self.host = host
        self.port = port
        self.popout_width = width

        self.set_default_size(self.popout_width, -1)
        self.set_size_request(self.popout_width, -1)
        self.set_resizable(False)

        apply_layer_shell_position(self, position, margin_bar, margin_side, is_popout=True)
        GtkLayerShell.set_keyboard_interactivity(self, True)

        self.connect("key-press-event", self.on_key_press)

        # Main Popout Box Container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.main_box.get_style_context().add_class("popout-window")
        self.add(self.main_box)

        # Header Row: Title + Close Button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.main_box.pack_start(header_box, False, False, 0)

        title_lbl = Gtk.Label(label="Antigravity Agent")
        title_lbl.get_style_context().add_class("popout-header")
        title_lbl.set_xalign(0.0)
        header_box.pack_start(title_lbl, True, True, 2)

        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("close-btn")
        close_btn.connect("clicked", lambda w: self.hide())
        header_box.pack_end(close_btn, False, False, 0)

        # Sessions Card
        self.card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.card_box.get_style_context().add_class("popout-card")
        self.main_box.pack_start(self.card_box, True, True, 0)

        self.session_title = Gtk.Label(label="No active sessions running")
        self.session_title.get_style_context().add_class("session-header")
        self.session_title.set_xalign(0.0)
        self.card_box.pack_start(self.session_title, False, False, 0)

        self.sessions_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.card_box.pack_start(self.sessions_container, True, True, 0)

        # Action Footer: Clear Sessions
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.main_box.pack_start(footer_box, False, False, 0)

        clear_btn = Gtk.Button(label="Clear Sessions")
        clear_btn.get_style_context().add_class("clear-btn")
        clear_btn.connect("clicked", self.on_clear_clicked)
        footer_box.pack_end(clear_btn, False, False, 0)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def on_clear_clicked(self, widget):
        try:
            req = urllib.request.Request(f"http://{self.host}:{self.port}/clear", method="POST")
            urllib.request.urlopen(req, timeout=1.0)
        except Exception:
            pass
        self.update_content({"sessions": []})

    def toggle(self):
        if self.get_visible():
            self.hide()
        else:
            self.show_all()

    def update_content(self, data):
        sessions = data.get("sessions", [])
        
        # Clear existing session labels
        for child in self.sessions_container.get_children():
            self.sessions_container.remove(child)

        if sessions:
            self.session_title.set_text(f"Active Sessions ({len(sessions)}):")
            for s in sessions:
                workspace = s.get("workspace", "workspace")
                host = s.get("host", "localhost")
                host_suffix = f"@{host}" if host not in ("localhost", "127.0.0.1") else ""
                substatus = s.get("substatus", "")
                
                lbl = Gtk.Label(label=f"• [{workspace}{host_suffix}]: {substatus}")
                lbl.get_style_context().add_class("session-item")
                lbl.set_line_wrap(True)
                lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                lbl.set_xalign(0.0)
                self.sessions_container.pack_start(lbl, False, False, 0)
        else:
            self.session_title.set_text("No active sessions running")

        self.sessions_container.show_all()


class TrafficLightWidget(Gtk.Window):
    def __init__(self, host="127.0.0.1", port=9876, position="top-right", margin_bar=4, margin_side=280, show_text=False, popout_width=260):
        super().__init__()
        self.host = host
        self.port = port
        self.show_text = show_text
        self.current_state = "offline"

        # Apply Layer Shell position for pill
        apply_layer_shell_position(self, position, margin_bar, margin_side, is_popout=False)
        GtkLayerShell.set_keyboard_interactivity(self, False)

        # Load Global CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS_TEXT.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Create details popout
        self.popout = DetailsPopout(
            host=self.host,
            port=self.port,
            position=position,
            margin_bar=margin_bar,
            margin_side=margin_side,
            width=popout_width
        )

        # EventBox container for clicks and tooltips
        self.event_box = Gtk.EventBox()
        self.event_box.set_visible_window(False)
        self.event_box.connect("button-press-event", self.on_click)
        self.add(self.event_box)

        # Main horizontal box
        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.box.get_style_context().add_class("traffic-pill")
        self.box.get_style_context().add_class("state-offline")
        self.event_box.add(self.box)

        # Dot Icon Label
        self.dot_label = Gtk.Label(label=STATE_EMOJIS["offline"])
        self.dot_label.get_style_context().add_class("dot-label")
        self.box.pack_start(self.dot_label, False, False, 0)

        # Optional Text Label
        self.text_label = Gtk.Label(label="")
        self.text_label.get_style_context().add_class("text-label")
        if self.show_text:
            self.box.pack_start(self.text_label, False, False, 0)

        self.set_tooltip_text("Antigravity: Initializing...")

        # Setup periodic update
        GLib.timeout_add(350, self.update_state)

    def on_click(self, widget, event):
        if event.button == 1:  # Left click -> Toggle details popout
            self.popout.toggle()
        elif event.button == 3:  # Right click -> Clear sessions
            try:
                req = urllib.request.Request(f"http://{self.host}:{self.port}/clear", method="POST")
                urllib.request.urlopen(req, timeout=1.0)
            except Exception:
                pass

    def update_state(self):
        try:
            url = f"http://{self.host}:{self.port}/status"
            req = urllib.request.urlopen(url, timeout=0.8)
            data = json.loads(req.read().decode("utf-8"))
            state = data.get("state", "offline")
            tooltip = data.get("tooltip", "Antigravity Traffic Light")

            if state != self.current_state:
                ctx = self.box.get_style_context()
                ctx.remove_class(f"state-{self.current_state}")
                ctx.add_class(f"state-{state}")
                self.current_state = state
                self.dot_label.set_text(STATE_EMOJIS.get(state, "●"))

            self.set_tooltip_text(tooltip)

            if self.show_text:
                if state == "running":
                    self.text_label.set_text("Working")
                elif state == "ask":
                    self.text_label.set_text("Confirm")
                elif state == "idle":
                    self.text_label.set_text("Idle")
                else:
                    self.text_label.set_text("")

            if self.popout.get_visible():
                self.popout.update_content(data)

        except Exception:
            if self.current_state != "offline":
                ctx = self.box.get_style_context()
                ctx.remove_class(f"state-{self.current_state}")
                ctx.add_class("state-offline")
                self.current_state = "offline"
                self.dot_label.set_text(STATE_EMOJIS["offline"])
                self.set_tooltip_text("Antigravity: Daemon Offline")
                if self.popout.get_visible():
                    self.popout.update_content({"sessions": []})

        return True


def main():
    parser = argparse.ArgumentParser(description="Standalone Antigravity Traffic Light Wayland Widget")
    parser.add_argument("--host", default="127.0.0.1", help="Daemon host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9876, help="Daemon port (default: 9876)")
    parser.add_argument(
        "--position",
        choices=[
            "top-right", "top-left", "top-center",
            "bottom-right", "bottom-left", "bottom-center",
            "left-top", "left-center", "left-bottom",
            "right-top", "right-center", "right-bottom",
        ],
        default="top-right",
        help="Position on screen / panel edge (default: top-right)"
    )
    parser.add_argument("--margin-bar", "--margin-top", dest="margin_bar", type=int, default=4, help="Margin from panel edge in pixels (default: 4)")
    parser.add_argument("--margin-side", type=int, default=280, help="Margin from side edge in pixels (default: 280)")
    parser.add_argument("--popout-width", type=int, default=260, help="Width of details popout window (default: 260)")
    parser.add_argument("--show-text", action="store_true", help="Show text label next to the circle")
    args = parser.parse_args()

    win = TrafficLightWidget(
        host=args.host,
        port=args.port,
        position=args.position,
        margin_bar=args.margin_bar,
        margin_side=args.margin_side,
        show_text=args.show_text,
        popout_width=args.popout_width
    )
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()

