#!/usr/bin/env python3
"""
Antigravity Traffic Light - Status Daemon
Aggregates lifecycle events from local and remote Antigravity agents
and provides status outputs for Waybar, DMS, desktop widgets, and system tray.
"""

import json
import sys
import time
import socket
import argparse
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional
import os

DEFAULT_PORT = 9876
DEFAULT_HOST = "127.0.0.1"
SESSION_EXPIRATION_SECONDS = 1800  # 30 minutes fallback for remote sessions


try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def is_pid_alive(pid: int) -> bool:
    """Check if process with given PID is still running and not a zombie."""
    if pid <= 0:
        return True

    if HAS_PSUTIL:
        try:
            p = psutil.Process(pid)
            return p.is_running() and p.status() != getattr(psutil, "STATUS_ZOMBIE", "zombie")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        except Exception:
            return False

    # Windows native fallback
    if sys.platform == "win32":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            SYNCHRONIZE = 0x00100000
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(handle)
            return exit_code.value == 259  # STILL_ACTIVE
        except Exception:
            return False

    # POSIX (Linux, macOS) native fallback without psutil
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False

    # Check for zombie state on Linux
    try:
        status_file = f"/proc/{pid}/status"
        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                for line in f:
                    if line.startswith("State:"):
                        if "Z (zombie)" in line:
                            return False
                        break
    except Exception:
        pass

    return True


def get_transcript_last_step(transcript_path: str) -> Optional[Dict[str, Any]]:
    """Safely and efficiently read the last JSON step from an Antigravity transcript file."""
    try:
        if not transcript_path or not os.path.exists(transcript_path):
            return None
        with open(transcript_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                return None
            read_size = min(size, 8192)
            f.seek(max(0, size - read_size))
            chunk = f.read(read_size)
        lines = [l.strip() for l in chunk.split(b"\n") if l.strip()]
        for line in reversed(lines):
            try:
                return json.loads(line.decode("utf-8", errors="ignore"))
            except Exception:
                continue
    except Exception:
        pass
    return None


ICONS = {
    "ask": "●",      # 🔴 Waiting for approval / attention
    "running": "●",  # 🟡 Thinking / Executing tool
    "idle": "●",     # 🟢 Done / Idle
    "offline": "●",  # ⚪ No active sessions
}

CSS_CLASSES = {
    "ask": "ask",
    "running": "running",
    "idle": "idle",
    "offline": "offline",
}


class AgentSession:
    def __init__(self, conversation_id: str, workspace: str = "", host: str = "localhost", pid: int = 0, transcript_path: str = ""):
        self.conversation_id = conversation_id
        self.workspace = workspace or "unknown"
        self.host = host or "localhost"
        self.pid = pid
        self.transcript_path = transcript_path or ""
        self.active_tool_step_idx = -1
        self.active_tool_name = ""
        self.fully_idle = True
        self.state = "idle"  # "ask", "running", "idle"
        self.substatus = "Initialized"
        self.last_updated = time.time()
        self.model = ""

    def update(self, state: str, substatus: str, model: str = "", pid: int = 0, transcript_path: str = ""):
        self.state = state
        self.substatus = substatus
        if model:
            self.model = model
        if pid > 0:
            self.pid = pid
        if transcript_path:
            self.transcript_path = transcript_path
        self.last_updated = time.time()

    def is_stale(self, max_age: float = SESSION_EXPIRATION_SECONDS) -> bool:
        # If running locally and PID is tracked, instantly detect process termination
        if self.pid > 0 and self.host in ("localhost", "127.0.0.1", socket.gethostname()):
            if not is_pid_alive(self.pid):
                return True
            # Expire idle finished sessions after 5 minutes so they don't linger forever
            if self.state == "idle" and (time.time() - self.last_updated) > 300:
                return True
            return False

        # Untracked / remote sessions:
        # If idle / finished, expire quickly (after 60 seconds) so old finished sessions don't pile up
        if self.state == "idle":
            return (time.time() - self.last_updated) > 60
        return (time.time() - self.last_updated) > max_age

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "workspace": self.workspace,
            "host": self.host,
            "pid": self.pid,
            "transcript_path": self.transcript_path,
            "active_tool_step_idx": self.active_tool_step_idx,
            "fully_idle": self.fully_idle,
            "state": self.state,
            "substatus": self.substatus,
            "last_updated": self.last_updated,
            "model": self.model,
            "age_seconds": round(time.time() - self.last_updated, 1),
        }


class StateManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.sessions: Dict[str, AgentSession] = {}
        self.subscribers = []
        self._watchdog = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog.start()

    def _watchdog_loop(self):
        while True:
            time.sleep(0.5)
            changed = False
            with self.lock:
                interrupted_changed = self._check_inactivity_and_interrupts()
                stale_changed = self._prune_stale()
                changed = interrupted_changed or stale_changed
            if changed:
                self._notify_subscribers()

    def _check_inactivity_and_interrupts(self) -> bool:
        now = time.time()
        changed = False

        for session in self.sessions.values():
            if session.state not in ("running", "ask"):
                continue

            # 1. Transcript-based detection (most accurate for local sessions)
            if session.transcript_path and os.path.exists(session.transcript_path):
                last_step = get_transcript_last_step(session.transcript_path)
                if last_step:
                    step_idx = last_step.get("step_index", -1)
                    step_status = last_step.get("status", "")
                    step_type = last_step.get("type", "")
                    has_error = bool(last_step.get("error"))
                    tool_calls = last_step.get("tool_calls", [])

                    # If a tool is actively running in foreground (e.g. run_command, MCP tool):
                    if session.active_tool_step_idx >= 0:
                        # Has the tool output step been recorded in transcript yet?
                        if step_idx >= session.active_tool_step_idx:
                            # Tool step finished or was interrupted
                            session.active_tool_step_idx = -1
                            if step_status in ("ERROR", "FAILED") or has_error:
                                err_msg = str(last_step.get("error") or "Tool execution error")
                                session.state = "idle"
                                session.substatus = f"Error: {err_msg[:45]}"
                                session.last_updated = now
                                changed = True
                                continue
                            elif step_status in ("CANCELED", "CANCELLED", "ABORTED"):
                                session.state = "idle"
                                session.substatus = "Interrupted"
                                session.last_updated = now
                                changed = True
                                continue
                        else:
                            # Tool is STILL actively executing! Keep running state alive.
                            # Do NOT expire or switch to idle, regardless of elapsed time.
                            session.last_updated = now
                            continue

                    # If we reached here, no tool is running in foreground.
                    # Check if model finished its response or an error/cancel occurred:
                    if step_status in ("ERROR", "FAILED") or has_error:
                        err_msg = str(last_step.get("error") or "Execution error")
                        session.state = "idle"
                        session.substatus = f"Error: {err_msg[:45]}"
                        session.last_updated = now
                        changed = True
                        continue

                    if step_status in ("CANCELED", "CANCELLED", "ABORTED"):
                        session.state = "idle"
                        session.substatus = "Interrupted"
                        session.last_updated = now
                        changed = True
                        continue

                    # Case: Model completed its response without requesting more tools
                    if step_status == "DONE" and step_type == "PLANNER_RESPONSE" and not tool_calls:
                        if (now - session.last_updated) > 1.0:
                            if not session.fully_idle:
                                session.state = "running"
                                session.substatus = "Background tasks running"
                            else:
                                session.state = "idle"
                                session.substatus = "Ready"
                            session.last_updated = now
                            changed = True
                            continue

            # 2. Timeout fallbacks (e.g. remote agents or when transcript is not available)
            # Only apply when no active tool is executing
            if session.active_tool_step_idx < 0 and session.state == "running" and (now - session.last_updated) > 180.0:
                session.state = "idle"
                session.substatus = "Ready"
                session.last_updated = now
                changed = True

        return changed

    def handle_event(self, payload: Dict[str, Any]) -> str:
        with self.lock:
            conv_id = payload.get("conversationId", "default")
            event_type = payload.get("event", "")
            workspace_paths = payload.get("workspacePaths", [])
            workspace = ""
            if workspace_paths and isinstance(workspace_paths, list):
                workspace = workspace_paths[0].rstrip("/").split("/")[-1]
            if not workspace:
                workspace = payload.get("workspace", "workspace")

            host = payload.get("host", socket.gethostname())
            model = payload.get("modelName", "")
            pid = int(payload.get("pid", 0))
            transcript_path = payload.get("transcriptPath", "")

            # Deduplicate: A single terminal process (PID) only has one active conversation.
            # If a new conversation starts on the same PID, remove the older conversation session.
            if pid > 0:
                for other_id, other_sess in list(self.sessions.items()):
                    if other_id != conv_id and other_sess.pid == pid and other_sess.host == host:
                        del self.sessions[other_id]

            if conv_id not in self.sessions:
                self.sessions[conv_id] = AgentSession(
                    conv_id,
                    workspace=workspace,
                    host=host,
                    pid=pid,
                    transcript_path=transcript_path
                )

            session = self.sessions[conv_id]
            session.workspace = workspace
            session.host = host
            if pid > 0:
                session.pid = pid
            if transcript_path:
                session.transcript_path = transcript_path

            new_state = "running"
            substatus = event_type

            if event_type == "PreInvocation":
                new_state = "running"
                substatus = "Thinking / Planning"
                session.active_tool_step_idx = -1
                session.active_tool_name = ""
                session.fully_idle = False
            elif event_type == "PreToolUse":
                tool_call = payload.get("toolCall", {})
                tool_name = tool_call.get("name", "tool") if isinstance(tool_call, dict) else "tool"
                args = tool_call.get("args", {}) if isinstance(tool_call, dict) else {}
                step_idx = payload.get("stepIdx", -1)

                session.active_tool_step_idx = step_idx
                session.active_tool_name = tool_name
                session.fully_idle = False
                
                is_ask = payload.get("waitingApproval", False) or (tool_name in ("ask_question", "request_approval"))
                if is_ask:
                    new_state = "ask"
                    substatus = f"Waiting for user response: {tool_name}"
                else:
                    new_state = "running"
                    arg_summary = ""
                    if tool_name == "run_command":
                        cmd = args.get("CommandLine", "")
                        arg_summary = f": `{cmd[:40]}...`" if len(cmd) > 40 else f": `{cmd}`"
                    elif tool_name in ("write_to_file", "replace_file_content", "view_file"):
                        target = args.get("TargetFile") or args.get("AbsolutePath", "")
                        fname = target.split("/")[-1] if target else ""
                        arg_summary = f": {fname}" if fname else ""
                    elif tool_name.startswith("mcp__"):
                        clean_name = tool_name.split("__")[-1]
                        arg_summary = f" ({clean_name})"
                    substatus = f"Executing {tool_name}{arg_summary}"
            elif event_type == "PostToolUse":
                new_state = "running"
                session.active_tool_step_idx = -1
                session.active_tool_name = ""
                err = payload.get("error")
                if err:
                    substatus = f"Tool failed: {str(err)[:35]}"
                else:
                    substatus = "Tool completed"
            elif event_type == "PostInvocation":
                new_state = "running"
                substatus = "Processing response"
            elif event_type == "Stop":
                fully_idle = payload.get("fullyIdle", True)
                session.fully_idle = fully_idle
                session.active_tool_step_idx = -1
                session.active_tool_name = ""
                error = payload.get("error", "")
                reason = payload.get("terminationReason", "")
                if not fully_idle:
                    new_state = "running"
                    substatus = "Background tasks running"
                elif error:
                    new_state = "idle"
                    substatus = f"Error: {error[:40]}"
                elif reason and reason not in ("model_stop", "stop", ""):
                    new_state = "idle"
                    substatus = f"Ready ({reason})"
                else:
                    new_state = "idle"
                    substatus = "Ready"
            elif event_type == "AskApproval":
                new_state = "ask"
                substatus = payload.get("reason", "Waiting for confirmation")
            elif "state" in payload:
                new_state = payload.get("state", "idle")
                substatus = payload.get("substatus", "")

            session.update(new_state, substatus, model=model, pid=pid, transcript_path=transcript_path)
            self._prune_stale()

        self._notify_subscribers()
        return new_state

    def _prune_stale(self) -> bool:
        stale_keys = [k for k, s in self.sessions.items() if s.is_stale()]
        if stale_keys:
            for k in stale_keys:
                del self.sessions[k]
            return True
        return False

    def clear(self):
        with self.lock:
            self.sessions.clear()
        self._notify_subscribers()

    def get_aggregate_state(self) -> Dict[str, Any]:
        with self.lock:
            self._prune_stale()
            if not self.sessions:
                return {
                    "state": "offline",
                    "icon": ICONS["offline"],
                    "class": CSS_CLASSES["offline"],
                    "active_count": 0,
                    "sessions": [],
                    "tooltip": "Antigravity Traffic Light\n────────────────────\n○ No active agents",
                }

            has_ask = any(s.state == "ask" for s in self.sessions.values())
            has_running = any(s.state == "running" for s in self.sessions.values())
            has_idle = any(s.state == "idle" for s in self.sessions.values())

            if has_ask:
                agg_state = "ask"
            elif has_running:
                agg_state = "running"
            elif has_idle:
                agg_state = "idle"
            else:
                agg_state = "offline"

            tooltip_lines = ["Antigravity Traffic Light", "────────────────────"]
            for s in sorted(self.sessions.values(), key=lambda x: (0 if x.state == 'ask' else (1 if x.state == 'running' else 2))):
                state_symbol = "🔴" if s.state == "ask" else ("🟡" if s.state == "running" else "🟢")
                host_str = f"@{s.host}" if s.host not in ("localhost", socket.gethostname()) else ""
                tooltip_lines.append(f"{state_symbol} [{s.workspace}{host_str}]: {s.substatus}")

            return {
                "state": agg_state,
                "icon": ICONS[agg_state],
                "class": CSS_CLASSES[agg_state],
                "active_count": len(self.sessions),
                "sessions": [s.to_dict() for s in self.sessions.values()],
                "tooltip": "\n".join(tooltip_lines),
            }

    def get_waybar_payload(self) -> Dict[str, Any]:
        agg = self.get_aggregate_state()
        return {
            "text": agg["icon"],
            "alt": agg["state"],
            "tooltip": agg["tooltip"],
            "class": agg["class"],
            "percentage": 100 if agg["state"] == "running" else 0,
        }

    def register_subscriber(self, q):
        with self.lock:
            self.subscribers.append(q)

    def unregister_subscriber(self, q):
        with self.lock:
            if q in self.subscribers:
                self.subscribers.remove(q)

    def _notify_subscribers(self):
        payload = self.get_waybar_payload()
        for q in list(self.subscribers):
            try:
                q(payload)
            except Exception:
                pass


