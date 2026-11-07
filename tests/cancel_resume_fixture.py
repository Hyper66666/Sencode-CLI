"""Cancellation and interrupted-state recovery using isolated real hosts.

Only synthetic credentials, temporary projects and a loopback provider are used.
The provider validates paired tool inputs/outputs for all three native protocols.
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
import tempfile
import threading
import time
import traceback
import uuid

from cli_fixture import Credential
from engine_fixture import Host
from tui_console_fixture import checked, environment_for, remove_owned_tree


def wire_history(body, protocol):
    calls, results, texts = {}, {}, []
    if protocol == "responses":
        for item in body["input"]:
            kind = item.get("type")
            if kind == "function_call":
                assert item["call_id"] not in calls
                calls[item["call_id"]] = item
            elif kind == "function_call_output":
                assert item["call_id"] not in results
                results[item["call_id"]] = item["output"]
            elif item.get("role") == "user":
                content = item.get("content", "")
                texts.append(content if isinstance(content, str) else "".join(x.get("text", "") for x in content))
    elif protocol == "messages":
        for item in body["messages"]:
            content = item.get("content", [])
            if isinstance(content, str):
                if item["role"] == "user": texts.append(content)
                continue
            for block in content:
                if block.get("type") == "tool_use":
                    assert block["id"] not in calls
                    calls[block["id"]] = block
                elif block.get("type") == "tool_result":
                    assert block["tool_use_id"] not in results
                    results[block["tool_use_id"]] = block["content"]
                elif block.get("type") == "text" and item["role"] == "user":
                    texts.append(block["text"])
    else:
        for item in body["messages"]:
            for call in item.get("tool_calls", []):
                assert call["id"] not in calls
                calls[call["id"]] = call
            if item["role"] == "tool":
                assert item["tool_call_id"] not in results
                results[item["tool_call_id"]] = item["content"]
            elif item["role"] == "user":
                texts.append(item.get("content", ""))
    assert calls.keys() == results.keys(), (list(calls), list(results))
    return texts[-1], calls, results


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_): pass

    def emit(self, value):
        self.wfile.write(("data: " + (value if isinstance(value, str) else json.dumps(value)) + "\n\n").encode())
        self.wfile.flush()

    def answer(self, protocol, text, tool=None, finish=True):
        if protocol == "responses":
            if text: self.emit({"type": "response.output_text.delta", "delta": text})
            if tool:
                identifier, arguments = tool
                self.emit({"type": "response.output_item.added", "output_index": 0,
                           "item": {"type": "function_call", "id": "fc_" + identifier,
                                    "call_id": identifier, "name": "run_command", "arguments": ""}})
                self.emit({"type": "response.function_call_arguments.delta", "output_index": 0,
                           "delta": json.dumps(arguments)})
            if finish: self.emit({"type": "response.completed", "response": {"status": "completed", "usage": {"input_tokens": 8, "output_tokens": 4}}})
        elif protocol == "messages":
            self.emit({"type": "message_start", "message": {"usage": {"input_tokens": 8}}})
            if text: self.emit({"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}})
            if tool:
                identifier, arguments = tool
                self.emit({"type": "content_block_start", "index": 1,
                           "content_block": {"type": "tool_use", "id": identifier, "name": "run_command", "input": {}}})
                self.emit({"type": "content_block_delta", "index": 1,
                           "delta": {"type": "input_json_delta", "partial_json": json.dumps(arguments)}})
            if finish:
                self.emit({"type": "message_delta", "delta": {"stop_reason": "tool_use" if tool else "end_turn"}, "usage": {"output_tokens": 4}})
                self.emit({"type": "message_stop"})
        else:
            delta = {"content": text}
            if tool:
                identifier, arguments = tool
                delta["tool_calls"] = [{"index": 0, "id": identifier, "function": {"name": "run_command", "arguments": json.dumps(arguments)}}]
            self.emit({"choices": [{"delta": delta, "finish_reason": ("tool_calls" if tool else "stop") if finish else None}],
                       "usage": {"prompt_tokens": 8, "completion_tokens": 4}})
            if finish: self.emit("[DONE]")

    def do_POST(self):
        try:
            protocol = "responses" if self.path.endswith("/responses") else "messages" if self.path.endswith("/messages") else "chatCompletions"
            assert (self.headers.get("x-api-key") if protocol == "messages" else self.headers.get("Authorization")) == ("fixture-key" if protocol == "messages" else "Bearer fixture-key")
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            prompt, calls, results = wire_history(body, protocol)
            self.server.requests.append({"protocol": protocol, "prompt": prompt, "calls": list(calls), "results": results})
            self.send_response(200); self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close"); self.end_headers()
            if prompt == "FAULT":
                self.answer(protocol, "Bookkeeping failure fixture", (protocol + "-fault", {"command": "printf forbidden >> forbidden.txt", "shell": "bash", "timeout_ms": 10000}))
            elif prompt == "RUN_CANCEL":
                identifier = protocol + "-once"
                if identifier not in results:
                    self.answer(protocol, "", (identifier, {"command": "printf 'once\\n' >> once.txt", "shell": "bash", "timeout_ms": 10000}))
                else:
                    self.answer(protocol, "WAIT_FOR_CANCEL", finish=False)
                    self.server.release.wait(12)
            else:
                self.answer(protocol, "CONTINUED_" + protocol)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except BaseException:
            self.server.errors.append(traceback.format_exc())
        finally:
            self.close_connection = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path); parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(); executable = args.executable.resolve(strict=True)
    evidence = {"schema": 1, "scope": "isolated-loopback-real-host", "result": "running", "checks": [],
                "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()}
    scratch = Path(tempfile.mkdtemp(prefix="sencode-cancel-resume-")); previous_env = dict(os.environ)
    hosts = []; targets = []
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests = []; server.errors = []; server.release = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]; advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]; advapi.CredDeleteW.restype = wintypes.BOOL

    def record(name): evidence["checks"].append({"name": name, "status": "passed"})

    try:
        environment = environment_for(scratch)
        os.environ.clear(); os.environ.update(environment)
        database = scratch / "catalog.sqlite3"

        def sql(statement, values=()):
            with closing(sqlite3.connect(database, timeout=10)) as db:
                db.create_function("sengoo_context", 1, lambda key: "cancel-fixture" if key == "instance_id" else None)
                result = db.execute(statement, values).fetchall(); db.commit(); return result

        def append(session, message):
            revision = sql("SELECT COALESCE(MAX(revision),0)+1 FROM messages WHERE session_id=?", (session,))[0][0]
            identifier = uuid.uuid4().hex
            sql("INSERT INTO messages(id,session_id,role,text,created_at,completed_at,revision,shared_fence) VALUES(?,?,?,?,1,1,?,1)",
                (identifier, session, message["role"], message.get("content", ""), revision))
            sql("INSERT INTO shared_history(message_id,session_id,message_json,execution_id,fence) VALUES(?,?,?,'fixture-interruption',1)",
                (identifier, session, json.dumps(message)))

        for protocol in ("chatCompletions", "responses", "messages"):
            workspace = scratch / ("project-" + protocol); workspace.mkdir()
            identifier = "custom-cancel-" + uuid.uuid4().hex
            init = subprocess.run([str(executable), "--cwd", str(workspace), "--database", str(database), "doctor"], capture_output=True, timeout=25)
            assert init.returncode == 0, init.stderr.decode(errors="replace")
            target = "Sencode/connection/" + identifier
            blob = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
            credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=blob, Persist=1)
            checked(advapi.CredWriteW(ctypes.byref(credential), 0)); targets.append(target)
            config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": protocol,
                      "successfulProtocol": protocol, "selectedModelId": "fixture", "credentialRef": target, "enabledModels": []}
            sql("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','cancel fixture',?,'fixture',1,1)", (identifier, json.dumps(config)))
            host = Host(executable, workspace, database, identifier); hosts.append(host)
            session = host.session
            modes = json.loads(sql("SELECT mode_json FROM shared_modes WHERE session_id=?", (session,))[0][0])
            attempts = [{"id": f"old-{i}", "execution_id": "old", "fence": 1, "connection_id": identifier, "model": "fixture",
                         "purpose": "native-agent", "attempt": 1, "status": "accepted", "error": 0, "usage_source": "provider-reported",
                         "input_tokens": 1, "output_tokens": 1, "updated_at": 1} for i in range(134)]
            modes["request_attempts"] = {"schema": 1, "attempts": attempts}; modes["fixture_preserved"] = {"values": list(range(356))}
            modes["independent_a"] = {"values": list(range(2200))}
            modes["independent_b"] = {"values": list(range(2200))}
            sql("UPDATE shared_modes SET mode_json=? WHERE session_id=?", (json.dumps(modes), session))
            start = host.submit(protocol + "-cancel", "RUN_CANCEL", full_access=True)
            host.wait("text_delta", start=start, timeout=25)
            host.send({"type": "cancel", "id": protocol + "-cancel"})
            host.result(protocol + "-cancel", start, 19)
            assert (workspace / "once.txt").read_text().splitlines() == ["once"]
            record(protocol + "-cancel-after-completed-tool")
            start = host.submit(protocol + "-continue", "CONTINUE", full_access=True)
            host.result(protocol + "-continue", start)
            assert (workspace / "once.txt").read_text().splitlines() == ["once"]
            record(protocol + "-long-session-continue-without-replay")
            sql("CREATE TRIGGER fixture_request_commit_failure BEFORE UPDATE OF mode_json ON shared_modes "
                "WHEN NEW.session_id='" + session + "' AND json_extract(OLD.mode_json,'$.request_attempts.attempts[#-1].status')='running' "
                "AND json_extract(NEW.mode_json,'$.request_attempts.attempts[#-1].status')='accepted' "
                "BEGIN SELECT RAISE(ABORT,'fixture request evidence failure'); END")
            start = host.submit(protocol + "-fault", "FAULT", full_access=True)
            failure = host.wait("result", protocol + "-fault", start)
            assert failure["code"] != 0 and failure["diagnostic"]["reason"] == "request_state_failed", failure
            sql("DROP TRIGGER fixture_request_commit_failure")
            content = sql("SELECT result FROM shared_tool_ledger WHERE session_id=? AND call_id=?", (session, protocol + "-fault"))
            assert len(content) == 1 and json.loads(content[0][0])["not_executed"], content
            assert not (workspace / "forbidden.txt").exists()
            record(protocol + "-post-response-state-failure-settles-before-turn-release")
            start = host.submit(protocol + "-after-fault", "AFTER_FAULT", full_access=True)
            host.result(protocol + "-after-fault", start)
            evidence_state = json.loads(sql("SELECT mode_json FROM shared_modes WHERE session_id=?", (session,))[0][0])
            assert not any(a["status"] == "running" for a in evidence_state["request_attempts"]["attempts"]), evidence_state["request_attempts"]
            assert evidence_state["independent_a"] == modes["independent_a"]
            assert evidence_state["independent_b"] == modes["independent_b"]
            assert evidence_state["fixture_preserved"] == modes["fixture_preserved"]
            record(protocol + "-aggregate-state-isolated-with-unrelated-fields-preserved")
            record(protocol + "-state-failure-continue-and-stale-attempt-recovery")
            host.stop()

            old_calls = [{"id": protocol + "-saved", "name": "run_command", "arguments": json.dumps({"command": "printf duplicate >> forbidden.txt", "shell": "bash"})},
                         {"id": protocol + "-unclaimed", "name": "run_command", "arguments": json.dumps({"command": "printf unexpected >> forbidden.txt", "shell": "bash"})}]
            append(session, {"role": "assistant", "content": "Saved before interruption", "tool_calls": old_calls})
            saved = json.dumps({"content": "EXACT_RESULT_中文", "is_error": False})
            sql("INSERT INTO shared_tool_ledger(session_id,call_id,execution_id,fence,name,arguments,state,result,updated_at) VALUES(?,?,'fixture-interruption',1,'run_command',?,'complete',?,1)",
                (session, old_calls[0]["id"], old_calls[0]["arguments"], saved))
            resumed = Host(executable, workspace, database, identifier, session); hosts.append(resumed)
            start = resumed.submit(protocol + "-repair", "REPAIR_CONTINUE", full_access=True)
            resumed.result(protocol + "-repair", start)
            request = server.requests[-1]
            assert request["results"][old_calls[0]["id"]] == saved, request
            assert json.loads(request["results"][old_calls[1]["id"]])["not_executed"], request
            assert not (workspace / "forbidden.txt").exists()
            assert sql("SELECT state FROM shared_tool_ledger WHERE session_id=? AND call_id=?", (session, old_calls[1]["id"])) == [("complete",)]
            record(protocol + "-restart-restores-exact-result-and-skips-unclaimed-tool")
            before_count = sql("SELECT COUNT(*) FROM messages WHERE session_id=? AND role='tool'", (session,))[0][0]
            start = resumed.submit(protocol + "-again", "CONTINUE_AGAIN")
            resumed.result(protocol + "-again", start)
            assert sql("SELECT COUNT(*) FROM messages WHERE session_id=? AND role='tool'", (session,))[0][0] == before_count
            record(protocol + "-recovery-is-idempotent")
            resumed.stop()

            unknown_calls = [{"id": protocol + "-blocked-absent", "name": "run_command", "arguments": "{}"},
                             {"id": protocol + "-blocked-unknown", "name": "run_command", "arguments": "{}"}]
            append(session, {"role": "assistant", "content": "Uncertain fixture", "tool_calls": unknown_calls})
            sql("INSERT INTO shared_tool_ledger(session_id,call_id,execution_id,fence,name,arguments,state,result,updated_at) VALUES(?,?,'fixture-interruption',1,'run_command','{}','complete',?,1)",
                (session, unknown_calls[1]["id"], json.dumps({"content": "unknown", "is_error": True, "outcome_unknown": True})))
            blocked = Host(executable, workspace, database, identifier, session); hosts.append(blocked)
            request_count = len(server.requests); row_count = sql("SELECT COUNT(*) FROM messages WHERE session_id=?", (session,))[0][0]
            start = blocked.submit(protocol + "-unknown", "CONTINUE_UNKNOWN")
            outcome = blocked.result(protocol + "-unknown", start, 12)
            assert outcome["diagnostic"]["automatic_replay_forbidden"], outcome
            assert len(server.requests) == request_count
            assert sql("SELECT COUNT(*) FROM messages WHERE session_id=?", (session,))[0][0] == row_count
            assert not sql("SELECT 1 FROM shared_tool_ledger WHERE session_id=? AND call_id=?", (session, unknown_calls[0]["id"]))
            record(protocol + "-unknown-outcome-blocks-before-any-repair-or-model-call")
            blocked.stop()
        assert not server.errors, server.errors
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"; evidence["error"] = traceback.format_exc()
    finally:
        server.release.set()
        for host in hosts: host.abort()
        for target in targets: checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown(); server.server_close()
        evidence["provider_errors"] = server.errors; evidence["request_count"] = len(server.requests)
        evidence["credential_targets_removed"] = len(targets)
        evidence["fixture_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        os.environ.clear(); os.environ.update(previous_env)
        remove_owned_tree(scratch)
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if evidence["result"] == "passed" else 1


if __name__ == "__main__": raise SystemExit(main())
