"""Real native CLI, owned Windows console and loopback tool-loop acceptance.

Never reads user configuration or credentials. A random fixture credential is
created and removed, and all project files live in an inventoried TEMP tree.
This is synthetic-provider evidence, not live-provider or release validation.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import http.server
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid

from cli_fixture import Credential
from engine_fixture import Host
from fullscreen_console_fixture import wait
from tui_console_fixture import (
    Console, JobExtendedLimits, checked, environment_for, kernel_api,
    remove_owned_tree, write_json,
)


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def event(self, content=None, tool=None, done=False):
        delta = {}
        if content is not None:
            delta["content"] = content
        if tool:
            identifier, name, arguments = tool
            delta["tool_calls"] = [{"index": 0, "id": identifier,
                                    "function": {"name": name, "arguments": json.dumps(arguments)}}]
        event = {"choices": [{"delta": delta, "finish_reason": "tool_calls" if tool else ("stop" if done else None)}]}
        if done or tool:
            event["usage"] = {"prompt_tokens": 12, "completion_tokens": 8}
        self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
        self.wfile.flush()

    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            history = request["messages"]
            latest = max(i for i, value in enumerate(history) if value["role"] == "user")
            prompt = history[latest]["content"]
            results = [value for value in history[latest + 1:] if value["role"] == "tool"]
            self.server.requests.append(request)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            tool = None
            if prompt == "timeline fixture":
                if not results:
                    self.event("TRACE_BEFORE\n")
                    time.sleep(.35)
                    tool = ("timeline-tool", "run_command", {"command": "printf 'CARD_TEST\\n'; sleep 1.3", "shell": "bash", "timeout_ms": 10000})
                else:
                    assert not json.loads(results[-1]["content"])["is_error"], results
                    time.sleep(.35)
                    self.event("TRACE_AFTER\n", done=True)
            elif prompt in {"recover fixture", "recover terminal fixture"}:
                if not results:
                    self.event("RECOVERY_BEFORE\n")
                    tool = ("recover-rejected", "list_directory", {"path": str(self.server.outside)})
                elif len(results) == 1:
                    rejected = json.loads(results[-1]["content"])
                    assert rejected["is_error"], rejected
                    # A duplicate completed identity must reuse its first result,
                    # even if a model incorrectly supplies different arguments.
                    tool = ("recover-rejected", "list_directory", {"path": "."})
                elif len(results) == 2:
                    assert results[-1]["tool_call_id"] == "recover-rejected", results
                    assert json.loads(results[-1]["content"])["is_error"], results
                    tool = ("recover-corrected", "list_directory", {"path": "."})
                else:
                    assert len(results) == 3 and not json.loads(results[-1]["content"])["is_error"], results
                    self.event("RECOVERY_FIXED\n", done=True)
            elif prompt == "coding fixture":
                stages = [
                    ("workflow-read", "read_file", {"path": "calc.txt"}),
                    ("workflow-patch", "apply_patch", {"path": "calc.txt", "old": "VALUE=1", "new": "VALUE=2"}),
                    ("workflow-test", "run_command", {"command": "test \"$(cat calc.txt)\" = 'VALUE=2' && printf 'TESTS_OK\\n'", "shell": "bash", "timeout_ms": 10000}),
                ]
                if results:
                    value = json.loads(results[-1]["content"])
                    assert not value["is_error"], value
                    if len(results) == 1:
                        assert "VALUE=1" in value["content"], value
                    if len(results) == 3:
                        command = json.loads(value["content"])
                        assert command["exit_code"] == 0 and "TESTS_OK" in command["stdout"], command
                if len(results) < len(stages):
                    self.event("CODING_STEP_" + str(len(results)) + "\n")
                    tool = stages[len(results)]
                else:
                    self.event("CODING_VERIFIED\n", done=True)
            elif prompt == "continue fixture":
                assert any(value.get("role") == "tool" and value.get("tool_call_id") == "workflow-test" for value in history), history
                self.event("CONTEXT_CONTINUED\n", done=True)
            else:
                raise AssertionError(("unexpected prompt", prompt))
            if tool:
                self.event(tool=tool)
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except BaseException:
            self.server.errors.append(traceback.format_exc())
        finally:
            self.close_connection = True


def ledger(database, session):
    with sqlite3.connect(database) as connection:
        return [dict(zip(("call_id", "name", "state", "arguments_json"), row)) for row in
                connection.execute("SELECT call_id,name,state,arguments FROM shared_tool_ledger WHERE session_id=? ORDER BY call_id", (session,))]


def worker(args):
    evidence = {"schema": 1, "result": "running", "host": os.environ.get("COMPUTERNAME"),
                "binary": str(args.executable), "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                "fixture_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "scope": "Owned native Windows console; real tool execution; synthetic loopback Chat Completions provider; no live API", "checks": [], "snapshots": {}}
    process = None
    hosts = []
    credential_written = False
    target = "Sencode/connection/agent-reliability-" + uuid.uuid4().hex
    identifier = target.rsplit("/", 1)[1]
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
    advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi.CredDeleteW.restype = wintypes.BOOL
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests, server.errors = [], []
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def check(name, callback):
        try:
            callback()
            evidence["checks"].append({"name": name, "status": "passed"})
        except BaseException:
            evidence["checks"].append({"name": name, "status": "failed", "error": traceback.format_exc()})

    def assert_that(value, detail):
        assert value, detail

    try:
        deadline = time.monotonic() + 8
        while not args.ready.exists():
            assert time.monotonic() < deadline, "Owned Job was not established"
            time.sleep(.02)
        environment = environment_for(args.scratch)
        # All subprocesses, including imported Host, inherit only this isolated
        # profile. The parent process and user environment are unaffected.
        os.environ.clear()
        os.environ.update(environment)
        workspace = args.scratch / "workspace-中文"
        workspace.mkdir()
        (workspace / "calc.txt").write_text("VALUE=1\n", encoding="utf-8")
        server.outside = args.scratch / "outside"
        server.outside.mkdir()
        database = args.scratch / "isolated.sqlite"
        common = ["--cwd", str(workspace), "--database", str(database), "--connection", identifier]
        initial = subprocess.run([str(args.executable), *common, "doctor"], capture_output=True, timeout=25)
        assert initial.returncode == 0, initial.stderr.decode(errors="replace")
        secret = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
        credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=secret, Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(credential), 0))
        credential_written = True
        config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "chatCompletions",
                  "successfulProtocol": "chatCompletions", "selectedModelId": "fixture", "credentialRef": target, "enabledModels": []}
        with sqlite3.connect(database) as connection:
            connection.create_function("sengoo_context", 1, lambda key: "agent-reliability" if key == "instance_id" else None)
            connection.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','reliability loopback',?,'fixture',1,1)", (identifier, json.dumps(config)))
            connection.commit()

        def recovery():
            host = Host(args.executable, workspace, database, identifier)
            hosts.append(host)
            start = host.submit("recovery-turn", "recover fixture")
            result = host.wait("result", "recovery-turn", start, timeout=25)
            evidence["recovery_result"] = result
            evidence["recovery_events"] = host.events[start:]
            assert result["success"] and "RECOVERY_FIXED" in result["content"], result
            rows = ledger(database, host.session)
            evidence["recovery_ledger"] = rows
            assert len(rows) == 2 and all(row["state"] == "complete" for row in rows), rows
            rejected = next(row for row in rows if row["call_id"] == "recover-rejected")
            assert json.loads(rejected["arguments_json"])["path"] == str(server.outside), rejected
            tools = [json.loads(event["text"]) for event in host.events[start:] if event["type"] == "tool"]
            assert len(tools) == 4, tools  # running/final for two actual operations
            host.stop()
        check("read-only-error-model-correction-and-completed-call-dedup", recovery)
        for host in hosts:
            if host.process.poll() is None:
                host.abort()

        console = Console()
        console.resize(120, 42)
        console.clear()
        baseline = console.modes()
        process = subprocess.Popen([str(args.executable), *common, "--auto-edit", "--allow-commands"], cwd=workspace)
        wait(console, process, lambda screen: "MESSAGE" in screen["text"], "native TUI homepage", timeout=20)

        def submit(prompt):
            console.inject(prompt)
            wait(console, process, lambda screen: prompt in screen["text"], "visible composer")
            console.key(0x0D, "\r")

        submit("timeline fixture")
        before = wait(console, process, lambda screen: "TRACE_BEFORE" in screen["text"], "real text before tool")
        evidence["snapshots"]["stream-before-tool"] = before
        running = wait(console, process, lambda screen: "run_command" in screen["text"] and "running" in screen["text"].lower(), "one live running tool card")
        evidence["snapshots"]["tool-running"] = running
        final = wait(console, process, lambda screen: "TRACE_AFTER" in screen["text"] and "NEXT MESSAGE" not in screen["text"], "timeline completion", timeout=20)
        evidence["snapshots"]["timeline"] = final
        check("text-tool-text-chronological-screen-order", lambda: assert_that(final["text"].index("TRACE_BEFORE") < final["text"].index("run_command") < final["text"].index("TRACE_AFTER"), final["text"]))
        check("tool-running-completed-update-one-card", lambda: assert_that(final["text"].count("run_command") == 1 and "running" not in final["text"].lower() and running["text"].count("run_command") == 1, final["text"]))

        def resume_timeline():
            nonlocal process
            with sqlite3.connect(database) as connection:
                session = connection.execute("SELECT session_id FROM shared_tool_ledger WHERE call_id='timeline-tool'").fetchone()[0]
            console.key(0x44, "\x04", 8)
            process.wait(timeout=12)
            assert process.returncode == 0 and console.modes() == baseline
            console.clear()
            process = subprocess.Popen([str(args.executable), *common, "--auto-edit", "--allow-commands", "resume", session], cwd=workspace)
            screen = wait(console, process, lambda value: "TRACE_AFTER" in value["text"] and "MESSAGE" in value["text"], "persisted chronological tool card replay", timeout=15)
            evidence["snapshots"]["resumed-timeline"] = screen
            text = screen["text"]
            assert text.count("run_command") == 1 and text.index("TRACE_BEFORE") < text.index("run_command") < text.index("TRACE_AFTER"), text
        check("resume-reconstructs-order-and-one-tool-card-without-reexecution", resume_timeline)

        def terminal_recovery():
            submit("recover terminal fixture")
            screen = wait(console, process, lambda value: "RECOVERY_FIXED" in value["text"] and "NEXT MESSAGE" not in value["text"], "recoverable read failure continues in the native TUI", timeout=15)
            evidence["snapshots"]["read-error-corrected"] = screen
        check("native-terminal-read-error-correction", terminal_recovery)

        def coding():
            submit("coding fixture")
            screen = wait(console, process, lambda value: "CODING_VERIFIED" in value["text"] and "NEXT MESSAGE" not in value["text"], "read patch Bash test completion", timeout=30)
            evidence["snapshots"]["coding"] = screen
            assert (workspace / "calc.txt").read_text(encoding="utf-8") == "VALUE=2\n"
            submit("continue fixture")
            screen = wait(console, process, lambda value: "CONTEXT_CONTINUED" in value["text"] and "NEXT MESSAGE" not in value["text"], "next user turn retains tool history", timeout=20)
            evidence["snapshots"]["continued"] = screen
        check("real-read-patch-bash-test-and-next-conversation-turn", coding)
        assert not server.errors, server.errors
        console.key(0x44, "\x04", 8)
        process.wait(timeout=12)
        assert process.returncode == 0, process.returncode
        check("native-terminal-restoration", lambda: assert_that(console.modes() == baseline, (baseline, console.modes())))
        evidence["result"] = "passed" if all(value["status"] == "passed" for value in evidence["checks"]) else "failed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None:
            try:
                evidence["last_screen"] = console.read(viewport=True)
            except BaseException:
                pass
    finally:
        for host in hosts:
            host.abort()
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        if credential_written:
            checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown()
        server.server_close()
        evidence["provider_errors"] = server.errors
        evidence["provider_requests"] = server.requests
        write_json(args.evidence, evidence)
    return 0 if evidence["result"] == "passed" else 1


def controller(args):
    kernel = kernel_api()
    scratch = Path(tempfile.mkdtemp(prefix="sencode-agent-reliability-"))
    ready = scratch / "ready"
    job = checked(kernel.CreateJobObjectW(None, None))
    process = None
    try:
        limits = JobExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000
        checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), str(args.executable), "--worker", "--scratch", str(scratch), "--ready", str(ready), "--evidence", str(args.evidence)], startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE)
        checked(kernel.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)))
        ready.write_text("assigned", encoding="ascii")
        code = process.wait(timeout=150)
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        print(json.dumps({"result": evidence["result"], "checks": [{"name": value["name"], "status": value["status"]} for value in evidence["checks"]], "evidence": str(args.evidence)}, indent=2))
        return code
    finally:
        checked(kernel.CloseHandle(job))
        if process is not None:
            process.wait(timeout=5)
        remove_owned_tree(scratch)


def main():
    if os.name != "nt":
        raise SystemExit("This acceptance fixture requires a real Windows console")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[1] / "target/agent-reliability/evidence.json")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    args.executable = args.executable.resolve(strict=True)
    args.evidence = args.evidence.resolve()
    return worker(args) if args.worker else controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
