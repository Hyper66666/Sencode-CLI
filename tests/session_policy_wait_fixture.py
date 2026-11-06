"""Owned Windows console and synthetic child-wait / session-policy regression."""
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
from terminal_pane_console_fixture import resize_fullscreen
from tui_console_fixture import Console, Coord, checked, environment_for, write_json


def prepare_owned_console(console):
    # Sixty transcript rows must fit even on a small desktop. This font change
    # affects only the fixture's hidden conhost, never the user's terminal.
    class FontInfoEx(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.ULONG), ("index", wintypes.DWORD),
                    ("size", Coord), ("family", wintypes.UINT),
                    ("weight", wintypes.UINT), ("face", wintypes.WCHAR * 32)]
    console.kernel.GetCurrentConsoleFontEx.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(FontInfoEx)]
    console.kernel.GetCurrentConsoleFontEx.restype = wintypes.BOOL
    console.kernel.SetCurrentConsoleFontEx.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(FontInfoEx)]
    console.kernel.SetCurrentConsoleFontEx.restype = wintypes.BOOL
    font = FontInfoEx(); font.cbSize = ctypes.sizeof(font)
    checked(console.kernel.GetCurrentConsoleFontEx(console.output, False, ctypes.byref(font)))
    font.size = Coord(5, 10); font.face = "Consolas"
    checked(console.kernel.SetCurrentConsoleFontEx(console.output, False, ctypes.byref(font)))
    resize_fullscreen(console, 120, 60)


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *_): pass
    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.server.requests.append(request)
            messages = request["messages"]
            latest = max(i for i, m in enumerate(messages) if m["role"] == "user")
            prompt = messages[latest]["content"]
            tools = [m for m in messages[latest + 1:] if m["role"] == "tool"]
            calls = []
            text = ""
            if request["model"] == "child":
                if not tools:
                    calls = [("child-read", "list_directory", {"path": "."})]
                else:
                    self.server.child_started.set()
                    time.sleep(2.2)
                    text = "CHILD_FINISHED"
            elif prompt.startswith("WAIT_") or prompt.startswith("Current child task results"):
                if not tools and prompt.startswith("WAIT_"):
                    count = 2 if prompt == "WAIT_TWO" else 1
                    calls = [(f"spawn-{i}", "spawn_agent", {"role": "explore", "prompt": "inspect", "model": "child"}) for i in range(count)]
                    text = "START_CHILDREN"
                elif not any(m.get("tool_call_id") == "parent-wait" for m in tools) and tools:
                    calls = [("parent-wait", "wait_agents", {"timeout_ms": 100})]
                else:
                    text = "PARENT_CONTINUED"
            elif prompt == "POLICY_EDIT":
                if not tools: calls = [("policy-edit", "write_file", {"path": "policy.txt", "content": "saved permission"})]
                else: text = "POLICY_FINISHED"
            elif prompt == "GROUPING":
                text = ("BEFORE_GROUP", "MIDDLE_GROUP", "AFTER_GROUP")[min(len(tools), 2)]
                if len(tools) < 2: calls = [(f"group-{len(tools)}", "read_file", {"path": "policy.txt"})]
            elif prompt == "SLOW_POLICY":
                self.server.child_started.set()
                deadline = time.monotonic() + 12
                while not self.server.release.wait(.02) and time.monotonic() < deadline: pass
                calls = [("slow-policy-edit", "write_file", {"path": "slow-policy.txt", "content": "immutable permission"})]
                if tools: calls = []; text = "SLOW_POLICY_FINISHED"
            else:
                text = "ACK " + prompt
            self.send_response(200); self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close"); self.end_headers()
            delta = {"content": text}
            if calls:
                delta["tool_calls"] = [{"index": i, "id": ident, "function": {"name": name, "arguments": json.dumps(arguments)}} for i, (ident, name, arguments) in enumerate(calls)]
            event = {"choices": [{"delta": delta, "finish_reason": "tool_calls" if calls else "stop"}], "usage": {"prompt_tokens": 13, "completion_tokens": 7}}
            self.wfile.write(("data: " + json.dumps(event) + "\n\ndata: [DONE]\n\n").encode()); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass
        except BaseException: self.server.errors.append(traceback.format_exc())
        finally: self.close_connection = True