STATE_MANAGER = StateManager()


class TrafficLightHTTPHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/status":
            data = STATE_MANAGER.get_aggregate_state()
            self._send_json(200, data)
        elif path == "/waybar":
            data = STATE_MANAGER.get_waybar_payload()
            self._send_json(200, data)
        elif path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._set_cors_headers()
            self.end_headers()

            queue_lock = threading.Event()
            queue_data = [STATE_MANAGER.get_waybar_payload()]

            def subscriber(data):
                queue_data.append(data)
                queue_lock.set()

            STATE_MANAGER.register_subscriber(subscriber)
            try:
                while True:
                    while queue_data:
                        msg = queue_data.pop(0)
                        payload = f"data: {json.dumps(msg)}\n\n"
                        self.wfile.write(payload.encode("utf-8"))
                        self.wfile.flush()
                    queue_lock.wait(timeout=15.0)
                    queue_lock.clear()
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                STATE_MANAGER.unregister_subscriber(subscriber)
        elif path == "/health":
            self._send_json(200, {"status": "ok", "time": time.time()})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        if path in ("/event", "/events"):
            new_state = STATE_MANAGER.handle_event(payload)
            self._send_json(200, {"status": "ok", "new_state": new_state})
        elif path == "/clear":
            STATE_MANAGER.clear()
            self._send_json(200, {"status": "cleared"})
        else:
            self._send_json(404, {"error": "Not found"})

    def _send_json(self, code: int, data: Any):
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        pass


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    server = HTTPServer((host, port), TrafficLightHTTPHandler)
    print(f"[agy-traffic-daemon] Listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[agy-traffic-daemon] Stopping...")
        server.server_close()


