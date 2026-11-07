"""Exercise the Sengoo JSONL execution host with real pipes, tools and SQLite.

Only the model endpoint is a loopback fixture. The executable owns all parsing,
streaming, permissions, process cancellation, fencing and durable admission.
"""
from contextlib import closing
import ctypes
import http.server
import json
import os
from pathlib import Path
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from cli_fixture import Credential


COMPACTION_MARKER = "ENGINE-COMPACTION-SYNTHETIC"
COMPACTION_SUMMARY = (
    "1. Goal: validate this isolated native execution host while preserving explicit workspace and permission constraints.\n"
    "2. Decisions: capture connection and model per request; keep Plan children read only and require nonce-bound approvals.\n"
    "3. Files: approved.txt and agent-child.txt contain synthetic fixture evidence; denied and Plan-forbidden paths must remain absent.\n"
    "4. Results: retain the exact recent tool responses and the public history of cancellation, handoff and replay checks.\n"
    "5. Open work: compaction and consult checks precede disconnect, shutdown and durable restart validation.\n"
    "6. Safety: do not replay uncertain command or MCP outcomes and do not reset cumulative request budgets.\n"
    "7. Attribution: the loopback provider is synthetic; it does not establish live-provider or installation compatibility. "
    + COMPACTION_MARKER
)


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    lock = threading.Lock()
    requests = []
    errors = []

    def log_message(self, *_):
        pass

    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = request["messages"]
            last_user = max(i for i, value in enumerate(messages) if value["role"] == "user")
            prompt = messages[last_user]["content"]
            summary_request = messages[0]["content"].startswith("You summarize coding sessions")
            tool_results = [message for message in messages[last_user + 1:] if message["role"] == "tool"]
            with self.lock:
                self.requests.append(request)
                sequence = len(self.requests)
            tool = None
            if prompt == "permission deny" and not tool_results:
                tool = ("write_file", {"path": "denied.txt", "content": "must not exist"})
            elif prompt == "permission allow" and not tool_results:
                tool = ("write_file", {"path": "approved.txt", "content": "approved 中文😀"})
            elif prompt == "cancel command" and not tool_results:
                tool = ("run_command", {"command": "sleep 30", "timeout_ms": 60000})
            elif prompt == "cancel mcp" and not tool_results:
                tool = ("mcp__call", {"server": "fixture", "tool": "slow", "arguments": {}})
            elif prompt == "plan guards":
                attempts = [("write_file", {"path": "plan-forbidden.txt", "content": "forbidden"}),
                            ("run_command", {"command": "Set-Content -LiteralPath shell-forbidden.txt forbidden"}),
                            ("mcp__call", {"server": "fixture", "tool": "slow", "arguments": {}}),
                            ("write_plan", {"content": "Inspect, design, and request approval."})]
                if len(tool_results) < len(attempts):
                    tool = attempts[len(tool_results)]
            elif prompt == "finish goal" and not tool_results:
                tool = ("finish_goal", {"summary": "Run the user-defined acceptance command."})
            elif prompt in ("agents host", "agents cancel", "plan children"):
                if not tool_results:
                    child_prompt = {"agents host": "child write", "agents cancel": "slow cancel", "plan children": "child forbidden"}[prompt]
                    tool = ("spawn_agent", {"role": "general", "prompt": child_prompt,
                            "connection_id": self.server.child_connection, "model": "child-model"})
                elif len(tool_results) == 1 or not all(child["done"] for child in json.loads(tool_results[-1]["content"])["children"]):
                    tool = ("wait_agents", {"timeout_ms": 1000})
            elif prompt in ("child write", "child forbidden") and not tool_results:
                tool = ("write_file", {"path": "agent-child.txt" if prompt == "child write" else "child-forbidden.txt", "content": "child evidence 中文😀"})
            if summary_request:
                assert "PUBLIC_HISTORY_JSON:" in prompt and not request.get("tools")
                events = [{"choices": [{"delta": {"content": COMPACTION_SUMMARY}, "finish_reason": "stop"}],
                           "usage": {"prompt_tokens": 11, "completion_tokens": 7}}]
            elif tool:
                name, arguments = tool
                events = [{"choices": [{"delta": {"tool_calls": [{"index": 0, "id": f"call-{sequence}",
                           "function": {"name": name, "arguments": json.dumps(arguments)}}]}, "finish_reason": "tool_calls"}],
                           "usage": {"prompt_tokens": 11, "completion_tokens": 7}}]
            else:
                events = [{"choices": [{"delta": {"content": "reply 中文"}, "finish_reason": None}]},
                          {"choices": [{"delta": {"content": "😀 " + prompt[:40]}, "finish_reason": "stop"}],
                           "usage": {"prompt_tokens": 11, "completion_tokens": 7}}]
            encoded = [("data: " + json.dumps(value, ensure_ascii=False) + "\n\n").encode("utf-8") for value in events]
            encoded.append(b"data: [DONE]\n\n")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(sum(map(len, encoded))))
            self.send_header("Connection", "close")
            self.end_headers()
            for index, frame in enumerate(encoded):
                if index == 1 and not tool:
                    time.sleep(3 if prompt.startswith("slow ") else .15)
                for offset in range(0, len(frame), 5):
                    self.wfile.write(frame[offset:offset + 5])
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as error:
            with self.lock:
                self.errors.append(repr(error))
            raise
        finally:
            self.close_connection = True


