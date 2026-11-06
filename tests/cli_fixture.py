"""Run the real CLI against an isolated DB, credential and loopback provider."""
import ctypes
from contextlib import closing, contextmanager
from ctypes import wintypes
import http.server
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid


class Credential(ctypes.Structure):
    _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
                ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]


@contextmanager
def isolated_project():
    project = Path(tempfile.mkdtemp(prefix="sencode-cli-中文😀-"))
    try:
        yield project
    finally:
        root = project.resolve(strict=True)
        entries = list(project.rglob("*"))
        # Inventory every target before cleanup, then remove literal files and
        # empty directories individually. Never recurse through an outside link.
        assert all(entry.parent.resolve().is_relative_to(root) for entry in entries)
        assert all(entry.is_symlink() or entry.resolve().is_relative_to(root) for entry in entries)
        for entry in sorted(entries, key=lambda item: len(item.parts), reverse=True):
            if entry.is_symlink():
                entry.unlink()
            elif entry.is_file():
                # Git marks loose objects read-only on Windows. These files
                # are owned solely by this inventoried temporary fixture.
                entry.chmod(entry.stat().st_mode | stat.S_IWUSR)
                entry.unlink()
            else:
                entry.rmdir()
        project.rmdir()


class Fixture(http.server.BaseHTTPRequestHandler):
    errors = []
    calls = []
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.headers.get("Authorization") != "Bearer fixture-key":
            self.send_error(401)
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        history = body["messages"]
        first = next((x.get("content", "") for x in history if x["role"] == "user"), "")
        results = [x for x in history if x["role"] == "tool"]
        count = len(results)
        self.calls.append((first, count))
        tool = None
        calls = []
        if first == "modify fixture":
            if count == 0:
                tool = ("read_file", {"path": "example.txt"})
            elif count == 1:
                assert "before 世界" in results[-1]["content"]
                tool = ("apply_patch", {"path": "example.txt", "old": "before", "new": "after"})
            elif count == 2:
                assert not json.loads(results[-1]["content"])["is_error"]
                tool = ("run_command", {"command": "test -f example.txt"})
            elif count == 3:
                command = json.loads(json.loads(results[-1]["content"])["content"])
                assert command["exit_code"] == 0
        elif first == "plan fixture":
            attempts = [("apply_patch", {"path": "example.txt", "old": "after", "new": "forbidden"}),
                        ("run_command", {"command": "Set-Content forbidden.txt yes"}),
                        ("mcp__call", {"server": "missing", "tool": "write", "arguments": {}}),
                        ("write_plan", {"content": "Inspect and test the existing project."})]
            if count < len(attempts):
                tool = attempts[count]
        elif first in ("goal fixture", "goal path fixture"):
            if count == 0:
                tool = ("finish_goal", {"summary": "The external verification checks the artifact."})
        elif first in ("goal fail fixture", "goal facility fixture", "goal approve fixture"):
            tool = ("finish_goal", {"summary": "Run the explicitly configured check."})
        elif first == "goal repeat fixture":
            pass
        elif first == "goal denied fixture":
            tool = ("write_file", {"path": "denied.txt", "content": "must not be created"})
        elif first == "denied edit fixture":
            assert count == 0, "permission pause must not send another request"
            tool = ("write_file", {"path": "ordinary-denied.txt", "content": "must not be created"})
        elif first == "denied command fixture":
            assert count == 0, "permission pause must not send another request"
            tool = ("run_command", {"command": "Set-Content -LiteralPath command-denied.txt forbidden"})
        elif first == "denied mcp fixture":
            assert count == 0, "permission pause must not send another request"
            tool = ("mcp__call", {"server": "fixture-denied", "tool": "write", "arguments": {}})
        elif first == "stdout fixture":
            pass
        elif first.startswith("Preserve still-relevant facts") or first.startswith("Summarize this coding session"):
            # Context compaction deliberately requires a substantial, clean
            # summary. Keep this fixture above that public minimum so the
            # resume/compact path exercises a successful request rather than
            # the quality-rejection diagnostic.
            summary = "Session evidence: " + ("The coding task, tool results, permissions, and next verification step are preserved. " * 12)
            delta = {"choices": [{"delta": {"content": summary}, "finish_reason": "stop"}],
                     "usage": {"prompt_tokens": 11, "completion_tokens": 90}}
            encoded = ("data: " + json.dumps(delta, ensure_ascii=False) + "\n\ndata: [DONE]\n\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                for offset in range(0, len(encoded), 3):
                    self.wfile.write(encoded[offset:offset + 3])
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            self.close_connection = True
            return
        elif first == "agents fixture":
            if count == 0:
                calls = [("spawn_agent", {"role": "explore", "prompt": "child read fixture"}),
                         ("spawn_agent", {"role": "general", "prompt": "child write fixture"})]
            elif count == 2:
                tool = ("wait_agents", {"timeout_ms": 1000})
            elif count == 3:
                report = json.loads(results[-1]["content"])
                if not all(child["done"] for child in report["children"]):
                    tool = ("wait_agents", {"timeout_ms": 1000})
        elif first == "child read fixture":
            if count == 0:
                tool = ("read_file", {"path": "example.txt"})
            else:
                assert "after 世界" in results[-1]["content"]
        elif first == "child write fixture":
            if count == 0:
                tool = ("write_file", {"path": "child.txt", "content": "child verified 世界"})
            else:
                assert not json.loads(results[-1]["content"])["is_error"]
        elif first == "plan git fixture":
            if count == 0:
                tool = ("git_status", {})
            elif count == 1:
                assert not json.loads(results[-1]["content"])["is_error"]
                tool = ("git_diff", {})
            elif count == 2:
                assert not json.loads(results[-1]["content"])["is_error"]
                tool = ("spawn_agent", {"role": "explore", "prompt": "child git fixture"})
            elif count == 3 or not all(child["done"] for child in json.loads(results[-1]["content"])["children"]):
                tool = ("wait_agents", {"timeout_ms": 1000})
        elif first == "child git fixture":
            if count == 0:
                tool = ("git_status", {})
            elif count == 1:
                assert not json.loads(results[-1]["content"])["is_error"]
                tool = ("git_diff", {})
            else:
                assert not json.loads(results[-1]["content"])["is_error"]
        else:
            if first != "interactive fixture":
                assert any(x.get("content", "") == "modify fixture" for x in history)
        if tool:
            calls.append(tool)
        if calls:
            delta = {"tool_calls": [{"index": index, "id": f"{first}-{count}-{index}",
                                      "function": {"name": name, "arguments": json.dumps(args)}}
                                     for index, (name, args) in enumerate(calls)]}
            reason = "tool_calls"
        else:
            delta = {"content": "fixture complete 世界😀"}
            reason = "stop"
        event = {"choices": [{"delta": delta, "finish_reason": reason}],
                 "usage": {"prompt_tokens": 11, "completion_tokens": 7}}
        encoded = ("data: " + json.dumps(event, ensure_ascii=False) + "\n\ndata: [DONE]\n\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            for offset in range(0, len(encoded), 3):
                self.wfile.write(encoded[offset:offset + 3])
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            # The closed-stdout test intentionally cancels its in-flight stream.
            pass
        self.close_connection = True


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    executable = Path(sys.argv[1]).resolve()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    identifier = "custom-cli-fixture-" + uuid.uuid4().hex
    target = "Sencode/connection/" + identifier
    key = (ctypes.c_ubyte * len(b"fixture-key")).from_buffer_copy(b"fixture-key")
    cred = Credential(Type=1, TargetName=target, CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    if not advapi.CredWriteW(ctypes.byref(cred), 0):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        with isolated_project() as project:
            database = project / "isolated.sqlite"
            (project / "example.txt").write_text("before 世界\n", encoding="utf-8")

            def run(*arguments, expected=0, stdin=None, environment=None):
                result = subprocess.run([str(executable), "--cwd", str(project), "--database", str(database), *arguments],
                                        cwd=project, capture_output=True, encoding="utf-8", input=stdin, timeout=60,
                                        env=None if environment is None else dict(os.environ, **environment))
                if result.returncode != expected:
                    with closing(sqlite3.connect(database)) as failed:
                        evidence = {"requests": Fixture.calls, "history": failed.execute("SELECT role,text FROM messages").fetchall(),
                                    "claims": failed.execute("SELECT name,state FROM shared_tool_ledger").fetchall()}
                    raise AssertionError((arguments, result.returncode, result.stdout, result.stderr, evidence))
                print(result.stdout.strip())
                lines = result.stdout.strip().splitlines()
                return json.loads(lines[-1]) if lines and lines[-1].startswith("{") else None

            run("doctor")
            config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                      "protocol": "chatCompletions", "successfulProtocol": "chatCompletions",
                      "selectedModelId": "fixture", "credentialRef": target, "enabledModels": []}
            with closing(sqlite3.connect(database)) as db:
                db.create_function("sengoo_context", 1, lambda key: "test-fixture" if key == "instance_id" else None)
                db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','fixture',?,'fixture',1,1)",
                           (identifier, json.dumps(config)))
                db.commit()
            result = run("--connection", identifier, "--auto-edit", "--allow-commands", "-p", "modify fixture", "--output-format", "json")
            assert result["success"] and (project / "example.txt").read_text(encoding="utf-8") == "after 世界\n"
            resumed = run("resume", result["session_id"], "--connection", identifier, "-p", "continue fixture", "--output-format", "json")
            assert resumed["session_id"] == result["session_id"] and resumed["success"]
            recent = run("resume", "--connection", identifier, "-p", "continue fixture", "--output-format", "json")
            assert recent["session_id"] == result["session_id"] and recent["success"]
            # No subcommand/prompt starts in the OS cwd and accepts redirected
            # session input. The single saved connection can be selected once.
            run(stdin="interactive fixture\n/quit\n")
            plan = run("--connection", identifier, "--plan", "--auto-edit", "--allow-commands", "-p", "plan fixture", "--output-format", "json")
            assert plan["success"] and not (project / "forbidden.txt").exists()
            assert (project / "example.txt").read_text(encoding="utf-8") == "after 世界\n"
            assert list((project / ".sencode" / "plans").glob("*.md"))
            goal = run("--connection", identifier, "--allow-commands", "--goal", "goal fixture", "--check", "exit 0", "--output-format", "json")
            assert goal["success"]
            failed = run("--connection", identifier, "--allow-commands", "--goal", "goal fail fixture", "--check", "exit 1", "--output-format", "json", expected=1)
            assert not failed["success"]
            denied = run("--connection", identifier, "--goal", "goal denied fixture", "--output-format", "json", expected=1)
            assert not denied["success"] and not (project / "denied.txt").exists()
            mcp_config = {"servers": [{"name": "fixture-denied", "command": "powershell.exe",
                                       "args": ["-NoProfile", "-NonInteractive", "-Command",
                                                "Set-Content -LiteralPath mcp-denied.txt forbidden"]}]}
            (project / ".sencode" / "mcp.json").write_text(json.dumps(mcp_config), encoding="utf-8")
            for kind, sentinel in (("edit", "ordinary-denied.txt"), ("command", "command-denied.txt"), ("mcp", "mcp-denied.txt")):
                prompt = f"denied {kind} fixture"
                ordinary = run("--connection", identifier, "-p", prompt, "--output-format", "json", expected=1)
                assert not ordinary["success"] and ordinary["code"] == 12 and not (project / sentinel).exists()
                assert sum(first == prompt for first, _ in Fixture.calls) == 1
            approval = run("--connection", identifier, "--goal", "goal approve fixture", "--check", "exit 0", "--output-format", "json", expected=1)
            assert not approval["success"]
            # Goal checks deliberately retain the explicit system PowerShell
            # contract. Absolute shell resolution must succeed without PATH;
            # clearing PATH no longer simulates an unavailable facility.
            pathless = run("--connection", identifier, "--allow-commands", "--goal", "goal path fixture", "--check", "exit 0", "--output-format", "json", environment={"PATH": ""})
            assert pathless["success"]
            missing_system_root = project / "unavailable-windows-root-fixture"
            assert not missing_system_root.exists()
            facility = run("--connection", identifier, "--allow-commands", "--goal", "goal facility fixture", "--check", "exit 0", "--output-format", "json", expected=1,
                           environment={"PATH": "", "SystemRoot": str(missing_system_root)})
            assert not facility["success"]
            budget = run("--connection", identifier, "--goal", "goal repeat fixture", "--max-requests", "2", "--output-format", "json", expected=1)
            assert not budget["success"]
            closed_output = subprocess.Popen([str(executable), "--cwd", str(project), "--database", str(database),
                                              "--connection", identifier, "--goal", "stdout fixture",
                                              "--output-format", "stream-json"], cwd=project,
                                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            closed_output.stdout.close()
            closed_output.stdout = None
            _, output_error = closed_output.communicate(timeout=20)
            assert closed_output.returncode != 0, output_error
            with closing(sqlite3.connect(database)) as db:
                modes = lambda session: json.loads(db.execute("SELECT mode_json FROM shared_modes WHERE session_id=?", (session,)).fetchone()[0])["goal"]
                assert modes(failed["session_id"])["same_failure_count"] == 2
                assert modes(failed["session_id"])["status"] == 2
                assert modes(denied["session_id"])["requests"] == 1
                assert modes(approval["session_id"])["status"] == 2
                assert modes(pathless["session_id"])["status"] == 4
                assert modes(facility["session_id"])["status"] == 2 and modes(facility["session_id"])["same_failure_count"] == 0
                assert modes(budget["session_id"])["requests"] == 2
                broken = [json.loads(row[0])["goal"] for row in db.execute("SELECT mode_json FROM shared_modes")
                          if "goal" in json.loads(row[0]) and json.loads(row[0])["goal"].get("objective") == "stdout fixture"]
                assert len(broken) == 1 and broken[0]["status"] == 2 and broken[0]["requests"] == 1
                before_compact = modes(failed["session_id"])["requests"]
                before_compact_tokens = modes(failed["session_id"])["tokens"]
            before_compact_calls = len(Fixture.calls)
            run("resume", failed["session_id"], "--connection", identifier, stdin="/compact\n/quit\n")
            with closing(sqlite3.connect(database)) as db:
                saved = json.loads(db.execute("SELECT mode_json FROM shared_modes WHERE session_id=?", (failed["session_id"],)).fetchone()[0])["goal"]
                # The summary request is still billed when the candidate
                # summary cannot satisfy the quality postcondition. Paused
                # Goal accounting must include that real provider call.
                compaction_calls = Fixture.calls[before_compact_calls:]
                assert len(compaction_calls) == 1 and compaction_calls[0][0].startswith(("Preserve still-relevant facts", "Summarize this coding session")), compaction_calls
                assert saved["requests"] == before_compact + 1 and saved["tokens"] == before_compact_tokens + 101, (before_compact, saved)
                assert saved["same_failure_count"] == 2 and saved["status"] == 2, saved
            agents = run("--connection", identifier, "--auto-edit", "-p", "agents fixture", "--output-format", "json")
            assert agents["success"] and (project / "child.txt").read_text(encoding="utf-8") == "child verified 世界"
            # Read-only Git must never execute repository hooks, clean/process
            # filters, external diffs or textconv, including inside a Plan child.
            def git(*arguments):
                invocation = subprocess.run(["git", *arguments], cwd=project, capture_output=True, encoding="utf-8", timeout=10)
                assert invocation.returncode == 0, (arguments, invocation.stdout, invocation.stderr)

            git("init", "-q")
            git("add", "example.txt")
            (project / "example.txt").write_text("after 世界 changed\n", encoding="utf-8")
            (project / ".gitattributes").write_text("example.txt filter=fixture diff=fixture\n", encoding="utf-8")
            git_directory = project / ".git"
            for name in ("fsmonitor", "clean", "process", "external", "textconv", "pager"):
                hook = git_directory / f"{name}-hook"
                hook.write_text(f"#!/bin/sh\necho invoked > .git/{name}-ran\ncat\n", encoding="utf-8")
                hook.chmod(0o755)
            for key_name, value in {
                "core.fsmonitor": ".git/fsmonitor-hook",
                "filter.fixture.clean": ".git/clean-hook",
                "filter.fixture.required": "true",
                "diff.external": ".git/external-hook",
                "diff.fixture.textconv": ".git/textconv-hook",
                "core.pager": ".git/pager-hook",
                "pager.status": "true",
                "pager.diff": "true",
            }.items():
                git("config", key_name, value)
            # A current-directory/PATH shadow must not become the trusted Git
            # executable. This harmless system binary would reject Git argv.
            shutil.copyfile(Path(os.environ["SystemRoot"]) / "System32" / "whoami.exe", project / "git.exe")
            for use_process in (False, True):
                if use_process:
                    git("config", "filter.fixture.process", ".git/process-hook")
                safe_git = run("--connection", identifier, "--plan", "-p", "plan git fixture", "--output-format", "json",
                               environment={"PATH": str(project) + os.pathsep + os.environ["PATH"]})
                assert safe_git["success"]
                assert not list(git_directory.glob("*-ran")), "read-only Git executed a repository command"
            assert sum(first == "child git fixture" and count == 2 for first, count in Fixture.calls) == 2
            with closing(sqlite3.connect(database)) as db:
                db.create_function("sengoo_context", 1, lambda key: "test-fixture" if key == "instance_id" else None)
                project_id = db.execute("SELECT project_id FROM sessions WHERE id=?", (result["session_id"],)).fetchone()[0]
                for index in range(105):
                    db.execute("INSERT INTO sessions(id,project_id,title,created_at,updated_at,last_sent_at) VALUES(?,?,'later fixture',?,?,?)",
                               (f"later-{index}", project_id, 9000000000000 + index, 9000000000000 + index, 9000000000000 + index))
                db.commit()
            old = run("resume", result["session_id"], "--connection", identifier, "-p", "continue fixture", "--output-format", "json")
            assert old["session_id"] == result["session_id"] and old["success"]
            with closing(sqlite3.connect(database)) as db:
                assert db.execute("SELECT count(*) FROM shared_tool_ledger WHERE state='complete'").fetchone()[0] >= 8
                assert db.execute("SELECT count(*) FROM shared_executions WHERE active=1").fetchone()[0] == 0
            print("external CLI read/patch/command/resume/Plan/Goal and Git hook isolation fixture passed")
    finally:
        advapi.CredDeleteW(target, 1, 0)
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
