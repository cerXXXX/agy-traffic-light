#!/usr/bin/env python3
"""
Antigravity Traffic Light - Standalone Wayland Overlay Widget
Renders a separate, dedicated traffic light circle on the top bar / screen edge
using Wayland Layer-Shell (GTK3 + GtkLayerShell).
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
    background-color: rgba(24, 24, 37, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 9999px;
    padding: 2px 8px;
    margin: 0px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
    transition: all 250ms ease;
}

.traffic-pill:hover {
    background-color: rgba(30, 30, 46, 0.98);
    border-color: rgba(255, 255, 255, 0.35);
}

.dot-label {
    font-size: 16px;
    font-weight: bold;
    padding: 0px 2px;
}

.text-label {
    font-size: 12px;
    font-family: sans-serif;
    color: #cdd6f4;
    padding-left: 4px;
    padding-right: 2px;
}

/* Green - Idle */
.state-idle .dot-label {
    color: #a6e3a1;
}

/* Yellow - Running */
.state-running .dot-label {
    color: #f9e2af;
}

/* Red - Needs Approval */
.state-ask .dot-label {
    color: #f38ba8;
}

.state-ask {
    border-color: rgba(243, 139, 168, 0.8);
    background-color: rgba(243, 139, 168, 0.25);
}

/* Grey - Offline */
.state-offline .dot-label {
    color: #585b70;
}
"""

STATE_EMOJIS = {
    "ask": "●",
    "running": "●",
    "idle": "●",
    "offline": "○",
}


class TrafficLightWidget(Gtk.Window):
    def __init__(self, host="127.0.0.1", port=9876, position="top-right", margin_top=6, margin_side=300, show_text=False):
        super().__init__()
        self.host = host
        self.port = port
        self.show_text = show_text
        self.current_state = "offline"

        # Initialize Wayland Layer Shell
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self, "agy-traffic-light")
        GtkLayerShell.set_keyboard_interactivity(self, False)

        # Set Anchors based on position
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        if "left" in position:
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, margin_side)
        elif "center" in position:
            pass
        else: # right
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, margin_side)

        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, margin_top)

        # Load CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS_TEXT.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
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
        GLib.timeout_add(400, self.update_state)

    def on_click(self, widget, event):
        if event.button == 3: # Right click -> Clear sessions
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

        except Exception:
            if self.current_state != "offline":
                ctx = self.box.get_style_context()
                ctx.remove_class(f"state-{self.current_state}")
                ctx.add_class("state-offline")
                self.current_state = "offline"
                self.dot_label.set_text(STATE_EMOJIS["offline"])
                self.set_tooltip_text("Antigravity: Daemon Offline")

        return True


def main():
    parser = argparse.ArgumentParser(description="Standalone Antigravity Traffic Light Wayland Widget")
    parser.add_argument("--host", default="127.0.0.1", help="Daemon host")
    parser.add_argument("--port", type=int, default=9876, help="Daemon port")
    parser.add_argument("--position", choices=["top-right", "top-left", "top-center"], default="top-right", help="Widget position on screen")
    parser.add_argument("--margin-top", type=int, default=6, help="Top margin in pixels")
    parser.add_argument("--margin-side", type=int, default=300, help="Side margin in pixels")
    parser.add_argument("--show-text", action="store_true", help="Show text label next to the circle")
    args = parser.parse_args()

    win = TrafficLightWidget(
        host=args.host,
        port=args.port,
        position=args.position,
        margin_top=args.margin_top,
        margin_side=args.margin_side,
        show_text=args.show_text
    )
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
