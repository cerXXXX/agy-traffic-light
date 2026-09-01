#!/usr/bin/env python3
"""
Antigravity Traffic Light - System Tray Applet
Displays a StatusNotifierItem / AppIndicator tray icon on KDE, GNOME, DMS, XFCE, Windows, macOS.
"""

import sys
import time
import json
import urllib.request
import threading

def run_pystray_app(host="127.0.0.1", port=9876):
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        print("Tray applet requires 'pystray' and 'Pillow'. Install them with: pip install pystray pillow")
        return

    COLOR_MAP = {
        "ask": (243, 139, 168),     # Red
        "running": (249, 226, 175), # Yellow
        "idle": (166, 227, 161),    # Green
        "offline": (108, 112, 134), # Grey
    }

    def create_circle_image(color_rgb, size=64):
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((4, 4, size - 4, size - 4), fill=color_rgb)
        return image

    current_state = "offline"
    icon = pystray.Icon("agy-traffic-light", create_circle_image(COLOR_MAP["offline"]), "Antigravity Agent")

    def update_loop():
        nonlocal current_state
        while True:
            try:
                url = f"http://{host}:{port}/status"
                req = urllib.request.urlopen(url, timeout=2.0)
                data = json.loads(req.read().decode("utf-8"))
                state = data.get("state", "offline")
                tooltip = data.get("tooltip", "Antigravity Traffic Light")
                
                if state != current_state:
                    current_state = state
                    color = COLOR_MAP.get(state, COLOR_MAP["offline"])
                    icon.icon = create_circle_image(color)
                icon.title = tooltip
            except Exception:
                if current_state != "offline":
                    current_state = "offline"
                    icon.icon = create_circle_image(COLOR_MAP["offline"])
                    icon.title = "Antigravity: Daemon Offline"
            time.sleep(1.0)

    t = threading.Thread(target=update_loop, daemon=True)
    t.start()
    icon.run()


if __name__ == "__main__":
    run_pystray_app()