def worker(args):
    evidence = {"schema": 1, "result": "running", "scope": "Owned profile, real console and synthetic loopback provider; no live service",
                "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(), "checks": [], "snapshots": {}}
    process = None; console = None; hosts = []
    identifier = "policy-wait-" + uuid.uuid4().hex
    target = "Sencode/connection/" + identifier
    credential_written = False
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests = []; server.errors = []; server.child_started = threading.Event(); server.release = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]; advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]; advapi.CredDeleteW.restype = wintypes.BOOL
    def record(name, detail=None): evidence["checks"].append({"name": name, "status": "passed", "detail": detail})
    try:
        deadline = time.monotonic() + 10
        while not args.ready.exists():
            assert time.monotonic() < deadline; time.sleep(.02)
        environment = environment_for(args.scratch); os.environ.clear(); os.environ.update(environment)
        workspace = args.scratch / "workspace-中文"; workspace.mkdir()
        database = args.scratch / "catalog.sqlite3"
        def run(*options, stdin="/exit\n", ok=True):
            result = subprocess.run([str(args.executable), "--cwd", str(workspace), "--database", str(database), "--tui", "plain", *map(str, options)],
                                    input=stdin, cwd=workspace, env=environment, capture_output=True, encoding="utf-8", errors="replace", timeout=25)
            assert (result.returncode == 0) == ok, (result.returncode, result.stdout, result.stderr)
            return result
        def sql(query, values=()):
            with closing(sqlite3.connect(database, timeout=5)) as db:
                db.create_function("sengoo_context", 1, lambda key: "policy-fixture" if key == "instance_id" else None)
                rows = db.execute(query, values).fetchall(); db.commit(); return rows
        def eventually(predicate, description):
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if predicate(): return
                assert process is None or process.poll() is None, description
                time.sleep(.01)
            raise AssertionError(description)
        def saved_policy(session):
            rows = sql("SELECT json_extract(mode_json,'$.cli_permissions') FROM shared_modes WHERE session_id=?", (session,))
            return json.loads(rows[0][0]) if rows and rows[0][0] else None
        run("doctor")
        config = {"baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "chatCompletions", "enabledModels": [{"id": "parent"}, {"id": "child"}]}
        sql("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','policy loopback',?,'parent',1,1)", (identifier, json.dumps(config)))
        blob = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
        credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=blob, Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(credential), 0)); credential_written = True
        wait_session = None
        for prompt in ("WAIT_ONE", "WAIT_TWO"):
            host = Host(args.executable, workspace, database, identifier); hosts.append(host)
            if wait_session is None: wait_session = host.session
            start = host.submit(prompt, prompt, maximum_requests=20)
            result = host.wait("result", prompt, start, timeout=20)
            evidence["wait_result_" + prompt] = result
            assert result["code"] == 0, result
            events = host.events[start:]
            child_events = [json.loads(e["text"])["agent"] for e in events if e.get("type") == "agent"]
            finished = [e for e in child_events if e["kind"] == "finished"]
            expected = 2 if prompt == "WAIT_TWO" else 1
            assert len(finished) == expected and all(e["value"]["error"] == 0 for e in finished), finished
            child_states = sql("SELECT e.active,e.cleanup_required FROM shared_modes m JOIN shared_executions e USING(session_id) WHERE json_extract(m.mode_json,'$.session_origin.parent_session_id')=?", (host.session,))
            assert len(child_states) == expected and all(s == (0, 0) for s in child_states), child_states
            assert not any(e.get("code") == 12 for e in events), events[-5:]
            assert result["success"] and any("CHILD_FINISHED" in json.dumps(e) for e in events), events[-8:]
            record(prompt.lower() + "-resumes-without-cancelling-children", {"result": result, "child_states": child_states})
            host.stop()
        server.child_started.clear()
        host = Host(args.executable, workspace, database, identifier); hosts.append(host)
        start = host.submit("cancel-wait", "WAIT_TWO", maximum_requests=20)
        assert server.child_started.wait(8), "children never reached the slow provider"
        cancelled_at = time.monotonic(); host.send({"type": "cancel", "id": "cancel-wait"})
        cancelled = host.result("cancel-wait", start, code=19)
        assert time.monotonic() - cancelled_at < 5, cancelled
        record("cancel-during-capacity-wait-remains-responsive")
        host.stop()
        host = Host(args.executable, workspace, database, identifier); hosts.append(host)
        start = host.submit("real-budget", "WAIT_TWO", maximum_requests=3)
        limited = host.result("real-budget", start, code=13)
        assert limited["diagnostic"]["reason"] == "budget", limited
        record("real-shared-budget-remains-distinct-from-capacity", limited)
        host.stop()
        run("--connection", identifier, "-p", "POLICY_SESSION", "--output-format", "json")
        session = sql("SELECT id FROM sessions WHERE last_sent_at IS NOT NULL ORDER BY last_sent_at DESC LIMIT 1")[0][0]
        run("resume", session, stdin="/permissions full\n/exit\n")
        stored = sql("SELECT json_extract(mode_json,'$.cli_permissions.mode') FROM shared_modes WHERE session_id=?", (session,))[0][0]
        assert stored == "full", stored
        record("unsent-permission-selection-is-persisted")
        console = Console(); prepare_owned_console(console); console.clear(); baseline = console.modes()
        def launch(*options, label="完全权限"):
            nonlocal process
            console.clear()
            process = subprocess.Popen([str(args.executable), "--cwd", str(workspace), "--database", str(database), *map(str, options)], cwd=workspace, env=environment)
            return wait(console, process, lambda s: "MESSAGE" in s["text"] and label in s["text"], "restored policy " + label)
        def stop():
            nonlocal process
            console.key(0x44, "\x04", 8); process.wait(timeout=12)
            assert process.returncode == 0 and console.modes() == baseline
            process = None
        def slash(name):
            command, _, argument = name.partition(" ")
            console.key(0x55, "\x15", 8); console.inject(command)
            wait(console, process, lambda s: "COMMANDS" in s["text"] and any(command in r["text"] for r in s["rows"] if "│ > " in r["text"]), "command menu")
            console.key(0x0D, "\r")
            wait(console, process, lambda s: "Command completed" in s["text"] and "COMMANDS" not in s["text"], "command completion")
            if argument:
                console.inject(argument)
                wait(console, process, lambda s: any(argument in r["text"] for r in s["rows"] if "│ > " in r["text"]), "command argument")
            console.key(0x0D, "\r")
        launch("resume", wait_session, label="手动审批")
        speakers = [r["text"].strip() for r in console.read(viewport=True)["rows"] if r["text"].strip() in {"YOU", "SENCODE"}]
        assert speakers == ["YOU", "SENCODE"], speakers
        record("restored-coordinator-context-does-not-create-user-turns")
        stop()
        screen = launch("resume", session)
        evidence["snapshots"]["restored-full"] = screen
        record("fullscreen-resume-restores-permission-footer")
        console.command("POLICY_EDIT")
        screen = wait(console, process, lambda s: "POLICY_FINISHED" in s["text"] and "NEXT MESSAGE" not in s["text"], "restored policy executes without reapproval")
        assert (workspace / "policy.txt").read_text() == "saved permission"
        record("restored-permission-controls-actual-edit")
        console.command("GROUPING")
        screen = wait(console, process, lambda s: "AFTER_GROUP" in s["text"] and "NEXT MESSAGE" not in s["text"], "tool-segment grouping")
        for width in (80, 120, 160):
            resize_fullscreen(console, width, 60)
            screen = wait(console, process, lambda s: s["width"] == width and "AFTER_GROUP" in s["text"], "grouping after resize")
            speakers = [r["text"].strip() for r in screen["rows"] if r["text"].strip() in {"YOU", "SENCODE"}]
            assert speakers == ["YOU", "SENCODE"] * 3, speakers
            assert all(word in screen["text"] for word in ("BEFORE_GROUP", "MIDDLE_GROUP", "AFTER_GROUP")), screen["text"]
            record(f"one-assistant-heading-per-user-{width}")
        evidence["snapshots"]["grouped-live"] = screen
        stop()
        screen = launch("-c")
        speakers = [r["text"].strip() for r in screen["rows"] if r["text"].strip() in {"YOU", "SENCODE"}]
        assert speakers == ["YOU", "SENCODE"] * 3, speakers
        record("continue-restores-grouped-transcript-and-full-permission")
        server.child_started.clear()
        console.command("SLOW_POLICY")
        wait(console, process, lambda s: "NEXT MESSAGE" in s["text"], "running policy snapshot")
        assert server.child_started.wait(5)
        console.key(0x09, "\t", 0x10)
        wait(console, process, lambda s: "下轮 手动审批" in s["text"], "future policy switch")
        assert saved_policy(session)["mode"] == "full", saved_policy(session)
        record("busy-permission-choice-does-not-rewrite-active-policy")
        server.release.set()
        screen = wait(console, process, lambda s: "SLOW_POLICY_FINISHED" in s["text"] and "NEXT MESSAGE" not in s["text"], "immutable edit and cleanup")
        assert (workspace / "slow-policy.txt").read_text() == "immutable permission"
        eventually(lambda: saved_policy(session)["mode"] == "manual", "deferred policy was not saved after cleanup")
        record("future-permission-saved-after-cleanup-current-edit-retains-full")
        stop()
        launch("-r", session, label="手动审批"); stop()
        record("short-resume-restores-manual")
        launch("resume", session, "--permissions", "auto", label="自动审批"); stop()
        record("explicit-permission-override-is-remembered")
        launch("resume", session, label="自动审批")
        console.key(0x09, "\t", 0x10)
        evidence["snapshots"]["unsent-full"] = wait(console, process, lambda s: "完全权限" in s["text"] and "自动审批" not in s["text"], "unsent full selection")
        eventually(lambda: saved_policy(session)["mode"] == "full", "idle permission selection was not saved")
        stop()
        assert saved_policy(session)["mode"] == "full", saved_policy(session)
        record("unsent-shift-tab-selection-survives-exit")
        labels = {"manual": "手动审批", "auto": "自动审批", "full": "完全权限"}
        previous = "full"
        for index, mode in enumerate(("manual", "auto", "full", "manual", "auto", "full")):
            launch("resume", session, label=labels[previous])
            console.key(0x09, "\t", 0x10)
            wait(console, process, lambda s: labels[mode] in s["text"] and labels[previous] not in s["text"], "immediate startup permission cycle")
            eventually(lambda: saved_policy(session)["mode"] == mode, "startup permission selection was not saved")
            stop(); previous = mode
            record(f"immediate-startup-permission-save-{index}-{mode}")
        run("--connection", identifier, "-p", "OTHER_SESSION", "--output-format", "json")
        other = sql("SELECT id FROM sessions WHERE title='OTHER_SESSION'")[0][0]
        launch("resume", other, label="手动审批")
        slash("/resume " + session)
        wait(console, process, lambda s: "完全权限" in s["text"] and "COMMANDS" not in s["text"], "in-app permission restore")
        record("in-app-switch-loads-destination-policy")
        slash("/plan")
        wait(console, process, lambda s: "规划只读" in s["text"], "Plan remains separate")
        console.key(0x09, "\t", 0x10)
        wait(console, process, lambda s: "手动审批" in s["text"] and "规划只读" in s["text"], "permission switch retains Plan")
        record("permission-change-cannot-leave-plan")
        stop()
        renamed = args.scratch / "renamed 项目"; workspace.rename(renamed); workspace = renamed
        launch("resume", session, label="手动审批"); stop()
        record("project-rename-retains-local-session-permission")
        record("console-restored")
        assert not server.errors, server.errors
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"; evidence["error"] = traceback.format_exc()
        if "sql" in locals():
            evidence["execution_state_on_failure"] = sql("SELECT session_id,active,cleanup_required FROM shared_executions")
            evidence["permission_state_on_failure"] = sql("SELECT session_id,json_extract(mode_json,'$.cli_permissions') FROM shared_modes WHERE json_extract(mode_json,'$.cli_permissions') IS NOT NULL")
        if console is not None and process is not None and process.poll() is None: evidence["last_screen"] = console.read(viewport=True)
    finally:
        server.release.set()
        if process is not None and process.poll() is None: process.terminate(); process.wait(timeout=5)
        for host in hosts: host.abort()
        if credential_written: checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown(); server.server_close()
        evidence["provider_errors"] = server.errors
        evidence["fixture_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        write_json(args.evidence, evidence)
    return 0 if evidence["result"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path); parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--worker", action="store_true"); parser.add_argument("--scratch", type=Path); parser.add_argument("--ready", type=Path)
    args = parser.parse_args(); args.executable = args.executable.resolve(strict=True); args.evidence = args.evidence.resolve()
    if args.worker: return worker(args)
    harness.__file__ = __file__
    return harness.controller(args)


if __name__ == "__main__": raise SystemExit(main())
