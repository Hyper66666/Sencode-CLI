"""Public host / isolated Responses continuation; no external API or real secrets."""
import argparse
from collections import Counter
from contextlib import closing
import ctypes
import hashlib
import http.server
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from cli_fixture import Credential
from engine_fixture import Host, clean_generated_directory
from responses_tool_continuation_fixture import call, message, reasoning


MISSING = object()


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    requests = []
    failures = []
    counts = Counter()

    def log_message(self, *_):
        pass

    def emit(self, items, signal=MISSING, *, kind="response.completed", status="completed"):
        events = []
        for index, item in enumerate(items):
            if item["type"] == "message":
                events.append({"type": "response.output_text.delta", "output_index": index,
                               "delta": item["content"][0].get("text", "")})
        response = {"status": status, "output": items,
                    "usage": {"input_tokens": 11, "output_tokens": 7}}
        if signal is not MISSING:
            response["end_turn"] = signal
        events.append({"type": kind, "response": response})
        data = "".join("data: " + json.dumps(event, ensure_ascii=False) + "\n\n" for event in events).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(data)))
        # A valid framed body completes without relying on a connection-close EOF.
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        for start in range(0, len(data), 3):
            self.wfile.write(data[start:start + 3])
            self.wfile.flush()

    def do_POST(self):
        try:
            assert self.path == "/v1/responses", self.path
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            known = {"native continue", "absent stop", "explicit stop", "phase only", "invalid signal",
                     "incomplete stop", "refusal stop", "budget cap", "tool error recovery", "resume continuation",
                     "spawn continuation", "child continuation", "cancel continuation"}
            users = [item.get("content", "") for item in body["input"] if item.get("role") == "user"]
            prompt = next(value for value in reversed(users) if value in known)
            self.requests.append(body)
            self.counts[prompt] += 1
            count = self.counts[prompt]
            assert not any("requires_continuation" in item or "responses_end_turn" in item for item in body["input"]), body
            if prompt == "native continue":
                assert users == [prompt], "continuation must not fabricate a user message"
                previous = [item for item in body["input"] if item.get("id", "").startswith("msg-continue-")]
                assert len(previous) == count - 1, (count, previous)
                for index, item in enumerate(previous):
                    assert item["phase"] == ("partial_answer" if index == 0 else "commentary"), previous
                items = [message(f"continue-{count}", f"CONTINUE_{count} 世界😀", ("partial_answer", "commentary", "final_answer")[count - 1])]
                if count == 1:
                    items.append(reasoning("continue"))
                if count > 1:
                    opaque = [item for item in body["input"] if item.get("id") == "rs-continue"]
                    assert len(opaque) == 1 and opaque[0]["encrypted_content"] == "opaque-fixture-continue-世界", opaque
                self.emit(items, count == 3)
            elif prompt == "resume continuation":
                phases = [item.get("phase") for item in body["input"] if item.get("id", "").startswith("msg-continue-")]
                assert phases == ["partial_answer", "commentary", "final_answer"], phases
                self.emit([message("resume", "RESUME_PHASES_OK", "final_answer")], True)
            elif prompt in {"absent stop", "phase only", "explicit stop"}:
                self.emit([message(prompt, "ONE_REQUEST_ONLY", "partial_answer")], True if prompt == "explicit stop" else MISSING)
            elif prompt == "invalid signal":
                self.emit([message("invalid", "INVALID_SIGNAL", "partial_answer")], "false")
            elif prompt == "incomplete stop":
                self.emit([], False, kind="response.incomplete", status="incomplete")
            elif prompt == "refusal stop":
                self.emit([{"id": "refusal", "type": "message", "role": "assistant", "content": [{"type": "refusal", "refusal": "fixture refused"}]}], False)
            elif prompt == "budget cap":
                self.emit([message(f"budget-{count}", "BUDGET_STILL_PARTIAL", "partial_answer")], False)
            elif prompt == "spawn continuation":
                outputs = [item for item in body["input"] if item.get("type") == "function_call_output"]
                if not outputs:
                    self.emit([call("spawn", "spawn_agent", {"prompt": "child continuation", "role": "explore"})], False)
                else:
                    # Parent plus two child requests must share the outer cap.
                    time.sleep(.05)
                    self.emit([message(f"parent-{count}", "CHILD_CONTINUATION_JOINED", "final_answer")], True)
            elif prompt == "child continuation":
                assert users == [prompt], users
                self.emit([message(f"child-{count}", f"CHILD_CONTINUE_{count}", "partial_answer" if count == 1 else "final_answer")], count == 2)
            elif prompt == "cancel continuation":
                if count == 1:
                    self.emit([message("cancel-first", "CANCEL_PARTIAL", "partial_answer")], False)
                else:
                    data = ('data: ' + json.dumps({"type": "response.output_text.delta", "delta": "WAIT_FOR_CANCEL"}) + '\n\n').encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Content-Length", str(len(data) + 100))
                    self.end_headers()
                    self.wfile.write(data)
                    self.wfile.flush()
                    self.server.cancel_release.wait(10)
                    self.close_connection = True
            elif prompt == "tool error recovery":
                outputs = [item for item in body["input"] if item.get("type") == "function_call_output"]
                if not outputs:
                    self.emit([call("lossy", "run_command", {"command": "printf 'valid\\377tail'; printf 'diagnostic\\377end' >&2; exit 2", "shell": "bash"})], False)
                else:
                    tool = json.loads(outputs[-1]["output"])
                    assert tool["is_error"], tool
                    result = json.loads(tool["content"])
                    assert result["stdout"] == "valid�tail" and result["stderr"] == "diagnostic�end", result
                    assert result["stdout_lossy"] and result["stderr_lossy"] and result["exit_code"] == 2, result
                    self.emit([message("recovered", "SHELL_ERROR_RETAINED_AND_CORRECTED", "final_answer")], True)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as error:
            self.failures.append(repr(error))
            self.send_error(400, "fixture assertion failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    options = parser.parse_args()
    executable = options.executable.resolve()
    evidence = {"schema": 1, "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(), "result": "running", "checks": []}
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.cancel_release = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    identifier = "custom-end-turn-" + uuid.uuid4().hex
    target = "Sencode/connection/" + identifier
    secret = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    written = False
    hosts = []
    workspace = Path(tempfile.mkdtemp(prefix="sencode-end-turn-中文-")).resolve()
    succeeded = False
    try:
        database = workspace / "isolated.sqlite"
        initialized = subprocess.run([str(executable), "--cwd", str(workspace), "--database", str(database), "doctor"], capture_output=True, timeout=25)
        assert initialized.returncode == 0, initialized.stderr.decode(errors="replace")
        credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=secret, Persist=1)
        assert advapi.CredWriteW(ctypes.byref(credential), 0), ctypes.get_last_error()
        written = True
        config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "responses", "successfulProtocol": "responses",
                  "selectedModelId": "fixture", "credentialRef": target, "enabledModels": [{"id": "fixture"}]}
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "end-turn-fixture" if key == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','end-turn fixture',?,'fixture',1,1)", (identifier, json.dumps(config)))
            db.commit()

        def submit(prompt, *, success=True, maximum=10, session="", **fields):
            host = Host(executable, workspace, database, identifier, session)
            hosts.append(host)
            started = time.monotonic()
            start = host.submit("case-" + uuid.uuid4().hex, prompt, maximum_requests=maximum, **fields)
            result = host.wait("result", start=start, timeout=25)
            assert result["success"] is success, (prompt, result, Provider.failures)
            assert isinstance(result.get("elapsed_ms"), int) and result["elapsed_ms"] >= 0, result
            assert time.monotonic() - started < 15, "completed HTTP body waited for keep-alive EOF"
            result["_session"] = host.session
            host.stop()
            return result

        continued = submit("native continue")
        assert Provider.counts["native continue"] == 3 and continued["content"] == "CONTINUE_3 世界😀", continued
        evidence["checks"].extend(["explicit-false-continues-without-synthetic-user", "ordered-phases-and-opaque-state-preserved", "framed-http-completion-does-not-wait-for-eof", "monotonic-host-elapsed"])
        session = continued["_session"]
        with closing(sqlite3.connect(database)) as db:
            history = [json.loads(row[0]) for row in db.execute("SELECT h.message_json FROM shared_history h JOIN messages m ON m.id=h.message_id WHERE h.session_id=? ORDER BY m.revision,m.created_at,m.id", (session,))]
            turns = [item for item in history if item.get("role") == "assistant"]
            assert [item["responses_end_turn"] for item in turns] == [False, False, True], turns
            assert [item["requires_continuation"] for item in turns] == [True, True, False], turns
        resumed = submit("resume continuation", session=session)
        assert resumed["content"] == "RESUME_PHASES_OK", resumed
        evidence["checks"].append("restart-preserves-control-metadata-and-phases")
        for prompt in ("absent stop", "phase only", "explicit stop"):
            submit(prompt)
            assert Provider.counts[prompt] == 1, (prompt, Provider.counts)
        evidence["checks"].append("missing-true-and-phase-alone-never-guess-continuation")
        for prompt in ("invalid signal", "incomplete stop", "refusal stop"):
            result = submit(prompt, success=False)
            assert Provider.counts[prompt] == 1, (prompt, Provider.counts)
            assert result.get("diagnostic", {}).get("reason") == "provider_request", result
        evidence["checks"].append("malformed-incomplete-refusal-stop-with-request-diagnostics")
        budget = submit("budget cap", success=False, maximum=2)
        assert Provider.counts["budget cap"] == 2 and budget.get("diagnostic", {}).get("reason") == "budget", budget
        evidence["checks"].append("continuations-share-request-budget")
        recovered = submit("tool error recovery", allow_commands=True)
        assert recovered["content"] == "SHELL_ERROR_RETAINED_AND_CORRECTED" and Provider.counts["tool error recovery"] == 2, recovered
        evidence["checks"].append("nonzero-lossy-shell-result-remains-data-not-host-interruption")
        joined = submit("spawn continuation", maximum=4)
        assert joined["content"] == "CHILD_CONTINUATION_JOINED" and Provider.counts["child continuation"] == 2, joined
        with closing(sqlite3.connect(database)) as db:
            rows = [(session_id, json.loads(raw)) for session_id, raw in db.execute("SELECT session_id,message_json FROM shared_history")]
            child_session = next(session_id for session_id, item in rows if item.get("role") == "user" and item.get("content") == "child continuation")
            child_turns = [item for session_id, item in rows if session_id == child_session and item.get("role") == "assistant"]
            assert sorted(item["responses_end_turn"] for item in child_turns) == [False, True], child_turns
        assert Provider.counts["spawn continuation"] + Provider.counts["child continuation"] == 4, Provider.counts
        evidence["checks"].append("child-continuation-persists-turns-under-shared-request-cap")
        host = Host(executable, workspace, database, identifier)
        hosts.append(host)
        start = host.submit("cancel-case", "cancel continuation")
        host.wait("text_delta", "cancel-case", start, timeout=20)
        while not any(event.get("type") == "text_delta" and "WAIT_FOR_CANCEL" in event.get("text", "") for event in host.events[start:]):
            host.wait("text_delta", "cancel-case", len(host.events), timeout=20)
        host.send({"type": "cancel", "id": "cancel-case"})
        cancelled = host.wait("result", "cancel-case", start, timeout=15)
        assert cancelled["code"] == 19 and not cancelled["success"], cancelled
        assert Provider.counts["cancel continuation"] == 2, Provider.counts
        server.cancel_release.set()
        host.stop()
        evidence["checks"].append("cancel-during-continuation-does-not-start-another-request")
        assert not Provider.failures, Provider.failures
        evidence["result"] = "passed"
        evidence["request_counts"] = dict(Provider.counts)
        succeeded = True
    except Exception as error:
        evidence["result"] = "failed"
        evidence["error"] = repr(error)
        raise
    finally:
        server.cancel_release.set()
        for host in hosts:
            if host.process.poll() is None:
                host.abort()
        server.shutdown()
        server.server_close()
        if written:
            assert advapi.CredDeleteW(target, 1, 0), ctypes.get_last_error()
        if succeeded:
            clean_generated_directory(workspace)
        else:
            print(f"failed fixture retained for inspection: {workspace}", file=sys.stderr)
        options.evidence.parent.mkdir(parents=True, exist_ok=True)
        options.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Responses explicit end_turn public acceptance passed")


if __name__ == "__main__":
    main()
