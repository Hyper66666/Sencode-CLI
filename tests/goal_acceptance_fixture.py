"""Goal acceptance in real hosts and an owned Windows console, using loopback.

Only temporary projects, synthetic credentials and fixture-owned processes are
used. This is not live-model evidence or access to the user's project history.
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
from terminal_pane_console_fixture import resize_fullscreen
from tui_console_fixture import Console, checked, environment_for, write_json


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.server.requests.append(body)
            messages = body["messages"]
            start = max(i for i, m in enumerate(messages) if m["role"] == "user")
            prompt = messages[start]["content"]
            results = [m for m in messages[start + 1:] if m["role"] == "tool"]
            arguments = {"summary": "Verify the requested fixture result."}
            name = "finish_goal"
            text = ""
            if prompt in {"AUTO", "DIRECT", "UI_APPROVAL"}:
                if prompt == "AUTO" and not results:
                    pass  # Missing proposal must be recoverable, not a terminal pause.
                else:
                    arguments["checks"] = ["test -f artifact.txt"]
            elif prompt == "FIX":
                if not results:
                    arguments["checks"] = ["test -f fixed.txt"]
                elif len(results) == 1:
                    name = "run_command"
                    arguments = {"command": "printf fixed > fixed.txt", "shell": "bash"}
                # Third call verifies the pinned check, not a replacement.
            elif prompt in {"USER", "PINNED"}:
                arguments["checks"] = ["test -f pinned.txt"] if prompt == "PINNED" and not results else ["exit 0"]
            elif prompt in {"DENY", "APPROVE"}:
                arguments["checks"] = ["printf verified > " + prompt.lower() + ".txt"]
            elif prompt == "CANCEL":
                arguments["checks"] = ["printf started > cancel-started.txt; sleep 15; printf bad > cancel-must-not-write.txt"]
            elif prompt == "ORDINARY":
                if results:
                    name = ""
                    text = "ORDINARY_DONE"
                else:
                    arguments["checks"] = ["printf bad > ordinary-must-not-write.txt"]
            else:
                name = ""
                text = "ACK_" + prompt
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            delta = {"content": text}
            if name:
                delta = {"content": "Checking acceptance.", "tool_calls": [{"index": 0, "id": "goal-" + uuid.uuid4().hex,
                         "function": {"name": name, "arguments": json.dumps(arguments)}}]}
            event = {"choices": [{"delta": delta, "finish_reason": "tool_calls" if name else "stop"}]}
            self.wfile.write(("data: " + json.dumps(event) + "\n\ndata: [DONE]\n\n").encode())
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except BaseException:
            self.server.errors.append(traceback.format_exc())
        finally:
            self.close_connection = True


def worker(args):
    evidence = {"schema": 1, "scope": "isolated-loopback-real-host-and-owned-console", "result": "running",
                "checks": [], "snapshots": {}, "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest()}
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests = []; server.errors = []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    hosts = []; process = None; credential_written = False
    identifier = "custom-goal-acceptance-" + uuid.uuid4().hex
    target = "Sencode/connection/" + identifier
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
    advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi.CredDeleteW.restype = wintypes.BOOL

    def record(name):
        evidence["checks"].append({"name": name, "status": "passed"})

    try:
        deadline = time.monotonic() + 10
        while not args.ready.exists():
            assert time.monotonic() < deadline
            time.sleep(.02)
        environment = environment_for(args.scratch); os.environ.clear(); os.environ.update(environment)
        workspace = args.scratch / "project-中文"; workspace.mkdir()
        (workspace / "artifact.txt").write_text("verified fixture", encoding="utf-8")
        database = args.scratch / "catalog.sqlite"

        def sql(statement, values=()):
            with closing(sqlite3.connect(database, timeout=10)) as db:
                db.create_function("sengoo_context", 1, lambda key: "goal-fixture" if key == "instance_id" else None)
                rows = db.execute(statement, values).fetchall(); db.commit(); return rows

        def goal(session):
            return json.loads(sql("SELECT json_extract(mode_json,'$.goal') FROM shared_modes WHERE session_id=?", (session,))[0][0])

        def launch_host(session=""):
            host = Host(args.executable, workspace, database, identifier, session)
            hosts.append(host); return host

        bootstrap = launch_host(); bootstrap.stop()
        config = {"baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "chatCompletions", "enabledModels": [{"id": "fixture"}]}
        sql("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Goal loopback',?,'fixture',1,1)", (identifier, json.dumps(config)))
        blob = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
        credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=blob, Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(credential), 0)); credential_written = True

        for case in ("AUTO", "DIRECT", "FIX"):
            host = launch_host(); start = host.submit(case, case, goal=case, full_access=True)
            host.result(case, start); saved = goal(host.session)
            assert saved["status"] == 4 and saved["checks_source"] == "model" and saved["checks_shell"] == "bash", saved
            if case == "AUTO": assert saved["requests"] == 2, saved
            if case == "FIX": assert (workspace / "fixed.txt").exists() and saved["requests"] == 3, saved
            host.stop(); record("model-checks-" + case.lower())

        host = launch_host()
        start = host.submit("USER", "USER", goal="USER", checks=["if (!(Test-Path required.txt)) { exit 1 }"], full_access=True)
        result = host.result("USER", start, 12); saved = goal(host.session)
        assert result["diagnostic"]["reason"] == "goal_checks_failed" and "Goal paused" in result["content"], result
        assert saved["checks"] == ["if (!(Test-Path required.txt)) { exit 1 }"] and saved["checks_source"] == "user" and saved["status"] == 2, saved
        host.stop(); record("configured-checks-cannot-be-replaced-by-model-success")

        host = launch_host(); start = host.submit("PINNED", "PINNED", goal="PINNED", full_access=True)
        host.result("PINNED", start, 12); saved = goal(host.session)
        assert saved["status"] == 2 and saved["checks"] == ["test -f pinned.txt"] and saved["same_failure_count"] == 2, saved
        session = host.session; before = saved["requests"]; host.stop()
        (workspace / "pinned.txt").write_text("repaired", encoding="utf-8")
        host = launch_host(session); start = host.submit("RESUME", "PINNED", goal="PINNED", full_access=True)
        host.result("RESUME", start); saved = goal(session)
        assert saved["status"] == 4 and saved["requests"] > before and saved["checks_source"] == "model" and saved["checks_shell"] == "bash" and saved["checks"] == ["test -f pinned.txt"], saved
        host.stop(); record("failed-model-checks-pinned-across-repair-restart-and-budget-resume")

        for case, approved in (("DENY", False), ("APPROVE", True)):
            host = launch_host(); start = host.submit(case, case, goal=case)
            approval = host.wait("approval", case, start)
            assert "printf verified > " + case.lower() + ".txt" in approval["text"] and "bash" in approval["text"], approval
            assert not (workspace / (case.lower() + ".txt")).exists()
            host.send({"type": "approval", "id": approval["id"], "request_id": case, "approved": approved})
            result = host.result(case, start, 0 if approved else 12)
            assert (workspace / (case.lower() + ".txt")).exists() == approved
            if not approved:
                assert result["diagnostic"]["reason"] == "goal_permission_required" and "Tool execution failed" not in result["content"]
                assert goal(host.session)["last_failure"] == "Acceptance commands require permission"
            host.stop(); record("exact-model-command-approval-" + case.lower())

        host = launch_host(); start = host.submit("CANCEL", "CANCEL", goal="CANCEL", full_access=True)
        deadline = time.monotonic() + 8
        while not (workspace / "cancel-started.txt").exists(): assert time.monotonic() < deadline; time.sleep(.02)
        host.send({"type": "cancel", "id": "CANCEL"}); host.result("CANCEL", start, 19)
        assert not (workspace / "cancel-must-not-write.txt").exists() and goal(host.session)["status"] == 2
        host.stop(); record("cancel-acceptance-command-is-cancelled-and-cleaned-up")

        host = launch_host(); start = host.submit("ORDINARY", "ORDINARY", full_access=True)
        host.result("ORDINARY", start)
        assert not (workspace / "ordinary-must-not-write.txt").exists()
        host.stop(); record("finish-goal-outside-goal-cannot-run-acceptance")

        console = Console(); prepare_owned_console(console); console.clear(); baseline = console.modes()
        process = subprocess.Popen([str(args.executable), "--cwd", str(workspace), "--database", str(database), "--connection", identifier, "--permissions", "full"], cwd=workspace, env=environment)
        wait(console, process, lambda s: "MESSAGE" in s["text"] and "完全权限" in s["text"], "CLI ready")
        for columns in (80, 120, 160):
            resize_fullscreen(console, columns, 40)
            screen = wait(console, process, lambda s: len(s["rows"]) == 40 and "MESSAGE" in s["text"], "resized footer")
            footer = "\n".join(r["text"] for r in screen["rows"][-2:])
            assert "完全权限" in footer and "/help" in footer and "Enter send" not in footer and "Ready /" not in footer, footer
            evidence["snapshots"][f"footer-{columns}"] = screen
        record("compact-real-console-footer-80-120-160")
        resize_fullscreen(console, 120, 60)
        console.inject("/goal"); wait(console, process, lambda s: "COMMANDS" in s["text"], "Goal completion menu")
        console.key(0x0D, "\r"); wait(console, process, lambda s: "Command completed" in s["text"] and "COMMANDS" not in s["text"], "complete only")
        console.inject("DIRECT"); console.key(0x0D, "\r")
        screen = wait(console, process, lambda s: "Worked for" in s["text"] and "NEXT MESSAGE" not in s["text"], "Goal completed without --check")
        assert "Tool execution failed" not in screen["text"] and "configure acceptance commands" not in screen["text"] and "Paused / cancelled" not in screen["text"]
        evidence["snapshots"]["goal-completed"] = screen; record("slash-goal-without-check-completes-from-model-conditions")
        console.key(0x44, "\x04", 8); assert process.wait(timeout=12) == 0
        assert console.modes() == baseline; process = None
        assert not server.errors, server.errors
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"; evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None: evidence["last_screen"] = console.read(viewport=True)
    finally:
        if process is not None and process.poll() is None: process.terminate(); process.wait(timeout=5)
        for host in hosts: host.abort()
        if credential_written: checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown(); server.server_close()
        evidence["provider_errors"] = server.errors; evidence["request_count"] = len(server.requests)
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