class Host:
    def __init__(self, executable, project, database, connection, session=""):
        arguments = [str(executable), "--engine-stdio", "--cwd", str(project), "--database", str(database),
                     "--connection", connection]
        if session:
            arguments += ["resume", session]
        self.process = subprocess.Popen(arguments, cwd=project, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
        self.incoming = queue.Queue()
        self.events = []
        self.errors = []

        def output_reader():
            for line in self.process.stdout:
                try:
                    value = json.loads(line)
                    assert isinstance(value, dict), line
                    self.incoming.put(value)
                except Exception as error:
                    self.incoming.put({"type": "invalid-output", "text": line, "error": str(error)})
            self.incoming.put({"type": "host-eof"})

        def error_reader():
            for line in self.process.stderr:
                self.errors.append(line)

        threading.Thread(target=output_reader, daemon=True).start()
        threading.Thread(target=error_reader, daemon=True).start()
        ready = self.wait("ready")
        self.session = ready["session_id"]

    def send(self, value):
        self.process.stdin.write(json.dumps(value, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def submit(self, identifier, text, **options):
        start = len(self.events)
        self.send(dict(type="submit", id=identifier, text=text, **options))
        return start

    def wait(self, kind, identifier=None, start=0, timeout=15):
        deadline = time.monotonic() + timeout
        scan = start
        while True:
            while scan < len(self.events):
                event = self.events[scan]
                scan += 1
                if event.get("type") == kind and (identifier is None or event.get("request_id", event.get("id")) == identifier):
                    return event
                assert event.get("type") not in ("invalid-output", "host-eof"), (event, self.errors, self.events[-6:])
            remaining = deadline - time.monotonic()
            assert remaining > 0, ("host timeout", kind, identifier, self.process.poll(), self.errors, self.events[-6:])
            try:
                self.events.append(self.incoming.get(timeout=remaining))
            except queue.Empty:
                raise AssertionError(("host timeout", kind, identifier, self.process.poll(), self.errors, self.events[-6:]))

    def result(self, identifier, start, code=0):
        result = self.wait("result", identifier, start)
        assert result["code"] == code and result["success"] == (code == 0), result
        return result

    def stop(self):
        if self.process.poll() is None:
            self.send({"type": "shutdown"})
            self.process.wait(timeout=10)
        assert self.process.returncode == 0, (self.process.returncode, self.errors)
        self.process.stdin.close()

    def abort(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)
        for pipe in (self.process.stdin, self.process.stdout, self.process.stderr):
            if pipe:
                pipe.close()


def mcp_server(pid_file):
    Path(pid_file).write_text(str(os.getpid()), encoding="ascii")
    for line in sys.stdin:
        value = json.loads(line)
        method = value.get("method")
        if "id" not in value:
            continue
        if method == "initialize":
            result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                      "serverInfo": {"name": "host-fixture", "version": "1"}}
        elif method == "tools/list":
            result = {"tools": [{"name": "slow", "inputSchema": {"type": "object", "properties": {}}}]}
        elif method == "tools/call":
            sys.stderr.write("slow fixture invoked\n")
            sys.stderr.flush()
            time.sleep(30)
            result = {"content": [{"type": "text", "text": "slow response"}]}
        else:
            result = {}
        print(json.dumps({"jsonrpc": "2.0", "id": value["id"], "result": result}), flush=True)


def clean_generated_directory(project):
    # Only enumerated fixture-owned paths are removed, files before empty dirs.
    for path in sorted(project.rglob("*"), key=lambda value: len(value.parts), reverse=True):
        if path.is_dir():
            path.rmdir()
        else:
            path.unlink()
    project.rmdir()


def main():
    executable = Path(sys.argv[1]).resolve()
    project = Path(tempfile.mkdtemp(prefix="sencode-engine-中文😀-")).resolve()
    database = project / "fixture.sqlite"
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    identifier = "custom-engine-fixture-" + uuid.uuid4().hex
    target = "Sencode/connection/" + identifier
    second_identifier = identifier + "-other"
    second_target = "Sencode/connection/" + second_identifier
    server.child_connection = second_identifier
    key = (ctypes.c_ubyte * len(b"fixture-key")).from_buffer_copy(b"fixture-key")
    credential = Credential(Type=1, TargetName=target, CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    assert advapi.CredWriteW(ctypes.byref(credential), 0), ctypes.WinError(ctypes.get_last_error())
    second_credential = Credential(Type=1, TargetName=second_target, CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
    assert advapi.CredWriteW(ctypes.byref(second_credential), 0), ctypes.WinError(ctypes.get_last_error())
    hosts = []
    succeeded = False
    try:
        # First startup creates the isolated schema; a host with no selected
        # connection can remain idle while the fixture config is installed.
        bootstrap = Host(executable, project, database, "")
        hosts.append(bootstrap)
        bootstrap.stop()
        config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                  "protocol": "chatCompletions", "successfulProtocol": "chatCompletions",
                  "selectedModelId": "model-one", "credentialRef": target,
                  "enabledModels": [{"id": name} for name in ("model-one", "model-two", "child-model")]}
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "test-fixture" if key == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','fixture',?,'model-one',1,1)",
                       (identifier, json.dumps(config)))
            config["credentialRef"] = second_target
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','other fixture',?,'model-one',1,1)",
                       (second_identifier, json.dumps(config)))
            db.commit()
        settings = project / ".sencode"
        settings.mkdir(exist_ok=True)
        (settings / "mcp.json").write_text(json.dumps({"servers": [{"name": "fixture", "command": sys.executable,
                    "args": [str(Path(__file__).resolve()), "--mcp-fixture", str(project / "mcp.pid")]}]}), encoding="utf-8")
        host = Host(executable, project, database, identifier)
        hosts.append(host)

        start = host.submit("stream-one", "stream one", model="model-one")
        first_delta = host.wait("text_delta", "stream-one", start)
        assert first_delta["text"] == "reply 中文", first_delta
        queued = host.submit("stream-two", "stream two", connection=second_identifier, model="model-two")
        first = host.result("stream-one", start)
        second = host.result("stream-two", queued)
        assert first["session_id"] == second["session_id"] == host.session
        assert first["model"] == "model-one" and second["model"] == "model-two"
        assert first["connection_id"] == identifier and second["connection_id"] == second_identifier
        assert "😀" in first["content"]
        assert all(event["model"] == "model-one" for event in host.events[start:]
                   if event.get("request_id") == "stream-one" and event.get("type") in ("text_delta", "request_started"))
        count = len(Provider.requests)
        duplicate = host.submit("stream-one", "must not execute twice")
        host.result("stream-one", duplicate, 12)
        assert len(Provider.requests) == count

        live = host.submit("owned", "slow ownership", connection=identifier)
        host.wait("text_delta", "owned", live)
        contender = Host(executable, project, database, second_identifier, host.session)
        hosts.append(contender)
        busy = contender.submit("contender", "cannot take over a live session")
        rejected = contender.wait("result", "contender", busy)
        assert not rejected["success"] and rejected["code"] != 0
        host.result("owned", live)
        idle = contender.submit("contender", "idle handoff can execute")
        contender.result("contender", idle)
        contender.stop()

        denied = host.submit("deny", "permission deny", auto_edit=False, allow_commands=False)
        approval = host.wait("approval", "deny", denied)
        yes_queued = host.submit("queued-yes", "yes")
        host.send({"type": "approval", "id": "old-nonce", "approved": True})
        host.wait("notice", start=denied)
        time.sleep(.1)
        assert not (project / "denied.txt").exists()
        host.send({"type": "approval", "id": approval["id"], "request_id": "deny", "approved": False})
        host.result("deny", denied, 12)
        host.result("queued-yes", yes_queued)
        assert not (project / "denied.txt").exists()

        allowed = host.submit("allow", "permission allow", auto_edit=False)
        approval = host.wait("approval", "allow", allowed)
        host.send({"type": "approval", "id": approval["id"], "request_id": "allow", "approved": True})
        host.result("allow", allowed)
        assert (project / "approved.txt").read_text(encoding="utf-8") == "approved 中文😀"

        slow = host.submit("slow", "slow cancel")
        host.wait("text_delta", "slow", slow)
        cancelled_at = time.monotonic()
        host.send({"type": "cancel", "id": "slow"})
        host.result("slow", slow, 19)
        assert time.monotonic() - cancelled_at < 2, "provider cancellation waited for the complete response"

        command = host.submit("command", "cancel command", allow_commands=False)
        approval = host.wait("approval", "command", command)
        host.send({"type": "approval", "id": approval["id"], "approved": True})
        time.sleep(.4)
        cancelled_at = time.monotonic()
        host.send({"type": "cancel", "id": "command"})
        host.result("command", command, 19)
        assert time.monotonic() - cancelled_at < 5

        mcp = host.submit("mcp", "cancel mcp")
        approval = host.wait("approval", "mcp", mcp)
        host.send({"type": "approval", "id": approval["id"], "approved": True})
        deadline = time.monotonic() + 5
        while not (project / "mcp.pid").exists() and time.monotonic() < deadline:
            time.sleep(.02)
        assert (project / "mcp.pid").exists(), "approved MCP process did not start"
        time.sleep(.1)
        host.send({"type": "cancel", "id": "mcp"})
        host.result("mcp", mcp, 19)
        with closing(sqlite3.connect(database)) as db:
            assert not db.execute("SELECT 1 FROM shared_tool_ledger WHERE state='running'").fetchone(), "cancel left an uncertified tool claim"
            assert not db.execute("SELECT 1 FROM shared_executions WHERE active=1").fetchone(), "cancel retained session execution"

        plan = host.submit("plan", "plan guards", plan=True, auto_edit=True, allow_commands=True)
        host.result("plan", plan)
        assert not (project / "plan-forbidden.txt").exists() and not (project / "shell-forbidden.txt").exists()
        assert list((settings / "plans").glob("*.md"))
        assert not any(event.get("type") == "approval" and event.get("request_id") == "plan" for event in host.events[plan:])

        agents = host.submit("agents", "agents host", connection=identifier, plan=False, auto_edit=True)
        host.result("agents", agents)
        assert (project / "agent-child.txt").read_text(encoding="utf-8") == "child evidence 中文😀"
        child_events = [json.loads(event["text"])["agent"] for event in host.events[agents:]
                        if event.get("type") == "agent" and event.get("request_id") == "agents"]
        assert any(event["kind"] == "finished" for event in child_events)
        assert all(event["connection_id"] == second_identifier and event["model"] == "child-model" for event in child_events)

        planned_agents = host.submit("planned-agents", "plan children", plan=True, auto_edit=True)
        host.result("planned-agents", planned_agents)
        assert not (project / "child-forbidden.txt").exists(), "a child bypassed inherited Plan"

        child_cancel = host.submit("child-cancel", "agents cancel", plan=False)
        host.wait("agent", "child-cancel", child_cancel)
        host.send({"type": "cancel", "id": "child-cancel"})
        host.result("child-cancel", child_cancel, 19)
        with closing(sqlite3.connect(database)) as db:
            assert not db.execute("SELECT 1 FROM shared_executions WHERE active=1").fetchone(), "parent cancellation retained child execution"

        bad = host.submit("bad", "invalid", maximum_requests="50")
        host.result("bad", bad, 2)
        bad = host.submit("bad-policy", "invalid", token_budget=100)
        host.result("bad-policy", bad, 7)

        goal = host.submit("goal", "finish goal", plan=False, goal="finish goal", checks=["exit 0"], allow_commands=True)
        host.result("goal", goal)
        ordinary = host.submit("ordinary", "ordinary followup")
        host.result("ordinary", ordinary)
        system = next(value["content"] for value in Provider.requests[-1]["messages"] if value["role"] == "system")
        assert "GOAL MODE" not in system, "ordinary followup silently resumed the old goal"

        compact = host.submit("compact", "compact", operation="compact")
        compact_result = host.result("compact", compact)
        assert COMPACTION_MARKER not in compact_result["content"], "manual compact exposed internal summary as a public answer"
        assert not any(COMPACTION_MARKER in event.get("text", "") for event in host.events[compact:]
                       if event.get("type") == "text_delta"), "internal summary streamed publicly"
        with closing(sqlite3.connect(database)) as db:
            row = db.execute("SELECT mode_json FROM shared_modes WHERE session_id=?", (host.session,)).fetchone()
            assert COMPACTION_MARKER in json.loads(row[0])["context"]["summary"]
            assert not any(COMPACTION_MARKER in row[0] for row in db.execute("SELECT text FROM messages WHERE session_id=?", (host.session,)))
        consult = host.submit("consult", "consult fixture", operation="consult")
        report = host.result("consult", consult)
        assert "summary" in json.loads(report["content"])

        disconnected = Host(executable, project, database, identifier)
        hosts.append(disconnected)
        disconnected_start = disconnected.submit("disconnected", "slow cancel")
        disconnected.wait("text_delta", "disconnected", disconnected_start)
        disconnected.process.stdin.close()
        disconnected.result("disconnected", disconnected_start, 19)
        assert disconnected.process.wait(timeout=5) == 0

        shutting_down = Host(executable, project, database, identifier)
        hosts.append(shutting_down)
        shutdown_start = shutting_down.submit("shutdown", "slow cancel")
        shutting_down.wait("text_delta", "shutdown", shutdown_start)
        shutting_down.send({"type": "shutdown"})
        shutting_down.result("shutdown", shutdown_start, 19)
        assert shutting_down.process.wait(timeout=5) == 0

        session = host.session
        host.stop()
        restarted = Host(executable, project, database, identifier, session)
        hosts.append(restarted)
        count = len(Provider.requests)
        replay = restarted.submit("allow", "permission allow", auto_edit=True)
        restarted.result("allow", replay, 12)
        assert len(Provider.requests) == count
        recovered = restarted.submit("after-restart", "recovered")
        restarted.result("after-restart", recovered)
        restarted.stop()
        assert not Provider.errors, Provider.errors
        succeeded = True
        print("engine host acceptance passed: streaming, continuous submissions, provider snapshots, nonce approval, cancellation, Plan, Goal, compact, consult, restart and durable replay refusal")
    finally:
        for host in hosts:
            host.abort()
        advapi.CredDeleteW(target, 1, 0)
        advapi.CredDeleteW(second_target, 1, 0)
        server.shutdown()
        server.server_close()
        if succeeded:
            clean_generated_directory(project)
        else:
            print(f"failed fixture retained for inspection: {project}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp-fixture":
        mcp_server(sys.argv[2])
    else:
        main()
