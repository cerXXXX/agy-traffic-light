#!/bin/bash
# Script to install Antigravity Traffic Light hook on a remote SSH server.
# Run this on your remote server where you run Antigravity.

set -e

PLUGIN_DIR="$HOME/.gemini/config/plugins/agy-traffic-light"
mkdir -p "$PLUGIN_DIR/scripts"

cat << 'INNER_EOF' > "$PLUGIN_DIR/plugin.json"
{
  "name": "agy-traffic-light",
  "description": "Antigravity Traffic Light remote hook"
}
INNER_EOF

cat << 'INNER_EOF' > "$PLUGIN_DIR/scripts/notify.py"
#!/usr/bin/env python3
import sys, os, json, socket, urllib.request

DEFAULT_SERVER = os.environ.get("AGY_TRAFFIC_SERVER", "http://127.0.0.1:9876")

def main():
    event = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    payload = {}
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
            if raw.strip():
                payload = json.loads(raw)
    except Exception:
        pass
    payload["event"] = event
    payload["host"] = socket.gethostname()
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{DEFAULT_SERVER}/event", data=data, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=0.2)
    except Exception:
        pass
    if event == "PreToolUse":
        print(json.dumps({"decision": "allow"}))
    else:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
INNER_EOF
chmod +x "$PLUGIN_DIR/scripts/notify.py"

cat << 'INNER_EOF' > "$PLUGIN_DIR/hooks.json"
{
  "traffic-light-hooks": {
    "PreInvocation": [{ "type": "command", "command": "python3 scripts/notify.py PreInvocation" }],
    "PreToolUse": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "python3 scripts/notify.py PreToolUse" }] }],
    "PostToolUse": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "python3 scripts/notify.py PostToolUse" }] }],
    "PostInvocation": [{ "type": "command", "command": "python3 scripts/notify.py PostInvocation" }],
    "Stop": [{ "type": "command", "command": "python3 scripts/notify.py Stop" }]
  }
}
INNER_EOF

echo "✓ Remote hook installed to $PLUGIN_DIR"
echo ""
echo "To connect to your local desktop traffic light daemon, connect via SSH with reverse tunnel:"
echo "  ssh -R 9876:localhost:9876 user@$(hostname)"