def stream_waybar_stdout(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    import urllib.request
    url = f"http://{host}:{port}/waybar"
    
    last_output = ""
    while True:
        try:
            req = urllib.request.urlopen(url, timeout=2.0)
            data = req.read().decode("utf-8")
            if data != last_output:
                print(data, flush=True)
                last_output = data
        except Exception:
            offline_payload = json.dumps({
                "text": ICONS["offline"],
                "alt": "offline",
                "tooltip": "Antigravity Traffic Light\n────────────────────\n○ Daemon offline",
                "class": "offline"
            })
            if offline_payload != last_output:
                print(offline_payload, flush=True)
                last_output = offline_payload
        time.sleep(0.5)


def print_waybar_once(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    import urllib.request
    url = f"http://{host}:{port}/waybar"
    try:
        req = urllib.request.urlopen(url, timeout=2.0)
        print(req.read().decode("utf-8"))
    except Exception:
        print(json.dumps({
            "text": ICONS["offline"],
            "alt": "offline",
            "tooltip": "Daemon offline",
            "class": "offline"
        }))


def main():
    parser = argparse.ArgumentParser(description="Antigravity Traffic Light Daemon")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on (default: 9876)")
    parser.add_argument("--waybar-stream", action="store_true", help="Stream Waybar JSON to stdout")
    parser.add_argument("--waybar-once", action="store_true", help="Print single Waybar JSON to stdout and exit")
    args = parser.parse_args()

    if args.waybar_stream:
        stream_waybar_stdout(args.host, args.port)
    elif args.waybar_once:
        print_waybar_once(args.host, args.port)
    else:
        run_server(args.host, args.port)


if __name__ == "__main__":
    main()
