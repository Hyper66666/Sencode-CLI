"""One-turn Plan with the real host, portable SQLite and an owned console.

Only model responses are simulated. No live provider or user profile is used.
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
from tui_console_fixture import Console, checked, environment_for, write_json


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *_): pass

    def frame(self, text, tool=None):
        delta = {"content": text}
        if tool:
            name, args = tool
            delta["tool_calls"] = [{"index": 0, "id": "call-" + uuid.uuid4().hex, "function": {"name": name, "arguments": json.dumps(args)}}]
        event = {"choices": [{"delta": delta, "finish_reason": "tool_calls" if tool else "stop"}], "usage": {"prompt_tokens": 11, "completion_tokens": 5}}
        self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode()); self.wfile.flush()

    def do_POST(self):
        try:
            assert self.headers["Authorization"] == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = request["messages"]; system = messages[0]["content"]
            last = max(i for i, value in enumerate(messages) if value["role"] == "user")
            prompt = messages[last]["content"]; results = [m for m in messages[last + 1:] if m["role"] == "tool"]
            planning = "PLAN MODE FOR THIS TURN ONLY:" in system
            self.server.requests.append({"prompt": prompt, "planning": planning})
            assert planning == prompt.startswith("PLAN_"), (prompt, planning)
            self.server.started.set()
            if prompt == "PLAN_FAIL":
                self.send_response(503); self.send_header("Content-Length", "0"); self.send_header("Connection", "close"); self.end_headers(); return
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Connection", "close"); self.end_headers()
            if prompt in {"PLAN_SLOW", "PLAN_QUEUE", "PLAN_CRASH"}:
                self.server.started.set(); self.frame("PLAN_PARTIAL")
                self.server.release.wait(12)
                self.frame("PLAN_FINISHED")
            elif prompt.startswith("PLAN_"):
                if not results:
                    tool = ("read_file", {"path": "input.txt"}) if prompt == "PLAN_BUDGET" else ("write_file", {"path": "plan-must-not-write.txt", "content": "forbidden"})
                    self.frame("", tool)
                else:
                    result = json.loads(results[-1]["content"])
                    assert result["is_error"] and not (self.server.workspace / "plan-must-not-write.txt").exists(), result
                    self.frame("PLAN_FINISHED")
            elif prompt.startswith("WRITE_"):
                path = prompt + ".txt"
                if not results: self.frame("", ("write_file", {"path": path, "content": "after plan"}))
                else:
                    result = json.loads(results[-1]["content"])
                    assert not result["is_error"] and (self.server.workspace / path).read_text() == "after plan", result
                    self.frame("DONE_" + prompt)
            else: self.frame("ACK_" + prompt)
            self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass
        except BaseException: self.server.errors.append(traceback.format_exc())
        finally: self.close_connection = True


def worker(args):
    evidence = {"schema": 1, "result": "running", "scope": "Owned Windows console and isolated loopback host", "checks": [], "snapshots": {}, "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest()}
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests = []; server.errors = []; server.started = threading.Event(); server.release = threading.Event()
    hosts = []; process = None; credential_written = False
    identifier = "custom-plan-turn-" + uuid.uuid4().hex; target = "Sencode/connection/" + identifier
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]; advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]; advapi.CredDeleteW.restype = wintypes.BOOL
    threading.Thread(target=server.serve_forever, daemon=True).start()
    def record(name): evidence["checks"].append({"name": name, "status": "passed"})
    try:
        deadline = time.monotonic() + 10
        while not args.ready.exists(): assert time.monotonic() < deadline; time.sleep(.02)
        environment = environment_for(args.scratch); os.environ.clear(); os.environ.update(environment)
        workspace = args.scratch / "workspace-中文"; workspace.mkdir(); server.workspace = workspace
        (workspace / "input.txt").write_text("fixture input", encoding="utf-8")
        database = args.scratch / "catalog.sqlite3"
        def sql(statement, values=()):
            with closing(sqlite3.connect(database, timeout=10)) as db:
                db.create_function("sengoo_context", 1, lambda key: "plan-fixture" if key == "instance_id" else None)
                rows = db.execute(statement, values).fetchall(); db.commit(); return rows
        def run(*options, stdin="/exit\n"):
            result = subprocess.run([str(args.executable), "--cwd", str(workspace), "--database", str(database), "--connection", identifier, "--tui", "plain", *map(str, options)], input=stdin, cwd=workspace, env=environment, capture_output=True, encoding="utf-8", errors="replace", timeout=25)
            assert result.returncode == 0, (result.returncode, result.stdout, result.stderr); return result
        run("doctor")
        config = {"baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "chatCompletions", "enabledModels": [{"id": "fixture"}]}
        sql("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','plan loopback',?,'fixture',1,1)", (identifier, json.dumps(config)))
        blob = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key"); credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=blob, Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(credential), 0)); credential_written = True
        for case in ("success", "cancel", "failure", "budget", "preflight"):
            host = Host(args.executable, workspace, database, identifier); hosts.append(host)
            if case == "preflight":
                start = host.submit(case, "PLAN_SUCCESS", plan=True, connection="missing")
                result = host.wait("result", case, start); assert not result["success"], result
            else:
                prompt = {"success": "PLAN_SUCCESS", "cancel": "PLAN_SLOW", "failure": "PLAN_FAIL", "budget": "PLAN_BUDGET"}[case]
                server.started.clear(); server.release.clear()
                start = host.submit(case, prompt, plan=True, auto_edit=True, maximum_requests=1 if case == "budget" else 8)
                if case == "cancel":
                    host.wait("text_delta", case, start); host.send({"type": "cancel", "id": case})
                result = host.wait("result", case, start)
                assert result["success"] == (case == "success"), result
                if case == "cancel": assert result["code"] == 19, result
                server.release.set()
                plan = json.loads(sql("SELECT json_extract(mode_json,'$.plan') FROM shared_modes WHERE session_id=?", (host.session,))[0][0])
                assert not plan["active"] and plan["scope"] == "turn" and plan["read_only"], plan
            start = host.submit("follow-" + case, "WRITE_" + case.upper(), auto_edit=True)
            host.result("follow-" + case, start); host.stop(); record("host-" + case + "-clears-plan-before-next-submit")
        run("--permissions", "auto", stdin="/plan PLAN_SUCCESS\nWRITE_SCROLL\n/exit\n")
        assert (workspace / "WRITE_SCROLL.txt").exists(); record("plain-scrolling-plan-is-one-turn")
        run("--plan", "--permissions", "full", "-p", "PLAN_SUCCESS", "--output-format", "json")
        session = sql("SELECT id FROM sessions WHERE last_sent_at IS NOT NULL ORDER BY last_sent_at DESC LIMIT 1")[0][0]
        sql("UPDATE shared_modes SET mode_json=json_set(mode_json,'$.plan.active',json('true')) WHERE session_id=?", (session,))
        run("resume", session, stdin="WRITE_LEGACY\n/exit\n")
        assert (workspace / "WRITE_LEGACY.txt").exists(); record("legacy-plan-active-is-not-restored")
        console = Console(); prepare_owned_console(console); console.clear(); baseline = console.modes()
        def launch(*options):
            nonlocal process
            console.clear(); process = subprocess.Popen([str(args.executable), "--cwd", str(workspace), "--database", str(database), "--connection", identifier, "resume", session, *map(str, options)], cwd=workspace, env=environment)
            return wait(console, process, lambda s: "MESSAGE" in s["text"] and "完全权限" in s["text"], "ready")
        def outside(s): return "规划只读" not in s["text"] and "PLAN / read only" not in s["text"]
        def slash(text):
            command, _, argument = text.partition(" "); console.key(0x55, "\x15", 8); console.inject(command)
            wait(console, process, lambda s: "COMMANDS" in s["text"], "command menu"); console.key(0x0D, "\r")
            wait(console, process, lambda s: "Command completed" in s["text"] and "COMMANDS" not in s["text"], "completion")
            if argument: console.inject(argument)
            console.key(0x0D, "\r")
        def stop():
            nonlocal process
            console.key(0x44, "\x04", 8); process.wait(timeout=12)
            assert process.returncode == 0 and console.modes() == baseline; process = None
        launch()
        server.started.clear(); slash("/plan PLAN_SUCCESS"); assert server.started.wait(5)
        screen = wait(console, process, lambda s: "PLAN_FINISHED" in s["text"] and "NEXT MESSAGE" not in s["text"] and outside(s), "finished Plan footer")
        evidence["snapshots"]["completed"] = screen
        console.command("WRITE_TUI"); wait(console, process, lambda s: "DONE_WRITE_TUI" in s["text"] and outside(s), "ordinary follow-up")
        record("fullscreen-completion-restores-permission-and-tools")
        for name, vk, character, modifiers in (("escape", 0x1B, "\x1b", 0), ("control-c", 0x43, "\x03", 8)):
            server.started.clear(); server.release.clear(); slash("/plan PLAN_SLOW")
            wait(console, process, lambda s: "规划只读" in s["text"] and "NEXT MESSAGE" in s["text"], "active Plan")
            assert server.started.wait(5); console.key(vk, character, modifiers)
            wait(console, process, lambda s: "NEXT MESSAGE" not in s["text"] and outside(s), "cancel clears Plan")
            server.release.set(); record("fullscreen-" + name + "-clears-plan")
        server.started.clear(); slash("/plan PLAN_FAIL"); assert server.started.wait(5)
        wait(console, process, lambda s: "NEXT MESSAGE" not in s["text"] and outside(s), "failure clears Plan"); record("fullscreen-provider-failure-clears-plan")
        # Cancellation/failure deliberately pauses the pending queue. Reopen
        # the owned window to test automatic queue dispatch independently.
        stop(); launch()
        server.started.clear(); server.release.clear(); slash("/plan PLAN_QUEUE")
        wait(console, process, lambda s: "规划只读" in s["text"] and "NEXT MESSAGE" in s["text"], "queued Plan")
        assert server.started.wait(5); console.command("WRITE_QUEUE"); time.sleep(.15); server.release.set()
        wait(console, process, lambda s: "DONE_WRITE_QUEUE" in s["text"] and outside(s), "queued follow-up outside Plan")
        record("queued-follow-up-does-not-inherit-plan")
        server.started.clear(); server.release.clear(); slash("/plan PLAN_CRASH")
        assert server.started.wait(5)
        # The DB identifies the exact owned worker; never enumerate/stop other
        # user sessions. Its active execution must belong to this fixture session.
        rows = sql("SELECT owner_instance_id FROM shared_executions WHERE session_id=? AND active=1", (session,)); assert len(rows) == 1, rows
        instance = rows[0][0]
        assert instance.startswith("sg-"); owner_pid = int(instance.split("-")[1])
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]; kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]; kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = checked(kernel.OpenProcess(0x1001, False, owner_pid))
        try:
            ntdll = ctypes.WinDLL("ntdll"); query = ntdll.NtQueryInformationProcess
            query.argtypes = [wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG, ctypes.c_void_p]; query.restype = wintypes.LONG
            basic = (ctypes.c_size_t * 6)()
            assert query(handle, 0, ctypes.byref(basic), ctypes.sizeof(basic), None) == 0
            assert basic[4] == owner_pid and basic[5] == process.pid, "refuse to stop a worker outside the owned frontend"
            checked(kernel.TerminateProcess(handle, 88))
        finally: checked(kernel.CloseHandle(handle))
        screen = wait(console, process, lambda s: "Execution host stopped" in s["text"] and outside(s), "worker crash exits Plan")
        evidence["snapshots"]["crashed"] = screen; server.release.set(); record("worker-crash-clears-frontend-plan")
        stop(); launch(); screen = console.read(viewport=True); assert outside(screen)
        record("resume-after-crash-does-not-restore-plan"); stop()
        assert not server.errors, server.errors; evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"; evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None: evidence["last_screen"] = console.read(viewport=True)
    finally:
        server.release.set()
        if process is not None and process.poll() is None: process.terminate(); process.wait(timeout=5)
        for host in hosts: host.abort()
        if credential_written: checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown(); server.server_close(); evidence["provider_errors"] = server.errors; evidence["requests"] = server.requests
        evidence["fixture_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest(); write_json(args.evidence, evidence)
    return 0 if evidence["result"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("executable", type=Path); parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--worker", action="store_true"); parser.add_argument("--scratch", type=Path); parser.add_argument("--ready", type=Path)
    args = parser.parse_args(); args.executable = args.executable.resolve(strict=True); args.evidence = args.evidence.resolve()
    if args.worker: return worker(args)
    harness.__file__ = __file__; return harness.controller(args)


if __name__ == "__main__": raise SystemExit(main())
