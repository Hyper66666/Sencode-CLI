"""Real JSONL hosts; only the three model endpoints are loopback fixtures."""
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
import tempfile
import threading
import traceback
import uuid

from cli_fixture import Credential
from engine_fixture import Host, COMPACTION_SUMMARY
from cancel_resume_fixture import Provider as StreamProvider, wire_history
from tui_console_fixture import checked, environment_for, remove_owned_tree


class Provider(StreamProvider):
    def finish_stream(self, protocol):
        if protocol == "responses":
            self.emit({"type": "response.completed", "response": {"status": "completed", "usage": {"input_tokens": 8, "output_tokens": 4}}})
        elif protocol == "messages":
            self.emit({"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 4}})
            self.emit({"type": "message_stop"})
        else:
            self.emit({"choices": [{"delta": {}, "finish_reason": "stop"}]}); self.emit("[DONE]")

    def do_POST(self):
        try:
            protocol = "responses" if self.path.endswith("/responses") else "messages" if self.path.endswith("/messages") else "chatCompletions"
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            prompt, calls, results = wire_history(body, protocol)
            self.server.requests.append({"protocol": protocol, "prompt": prompt, "body": body})
            self.send_response(200); self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close"); self.end_headers()
            if protocol == "chatCompletions" and body.get("messages", [{}])[0].get("content", "").startswith("You summarize coding sessions"):
                self.emit({"choices": [{"delta": {"reasoning_content": "private summary analysis"}, "finish_reason": None}]})
                if hasattr(self.server, "summary_started"):
                    self.server.summary_started.set()
                if hasattr(self.server, "summary_release"):
                    assert self.server.summary_release.wait(15)
                self.answer(protocol, COMPACTION_SUMMARY)
            elif prompt in ("STEER_STREAM", "STEER_CANCEL", "STEER_DUPLICATE"):
                self.answer(protocol, "STREAMING_BEFORE_INSERT", finish=False)
                assert self.server.release.wait(15), "fixture stream not released"
                self.finish_stream(protocol)
            elif prompt == "STEER_TOOL" and protocol + "-once" not in results:
                self.answer(protocol, "", (protocol + "-once", {"command": "printf 'once\\n' >> once.txt; sleep 1", "shell": "bash", "timeout_ms": 10000}))
            else:
                self.answer(protocol, "APPLIED: " + prompt)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # The explicit cancellation scenario closes its HTTP stream.
        except BaseException:
            self.server.errors.append(traceback.format_exc())
        finally:
            self.close_connection = True


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, required=True); args = parser.parse_args()
    executable = args.executable.resolve(); scratch = Path(tempfile.mkdtemp(prefix="sencode-steering-世界-"))
    evidence = {"schema": 1, "scope": "isolated-real-host-loopback-three-protocols",
                "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(), "checks": []}
    previous = dict(os.environ); hosts = []; targets = []
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests = []; server.errors = []; server.release = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]; advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]; advapi.CredDeleteW.restype = wintypes.BOOL

    def record(protocol, name): evidence["checks"].append({"name": protocol + "-" + name, "status": "passed"})

    try:
        environment = environment_for(scratch)
        os.environ.clear(); os.environ.update(environment)
        database = scratch / "catalog.sqlite3"

        def sql(statement, values=()):
            with closing(sqlite3.connect(database, timeout=10)) as db:
                db.create_function("sengoo_context", 1, lambda k: "steering-fixture" if k == "instance_id" else None)
                rows = db.execute(statement, values).fetchall(); db.commit(); return rows

        bootstrap = Host(executable, scratch, database, ""); hosts.append(bootstrap); bootstrap.stop()
        for protocol in ("chatCompletions", "responses", "messages"):
            project = scratch / protocol; project.mkdir()
            identifier = "custom-steer-" + uuid.uuid4().hex; target = "Sencode/connection/" + identifier
            key = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
            credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=key, Persist=1)
            checked(advapi.CredWriteW(ctypes.byref(credential), 0)); targets.append(target)
            config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": protocol,
                      "credentialRef": target, "selectedModelId": "fixture", "enabledModels": [{"id": "fixture"}]}
            sql("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Fixture',?,'fixture',1,1)", (identifier, json.dumps(config)))
            host = Host(executable, project, database, identifier); hosts.append(host)
            server.release.clear(); start = host.submit("stream", "STEER_STREAM")
            session = host.wait("session", "stream", start); assert session["live_steering"]
            host.wait("text_delta", "stream", start); request_count = len(server.requests)
            message = {"type": "steer", "id": "message-one", "request_id": "stream", "text": "补充条件 中文😀"}
            host.send(dict(message, id="stale", request_id="old")); host.wait("steering_rejected", "old", start)
            host.send(dict(message, id="unsafe", full_access=True)); host.wait("steering_rejected", "stream", start)
            host.send(message); host.send(message); host.wait("steering_pending", "stream", start)
            assert len(server.requests) == request_count, "insertion started a parallel request"
            server.release.set(); outcome = host.result("stream", start)
            assert outcome["content"] == "APPLIED: 补充条件 中文😀", outcome
            applied = [e for e in host.events[start:] if e.get("type") == "steering_applied"]
            assert len(applied) == 1 and len(server.requests) == request_count + 1
            saved = [json.loads(r[0]) for r in sql("SELECT message_json FROM shared_history WHERE session_id=?", (host.session,))]
            assert sum(m.get("cli_steering_id") == "message-one" for m in saved) == 1
            assert not any(e.get("type") == "result" and not e.get("success") for e in host.events[start:])
            record(protocol, "inflight-stream-continues-fifo-deduplicated-durable-insertion")

            start = host.submit("tool", "STEER_TOOL", allow_commands=True)
            host.wait("tool", "tool", start)
            host.send({"type": "steer", "id": "message-tool", "request_id": "tool", "text": "AFTER_TOOL"})
            outcome = host.result("tool", start)
            assert outcome["content"] == "APPLIED: AFTER_TOOL", outcome
            assert (project / "once.txt").read_text(encoding="utf-8") == "once\n"
            assert sql("SELECT COUNT(*) FROM shared_tool_ledger WHERE session_id=? AND call_id=? AND state='complete'", (host.session, protocol + "-once")) == [(1,)]
            record(protocol, "active-tool-finishes-once-and-complete-pairs-precede-insertion")

            server.release.clear(); start = host.submit("cancel", "STEER_CANCEL")
            host.wait("text_delta", "cancel", start)
            commands = [{"type": "steer", "id": "message-cancel", "request_id": "cancel", "text": "NEVER_APPLIED"}, {"type": "cancel", "id": "cancel"}]
            host.process.stdin.write("".join(json.dumps(c) + "\n" for c in commands)); host.process.stdin.flush()
            host.result("cancel", start, 19); server.release.set()
            assert any(e.get("type") == "steering_rejected" and e.get("id") == "message-cancel" for e in host.events[start:])
            assert not sql("SELECT 1 FROM messages WHERE session_id=? AND text='NEVER_APPLIED'", (host.session,))
            record(protocol, "cancellation-wins-and-unapplied-message-is-rejected")
            host.stop()

            resumed = Host(executable, project, database, identifier, host.session); hosts.append(resumed)
            server.release.clear(); start = resumed.submit("duplicate", "STEER_DUPLICATE")
            resumed.wait("text_delta", "duplicate", start)
            resumed.send(dict(message, request_id="duplicate")); server.release.set(); resumed.result("duplicate", start)
            assert any(e.get("type") == "steering_applied" for e in resumed.events[start:])
            saved = [json.loads(r[0]) for r in sql("SELECT message_json FROM shared_history WHERE session_id=?", (host.session,))]
            assert sum(m.get("cli_steering_id") == "message-one" for m in saved) == 1
            assert (project / "once.txt").read_text(encoding="utf-8") == "once\n"
            resumed.stop(); record(protocol, "lost-ack-id-is-not-replayed-after-host-restart")
        assert not server.errors, server.errors
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"; evidence["error"] = traceback.format_exc()
    finally:
        server.release.set()
        for host in hosts: host.abort()
        for target in targets: checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown(); server.server_close(); evidence["provider_errors"] = server.errors
        evidence["fixture_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        os.environ.clear(); os.environ.update(previous); remove_owned_tree(scratch)
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2)); return 0 if evidence["result"] == "passed" else 1


if __name__ == "__main__": raise SystemExit(main())
