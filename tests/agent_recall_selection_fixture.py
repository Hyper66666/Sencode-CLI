"""Real native host/console, slow loopback children and optional private clipboard.

No live services or user data. --clipboard additionally requires a private window
station and desktop; denied isolation fails instead of using the user's station.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import ctypes
from ctypes import wintypes
import hashlib
import http.server
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import threading
import time
import traceback
import uuid

import agent_reliability_fixture as harness
from cli_fixture import Credential
from engine_fixture import Host
from fullscreen_console_fixture import wait
from session_policy_wait_fixture import prepare_owned_console
from tui_console_fixture import Console, Coord, InputRecord, checked, environment_for, write_json


class PrivateClipboard:
    def __init__(self):
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        for name, arguments, result in [
            ("GetProcessWindowStation", [], wintypes.HANDLE),
            ("GetThreadDesktop", [wintypes.DWORD], wintypes.HANDLE),
            ("CreateWindowStationW", [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p], wintypes.HANDLE),
            ("SetProcessWindowStation", [wintypes.HANDLE], wintypes.BOOL),
            ("CreateDesktopW", [wintypes.LPCWSTR, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p], wintypes.HANDLE),
            ("SetThreadDesktop", [wintypes.HANDLE], wintypes.BOOL),
            ("CloseWindowStation", [wintypes.HANDLE], wintypes.BOOL),
            ("CloseDesktop", [wintypes.HANDLE], wintypes.BOOL),
            ("OpenClipboard", [wintypes.HWND], wintypes.BOOL),
            ("CloseClipboard", [], wintypes.BOOL),
            ("GetClipboardData", [wintypes.UINT], wintypes.HANDLE),
        ]:
            function = getattr(self.user, name); function.argtypes = arguments; function.restype = result
        self.kernel.GetCurrentThreadId.restype = wintypes.DWORD
        self.kernel.GlobalLock.argtypes = [wintypes.HANDLE]; self.kernel.GlobalLock.restype = ctypes.c_void_p
        self.kernel.GlobalUnlock.argtypes = [wintypes.HANDLE]; self.kernel.GlobalUnlock.restype = wintypes.BOOL
        self.original_station = self.user.GetProcessWindowStation()
        self.original_desktop = self.user.GetThreadDesktop(self.kernel.GetCurrentThreadId())
        name = "SencodeSelection-" + uuid.uuid4().hex
        self.station = checked(self.user.CreateWindowStationW(name, 0, 0x37F, None))
        checked(self.user.SetProcessWindowStation(self.station))
        self.desktop = checked(self.user.CreateDesktopW("Fixture", None, None, 0, 0x1FF, None))
        checked(self.user.SetThreadDesktop(self.desktop))
        self.path = name + "\\Fixture"

    def read(self):
        checked(self.user.OpenClipboard(None))
        try:
            handle = self.user.GetClipboardData(13)
            if not handle: return ""
            pointer = checked(self.kernel.GlobalLock(handle))
            try: return ctypes.wstring_at(pointer)
            finally: self.kernel.GlobalUnlock(handle)
        finally: checked(self.user.CloseClipboard())

    def close(self):
        checked(self.user.SetThreadDesktop(self.original_desktop))
        checked(self.user.SetProcessWindowStation(self.original_station))
        checked(self.user.CloseDesktop(self.desktop)); checked(self.user.CloseWindowStation(self.station))


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *_): pass

    def frame(self, text="", calls=(), done=False):
        delta = {"content": text}
        if calls:
            delta["tool_calls"] = [{"index": i, "id": ident, "function": {"name": name, "arguments": json.dumps(args)}}
                                   for i, (ident, name, args) in enumerate(calls)]
        event = {"choices": [{"delta": delta, "finish_reason": "tool_calls" if calls else "stop" if done else None}]}
        if done or calls: event["usage"] = {"prompt_tokens": 11, "completion_tokens": 5}
        self.wfile.write(("data: " + json.dumps(event, ensure_ascii=False) + "\n\n").encode("utf-8")); self.wfile.flush()

    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.server.requests.append(request)
            messages = request["messages"]
            prompt = next(m["content"] for m in reversed(messages) if m["role"] == "user")
            tools = [m for m in messages if m["role"] == "tool"]
            self.send_response(200); self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close"); self.end_headers()
            if request["model"] == "child":
                if not tools:
                    self.frame("CHILD_PARTIAL", [("child-read", "list_directory", {"path": "."})])
                else:
                    self.frame("CHILD_STREAMING "); time.sleep(5.2 if "second" in prompt else 3.2)
                    self.frame("CHILD_DONE", done=True)
            elif prompt in {"EXPLICIT", "IMPLICIT"}:
                if not tools:
                    count = 2 if prompt == "EXPLICIT" else 1
                    calls = [(f"spawn-{i}", "spawn_agent", {"role": "explore", "prompt": "second" if i else "first", "model": "child"}) for i in range(count)]
                    self.frame("DELEGATED_ONCE", calls)
                elif prompt == "IMPLICIT":
                    self.frame("WAITING_ONCE", done=True)
                else:
                    reports = json.loads(tools[-1]["content"])
                    children = reports.get("children", [])
                    if children and all(c["done"] for c in children):
                        self.frame("FINAL_EXPLICIT", done=True)
                    else:
                        assert all(c["content"] == "" for c in children if not c["done"]), children
                        self.frame("WAITING_ONCE", [(f"wait-{len(tools)}", "wait_agents", {"timeout_ms": 100})])
            elif prompt.startswith("Current child task results"):
                self.frame("FINAL_IMPLICIT", done=True)
            elif prompt == "SELECT":
                self.frame("alpha 中文 e\u0301 👨\u200d👩\u200d👧 end\nsecond selectable line\n")
                time.sleep(3.5); self.frame("SELECT_FINISHED", done=True)
            else:
                self.frame("ACK " + prompt, done=True)
            self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass
        except BaseException: self.server.errors.append(traceback.format_exc())
        finally: self.close_connection = True


def mouse(console, screen, row, column, buttons, flags=0):
    class MouseEvent(ctypes.Structure):
        _fields_ = [("position", Coord), ("buttons", wintypes.DWORD), ("modifiers", wintypes.DWORD), ("flags", wintypes.DWORD)]
    event = InputRecord(); event.EventType = 2
    # Console events use screen-buffer coordinates; application exposes cells
    # relative to its viewport. Keep the owned host's current window offset.
    viewport = console.info().srWindow
    data = MouseEvent(Coord(column + viewport.Left, row + viewport.Top), buttons, 0, flags)
    ctypes.memmove(ctypes.byref(event.Event), ctypes.byref(data), ctypes.sizeof(data))
    written = wintypes.DWORD(); checked(console.kernel.WriteConsoleInputW(console.input, ctypes.byref(event), 1, ctypes.byref(written)))


def worker(args):
    evidence = {"schema": 1, "result": "running", "scope": "Owned real console and loopback provider; no live service",
                "clipboard": "requested-private-station" if args.clipboard else "not-requested; selection and copy dispatch tested separately",
                "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(), "checks": [], "snapshots": {}}
    clipboard = None; process = None; console = None; hosts = []; credential_written = False; serving = False
    identifier = "recall-selection-" + uuid.uuid4().hex; target = "Sencode/connection/" + identifier
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider); server.requests = []; server.errors = []
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]; advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]; advapi.CredDeleteW.restype = wintypes.BOOL
    def record(name, detail=None): evidence["checks"].append({"name": name, "status": "passed", "detail": detail})
    try:
        deadline = time.monotonic() + 10
        while not args.ready.exists(): assert time.monotonic() < deadline; time.sleep(.02)
        if args.clipboard:
            clipboard = PrivateClipboard()
            record("clipboard-isolated-from-interactive-window-station")
        threading.Thread(target=server.serve_forever, daemon=True).start(); serving = True
        environment = environment_for(args.scratch); os.environ.clear(); os.environ.update(environment)
        workspace = args.scratch / "workspace-中文"; workspace.mkdir(); database = args.scratch / "catalog.sqlite3"
        common = ["--cwd", str(workspace), "--database", str(database), "--connection", identifier]
        initial = subprocess.run([str(args.executable), *common, "doctor"], capture_output=True, timeout=25)
        assert initial.returncode == 0, initial.stderr.decode(errors="replace")
        def sql(query, values=()):
            with closing(sqlite3.connect(database, timeout=5)) as db:
                db.create_function("sengoo_context", 1, lambda key: "recall-fixture" if key == "instance_id" else None)
                result = db.execute(query, values).fetchall(); db.commit(); return result
        config = {"baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "chatCompletions", "enabledModels": [{"id": "parent"}, {"id": "child"}]}
        sql("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','recall loopback',?,'parent',1,1)", (identifier, json.dumps(config)))
        key = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
        checked(advapi.CredWriteW(ctypes.byref(Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=key, Persist=1)), 0)); credential_written = True
        for prompt, maximum in (("EXPLICIT", 4), ("IMPLICIT", 3)):
            first = len(server.requests); host = Host(args.executable, workspace, database, identifier); hosts.append(host)
            start = host.submit(prompt, prompt, maximum_requests=24); result = host.wait("result", prompt, start, timeout=25)
            assert result["success"] and ("FINAL_" + prompt) in result["content"], result
            parent = [r for r in server.requests[first:] if r["model"] == "parent"]
            assert len(parent) <= maximum, len(parent)
            if prompt == "IMPLICIT":
                notifications = [m for m in parent[-1]["messages"] if m["role"] == "user" and m["content"].startswith("Current child task results")]
                assert len(notifications) == 1, notifications
            record(prompt.lower() + "-wait-resumes-only-on-terminal-progress", {"parent_requests": len(parent)})
            host.stop()
        console = Console(); prepare_owned_console(console); console.clear(); baseline = console.modes()
        startup = subprocess.STARTUPINFO()
        if clipboard is not None: startup.lpDesktop = clipboard.path
        def launch(*options):
            nonlocal process
            console.clear()
            process = subprocess.Popen([str(args.executable), "--cwd", str(workspace), "--database", str(database), "--connection", identifier, *options], cwd=workspace, startupinfo=startup)
            return wait(console, process, lambda s: "MESSAGE" in s["text"], "composer ready", 20)
        def stop():
            nonlocal process
            console.key(0x55, "\x15", 8); console.key(0x44, "\x04", 8); process.wait(timeout=12)
            assert process.returncode == 0 and console.modes() == baseline; process = None
        def composer(screen): return "\n".join(r["text"] for r in screen["rows"] if "│ > " in r["text"] or "│   " in r["text"])
        def slash(name):
            command, _, value = name.partition(" "); console.key(0x55, "\x15", 8); console.inject(command)
            wait(console, process, lambda s: "COMMANDS" in s["text"] and command in composer(s), "slash menu")
            console.key(0x0D, "\r"); wait(console, process, lambda s: "Command completed" in s["text"] and "COMMANDS" not in s["text"], "completion")
            if value: console.inject(value)
            console.key(0x0D, "\r")
        launch(); console.command("SELECT")
        screen = wait(console, process, lambda s: "alpha 中文" in s["text"] and "second selectable" in s["text"], "streamed output")
        row = next(i for i, r in enumerate(screen["rows"]) if "alpha 中文" in r["text"])
        column = next(i for i, (ch, _) in enumerate(screen["rows"][row]["cells"]) if ch == ord("中"))
        end_column = next(i for i, (ch, _) in enumerate(screen["rows"][row]["cells"]) if ch == ord("文"))
        mouse(console, screen, row, column, 1); mouse(console, screen, row, end_column, 1, 1); mouse(console, screen, row, end_column, 0)
        selected = wait(console, process, lambda s: "Esc clear selection" in s["text"], "drag selection")
        evidence["snapshots"]["selection"] = selected
        if clipboard is not None:
            console.key(0x43, "\x03", 8)
            wait(console, process, lambda s: "Copied to clipboard" in s["text"], "explicit copy")
            assert clipboard.read() == "中文", repr(clipboard.read())
            record("real-unicode-drag-and-ctrl-c-copy-without-cancellation")
        else:
            record("real-unicode-drag-without-touching-user-clipboard")
        time.sleep(3.7)
        assert "SELECT_FINISHED" not in console.read(viewport=True)["text"], "stream replaced selected cells"
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "SELECT_FINISHED" in s["text"] and "NEXT MESSAGE" not in s["text"], "clear returns to live result")
        record("selected-cells-stay-stable-while-host-finishes-streaming")
        session = sql("SELECT id FROM sessions WHERE title='SELECT'")[0][0]
        for i in range(13):
            text = f"INPUT_{i:02}"; console.command(text)
            wait(console, process, lambda s: "ACK " + text in s["text"] and "NEXT MESSAGE" not in s["text"], "input saved")
        stop(); launch("resume", session)
        console.inject("unsent draft"); console.key(0x26)
        wait(console, process, lambda s: "INPUT_12" in composer(s), "latest input")
        for _ in range(15): console.key(0x26)
        wait(console, process, lambda s: "INPUT_03" in composer(s), "oldest of ten")
        for _ in range(10): console.key(0x28)
        wait(console, process, lambda s: "unsent draft" in composer(s), "unsent draft restored")
        record("ten-session-inputs-survive-exit-and-arrows-restore-draft")
        slash("/new"); wait(console, process, lambda s: "INPUT_" not in s["text"] and "MESSAGE" in s["text"], "new session")
        console.key(0x26); time.sleep(.1)
        assert "INPUT_" not in composer(console.read(viewport=True))
        record("new-session-never-inherits-input-recall")
        slash("/resume " + session)
        wait(console, process, lambda s: "SELECT_FINISHED" in s["text"] or "ACK INPUT_12" in s["text"], "switch back")
        console.key(0x26); wait(console, process, lambda s: "/new" in composer(s), "source ring restored")
        slash("/branch separate"); time.sleep(.2); console.key(0x26)
        screen = console.read(viewport=True); assert "/new" not in composer(screen) and "INPUT_" not in composer(screen), composer(screen)
        record("branch-has-independent-recall-despite-copied-transcript")
        stop(); renamed = args.scratch / "renamed-项目"; workspace.rename(renamed); workspace = renamed
        launch("resume", session); console.key(0x26)
        wait(console, process, lambda s: "/branch separate" in composer(s), "project rename retains ring")
        record("project-folder-rename-retains-local-session-recall")
        stop(); record("normal-exit-restores-console")
        assert not server.errors, server.errors
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"; evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None and console is not None: evidence["last_screen"] = console.read(viewport=True)
    finally:
        if process is not None and process.poll() is None: process.terminate(); process.wait(timeout=5)
        for host in hosts: host.abort()
        if credential_written: checked(advapi.CredDeleteW(target, 1, 0))
        if serving: server.shutdown()
        if clipboard is not None: clipboard.close()
        server.server_close(); evidence["provider_errors"] = server.errors
        evidence["fixture_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        write_json(args.evidence, evidence)
    return 0 if evidence["result"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path); parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--clipboard", action="store_true", help="Require private-station Windows clipboard integration")
    parser.add_argument("--worker", action="store_true"); parser.add_argument("--scratch", type=Path); parser.add_argument("--ready", type=Path)
    args = parser.parse_args(); args.executable = args.executable.resolve(strict=True); args.evidence = args.evidence.resolve()
    if args.worker:
        args.clipboard = args.clipboard or os.environ.get("SENCODE_FIXTURE_PRIVATE_CLIPBOARD") == "1"
        return worker(args)
    if args.clipboard:
        # The shared controller owns the child Job; carry this explicit scope to
        # its worker without weakening the default no-user-clipboard boundary.
        os.environ["SENCODE_FIXTURE_PRIVATE_CLIPBOARD"] = "1"
    harness.__file__ = __file__
    return harness.controller(args)


if __name__ == "__main__": raise SystemExit(main())
