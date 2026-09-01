#!/usr/bin/env python3
"""
Antigravity Traffic Light - Hook Emitter
Executed by Antigravity lifecycle hooks. Reads context from stdin,
dispatches event payload to the Traffic Light Daemon, and outputs valid response JSON to stdout.
"""

import sys
import os
import json
import socket
import urllib.request
import urllib.error

DEFAULT_SERVER_URL = "http://127.0.0.1:9876"


def send_event_to_daemon(payload: dict, server_url: str):
    """Send payload to the daemon with a very short timeout so the agent is never blocked."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{server_url}/event",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=0.15) as resp:
            pass
    except Exception:
        # Silently ignore connection failures if daemon isn't running
        pass


def main():
    event_type = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    server_url = os.environ.get("AGY_TRAFFIC_SERVER", DEFAULT_SERVER_URL).rstrip("/")

    # Read stdin JSON payload from Antigravity
    payload = {}
    try:
        if not sys.stdin.isatty():
            raw_input = sys.stdin.read()
            if raw_input.strip():
                payload = json.loads(raw_input)
    except Exception:
        payload = {}

    payload["event"] = event_type
    if "host" not in payload:
        payload["host"] = socket.gethostname()

    # Dispatch to local/remote status daemon
    send_event_to_daemon(payload, server_url)

    # Standard response according to Antigravity hook contracts
    if event_type == "PreToolUse":
        # Allow default tool execution without override
        output = {"decision": "allow"}
    else:
        output = {}

    # Print response to stdout for Antigravity
    sys.stdout.write(json.dumps(output) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
