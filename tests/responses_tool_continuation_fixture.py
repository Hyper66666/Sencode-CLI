"""Real CLI / loopback Responses continuation; private DB and credential only."""
import argparse
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
import uuid

from cli_fixture import Credential
from engine_fixture import clean_generated_directory


def reasoning(n):
    return {"id": f"rs-{n}", "type": "reasoning", "summary": [],
            "encrypted_content": f"opaque-fixture-{n}-世界", "status": "completed"}


def message(n, text, phase):
    return {"id": f"msg-{n}", "type": "message", "role": "assistant",
            "status": "completed", "phase": phase,
            "content": [{"type": "output_text", "text": text, "annotations": []}]}


def call(n, name, arguments):
    return {"id": f"fc-{n}", "type": "function_call", "call_id": f"call-{n}",
            "name": name, "arguments": json.dumps(arguments, ensure_ascii=False),
            "status": "completed"}


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    requests = []
    failures = []
    snapshots = {}

    def log_message(self, *_):
        pass

    def emit(self, items):
        events = []
        for index, item in enumerate(items):
            added = dict(item)
            if item["type"] == "reasoning":
                added.pop("encrypted_content", None)
                added["status"] = "in_progress"
            elif item["type"] == "function_call":
                added["arguments"] = ""
                added["status"] = "in_progress"
            elif item["type"] == "message":
                added["content"] = []
                added["status"] = "in_progress"
            events.append({"type": "response.output_item.added", "output_index": index, "item": added})
            if item["type"] == "function_call":
                args = item["arguments"]
                split = len(args) // 2
                for part in (args[:split], args[split:]):
                    events.append({"type": "response.function_call_arguments.delta", "output_index": index,
                                   "item_id": item["id"], "delta": part})
            elif item["type"] == "message":
                events.append({"type": "response.output_text.delta", "output_index": index,
                               "item_id": item["id"], "content_index": 0,
                               "delta": item["content"][0]["text"]})
            events.append({"type": "response.output_item.done", "output_index": index, "item": item})
        events.append({"type": "response.completed", "response": {"id": "response-fixture",
                       "status": "completed", "output": items,
                       "usage": {"input_tokens": 31, "output_tokens": 14,
                                 "attribution": {"items": {
                                     f"historical-{i}": {"input_tokens": i, "output_tokens": 0,
                                         "cached_tokens": 0, "cache_write_tokens": 0,
                                         "content": [{"input_tokens": i, "output_tokens": 0}]}
                                     for i in range(600)}}}}})
        data = "".join("data: " + json.dumps(e, ensure_ascii=False) + "\n\n" for e in events).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            for start in range(0, len(data), 7):
                self.wfile.write(data[start:start + 7])
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        self.close_connection = True

    def require_items(self, body, items):
        actual = body["input"]
        positions = []
        for item in items:
            matches = [i for i, value in enumerate(actual) if value.get("id") == item["id"]]
            assert len(matches) == 1, (item["id"], actual)
            seen = actual[matches[0]]
            # Runtime-only status may be omitted by a typed input projection;
            # identifiers, phase, encrypted bytes and content remain exact.
            for key, value in item.items():
                if key != "status":
                    assert seen.get(key) == value, (key, seen, value)
            positions.append(matches[0])
        assert positions == sorted(positions), positions
        assert len([v for v in actual if v.get("type") == "function_call"]) == len(
            {v["call_id"] for v in actual if v.get("type") == "function_call"}), actual

    def do_POST(self):
        try:
            assert self.path == "/v1/responses", self.path
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.requests.append(body)
            assert body.get("store") is False, "stateless history must request replayable reasoning"
            inputs = body["input"]
            tools = {v["call_id"]: v for v in inputs if v.get("type") == "function_call_output"}
            users = [v.get("content", "") for v in inputs if v.get("role") == "user"]
            latest = users[-1]
            if latest in {"cross-model reasoning", "cross-connection reasoning"}:
                assert not any(v.get("type") == "reasoning" or "encrypted_content" in v or "phase" in v for v in inputs), inputs
                assert not any(v.get("id") for v in inputs), inputs
                assert any("owned fixture 世界" in v.get("output", "") for v in inputs if v.get("type") == "function_call_output"), inputs
                self.emit([message("bridge", "public history bridge verified", "final_answer")])
                return
            if latest == "malformed item":
                invalid = reasoning("bad")
                invalid["id"] = "bad\x00hidden"
                self.emit([invalid, call("bad", "write_file", {"path": "must-not-write.txt", "content": "forbidden"})])
                return
            if latest == "resume reasoning":
                self.require_items(body, self.snapshots["first"] + self.snapshots["second"] + self.snapshots["final"])
                if "call-3" not in tools:
                    items = [reasoning(3), call(3, "read_file", {"path": "source.txt"})]
                    self.snapshots["resume"] = items
                    self.emit(items)
                    return
                self.require_items(body, self.snapshots["resume"])
                assert "owned fixture 世界" in tools["call-3"]["output"]
                self.emit([message(4, "resume verified 世界", "final_answer")])
                return
            assert latest == "inspect reasoning", latest
            if "call-1" not in tools:
                # Message precedes reasoning deliberately: replay must retain
                # the provider output order rather than moving reasoning first.
                items = [message(1, "我先检查文件。", "commentary"), reasoning(1),
                         call(1, "read_file", {"path": "source.txt"})]
                self.snapshots["first"] = items
                self.emit(items)
                return
            self.require_items(body, self.snapshots["first"])
            assert "owned fixture 世界" in tools["call-1"]["output"]
            if "call-2" not in tools:
                items = [reasoning(2), call(2, "run_command", {
                    "command": "printf '%s' 'bash 世界'; printf '%s' 'bash stderr' >&2; test -f source.txt"})]
                self.snapshots["second"] = items
                self.emit(items)
                return
            self.require_items(body, self.snapshots["second"])
            result = json.loads(tools["call-2"]["output"])
            assert not result["is_error"], result
            output = json.loads(result["content"])
            assert output["exit_code"] == 0 and output["stdout"] == "bash 世界" and output["stderr"] == "bash stderr", output
            assert output.get("shell", result.get("shell")) == "bash", result
            items = [message(3, "tool continuation verified 世界", "final_answer")]
            self.snapshots["final"] = items
            self.emit(items)
        except Exception as error:
            self.failures.append(repr(error))
            self.send_error(400, "fixture assertion failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    identifier = "custom-responses-" + uuid.uuid4().hex
    target = "Sencode/connection/" + identifier
    key = (ctypes.c_ubyte * len(b"fixture-key")).from_buffer_copy(b"fixture-key")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    written_targets = []
    evidence = {"schema": 1, "result": "running", "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(), "checks": []}
    root = Path(tempfile.mkdtemp(prefix="sencode-responses-中文-")).resolve()
    succeeded = False
    try:
        for credential_target in (target, target + "-other"):
            credential = Credential(Type=1, TargetName=credential_target, CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
            if not advapi.CredWriteW(ctypes.byref(credential), 0):
                raise ctypes.WinError(ctypes.get_last_error())
            written_targets.append(credential_target)
        database = root / "isolated.sqlite3"
        (root / "source.txt").write_text("owned fixture 世界\n", encoding="utf-8")
        base = [str(executable), "--cwd", str(root), "--database", str(database)]
        init = subprocess.run(base + ["doctor"], cwd=root, capture_output=True, timeout=20)
        assert init.returncode == 0, init.stderr
        config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "responses",
                  "successfulProtocol": "responses", "credentialRef": target, "selectedModelId": "fixture",
                  "enabledModels": [{"id": "fixture"}, {"id": "other"}]}
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "fixture" if key == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Responses fixture',?,'fixture',1,1)",
                       (identifier, json.dumps(config)))
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Other connection fixture',?,'fixture',1,1)",
                       (identifier + "-other", json.dumps(dict(config, credentialRef=target + "-other"))))
            db.commit()

        def run(*arguments, expected=0, connection=identifier):
            result = subprocess.run(base + ["--connection", connection, *arguments, "--output-format", "json"],
                                    cwd=root, capture_output=True, encoding="utf-8", timeout=45)
            assert result.returncode == expected, (result.stdout, result.stderr, Provider.failures)
            return json.loads(result.stdout.strip().splitlines()[-1])

        first = run("--allow-commands", "-p", "inspect reasoning")
        assert first["success"] and first["content"] == "tool continuation verified 世界", first
        assert len(Provider.requests) == 3, "rich valid metadata must not cause retries"
        evidence["checks"].extend(["fragmented-reasoning-tool-round-trip", "provider-order-and-assistant-phase", "default-git-bash-stdout-stderr-cwd", "completion-usage-metadata-over-4096-nodes"])
        resumed = run("resume", first["session_id"], "-p", "resume reasoning")
        assert resumed["success"] and resumed["session_id"] == first["session_id"] and resumed["content"] == "resume verified 世界", resumed
        assert len(Provider.requests) == 5, "resumed rich completion must not cause retries"
        evidence["checks"].append("restart-persists-encrypted-output-and-phase")
        bridged = run("resume", first["session_id"], "-p", "cross-connection reasoning", connection=identifier + "-other")
        assert bridged["success"] and bridged["content"] == "public history bridge verified", bridged
        evidence["checks"].append("connection-switch-rebuilds-public-history-without-opaque-items")
        bridged = run("resume", first["session_id"], "--model", "other", "-p", "cross-model reasoning")
        assert bridged["success"] and bridged["content"] == "public history bridge verified", bridged
        evidence["checks"].append("model-switch-rebuilds-public-history-without-opaque-items")
        bad = run("--auto-edit", "-p", "malformed item", expected=1)
        assert not bad["success"] and not (root / "must-not-write.txt").exists(), bad
        evidence["checks"].append("invalid-item-refuses-tools-before-side-effects")
        assert not Provider.failures, Provider.failures
        with closing(sqlite3.connect(database)) as db:
            count = db.execute("SELECT count(*) FROM shared_tool_ledger WHERE state='complete'").fetchone()[0]
            assert count == 3, count
        evidence["checks"].append("three-tools-execute-once")
        evidence["result"] = "passed"
        evidence["requests"] = len(Provider.requests)
        succeeded = True
    except Exception as error:
        evidence["result"] = "failed"
        evidence["error"] = repr(error)
        raise
    finally:
        server.shutdown()
        server.server_close()
        for credential_target in written_targets:
            advapi.CredDeleteW(credential_target, 1, 0)
        if succeeded:
            clean_generated_directory(root)
        else:
            print(f"failed fixture retained for inspection: {root}", file=sys.stderr)
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Responses reasoning tools / Bash / restart acceptance passed")


if __name__ == "__main__":
    main()
