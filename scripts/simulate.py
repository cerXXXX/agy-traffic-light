#!/usr/bin/env python3
"""
Simulate Antigravity agent states to test the Traffic Light indicator.
"""

import time
import json
import urllib.request
import argparse

SERVER_URL = "http://127.0.0.1:9876"

def send_event(payload):
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{SERVER_URL}/event", data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"-> Sent {payload.get('event')}: new state = {res.get('new_state')}")
    except Exception as e:
        print(f"Error connecting to daemon: {e}")

def run_simulation(session_name="my-project", is_remote=False):
    conv_id = f"sim-{session_name}"
    host = "remote-vps" if is_remote else "localhost"

    print(f"\n--- Starting simulation for session [{session_name}] ---")
    
    print("\n1. 🟡 Agent starts thinking (PreInvocation)...")
    send_event({
        "conversationId": conv_id,
        "workspacePaths": [f"/home/user/projects/{session_name}"],
        "event": "PreInvocation",
        "host": host
    })
    time.sleep(2)

    print("\n2. 🟡 Agent runs command: 'npm run test' (PreToolUse)...")
    send_event({
        "conversationId": conv_id,
        "workspacePaths": [f"/home/user/projects/{session_name}"],
        "event": "PreToolUse",
        "toolCall": {"name": "run_command", "args": {"CommandLine": "npm run test"}},
        "host": host
    })
    time.sleep(2)

    print("\n3. 🔴 Agent requests confirmation for: 'rm -rf build' (Approval required)...")
    send_event({
        "conversationId": conv_id,
        "workspacePaths": [f"/home/user/projects/{session_name}"],
        "event": "PreToolUse",
        "toolCall": {"name": "run_command", "args": {"CommandLine": "rm -rf build"}},
        "waitingApproval": True,
        "host": host
    })
    time.sleep(3)

    print("\n4. 🟡 User approved, tool finished (PostToolUse)...")
    send_event({
        "conversationId": conv_id,
        "workspacePaths": [f"/home/user/projects/{session_name}"],
        "event": "PostToolUse",
        "host": host
    })
    time.sleep(1.5)

    print("\n5. 🟢 Agent finished task and is now Idle (Stop)...")
    send_event({
        "conversationId": conv_id,
        "workspacePaths": [f"/home/user/projects/{session_name}"],
        "event": "Stop",
        "host": host
    })
    print("\nSimulation complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate agent states")
    parser.add_argument("--name", default="my-project", help="Session name")
    parser.add_argument("--remote", action="store_true", help="Simulate as remote server")
    args = parser.parse_args()
    run_simulation(args.name, args.remote)
