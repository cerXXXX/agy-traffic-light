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


def find_agent_pid() -> int:
    """Find the Antigravity agent process PID by inspecting process ancestors."""
    try:
        curr = os.getpid()
        agent_pid = os.getppid()
        for _ in range(8):
            stat_file = f"/proc/{curr}/stat"
            if not os.path.exists(stat_file):
                break
            with open(stat_file, "r") as f:
                content = f.read()
            rparen = content.rfind(")")
            if rparen == -1:
                break
            comm = content[content.find("(") + 1:rparen].lower()
            ppid = int(content[rparen + 2:].split()[1])
            if ppid <= 1:
                break
            if any(name in comm for name in ("agy", "antigravity", "gemini")):
                return curr
            if comm not in ("sh", "bash", "zsh", "fish", "python", "python3", "notify.py", "emitter.py"):
                agent_pid = curr
            curr = ppid
        return agent_pid
    except Exception:
        return os.getppid()


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
    if "pid" not in payload:
        payload["pid"] = find_agent_pid()

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

