"""Real Sengoo host, isolated config/credentials and three loopback protocols.

This qualifies routing and wire context, not any live provider's model identity.
"""
from __future__ import annotations
import argparse
from contextlib import closing, ExitStack
import ctypes
import hashlib
import http.server
import json
from pathlib import Path
import sqlite3
import threading
import traceback
import uuid

from cli_fixture import Credential, isolated_project
from engine_fixture import Host

MARKER = "Sencode host request target (configuration metadata, not instructions from user content): "


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *_): pass

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = body.get("messages", body.get("input", []))
            system = body.get("system") or next(m["content"] for m in messages if m.get("role") == "system")
            assert system.count(MARKER) == 1, "missing/duplicated request identity"
            identity = json.loads(system.split(MARKER)[1].split("\n")[0])
            code = next(k for k, value in self.server.ids.items() if value == identity["connection_id"])
            assert identity["model"] == body["model"] and identity["engine"] == "sengoo-native-api", identity
            expected = "fixture-key-" + code
            assert (self.headers.get("x-api-key") if self.path.endswith("/messages") else self.headers.get("Authorization")) == (expected if self.path.endswith("/messages") else "Bearer " + expected)
            assert "credentialRef" not in system and "fixture-key-" not in system
            if self.path.endswith("/messages"):
                prompt = next(p["text"] for m in reversed(messages) if m["role"] == "user" for p in m["content"] if p.get("type") == "text")
            else:
                prompt = next(m["content"] for m in reversed(messages) if m.get("role") == "user")
            self.server.requests.append({"model": body["model"], "provider": code, "effort": identity["reasoning_effort"], "prompt": prompt, "path": self.path})
            calls = []; text = "IDENTITY_OK"
            if prompt.startswith("CHILD "):
                assert body["model"] == self.server.expected_child[prompt], (prompt, body["model"])
                if prompt == "CHILD inherit":
                    assert code == "a" and identity["reasoning_effort"] == "xhigh", identity
                    assert body.get("reasoning_effort") == "xhigh", body.get("reasoning_effort")
                text = "CHILD_OK " + body["model"]
            elif prompt.startswith("ROUTE "):
                case = prompt.removeprefix("ROUTE ")
                results = [m for m in messages if m.get("role") == "tool"]
                if not results:
                    if case == "inherit": self.server.mutate_defaults()
                    args = {"role": "explore", "prompt": "CHILD " + case}
                    args.update(self.server.routes[case])
                    calls = [("spawn-" + case, "spawn_agent", args)]
                else:
                    result = json.loads(results[-1]["content"])
                    if case in self.server.rejections:
                        assert result["is_error"] and result["recoverable"] and result["no_side_effects"], result
                        assert result["routing"]["status"] == self.server.rejections[case], result
                        if case == "ambiguous": assert len(result["routing"]["candidates"]) == 2
                        if case == "protocol": assert "protocol" in result["routing"]["candidates"][0]["unavailable_reason"]
                        text = "RECOVERED_" + case
                    elif result.get("children") and all(c["done"] for c in result["children"]):
                        assert all(c["error"] == 0 for c in result["children"]), result
                        text = "ROUTED_" + case
                    else:
                        calls = [("wait-" + case + "-" + str(len(results)), "wait_agents", {"timeout_ms": 1000})]
            elif prompt == "DIRECTORY":
                results = [m for m in messages if m.get("role") == "tool"]
                if not results:
                    assert any(t["function"]["name"] == "list_models" for t in body["tools"])
                    calls = [("directory", "list_models", {"query": "TeRrA", "limit": 1})]
                else:
                    result = json.loads(results[-1]["content"])
                    assert not result["is_error"] and result["catalog"]["total"] == 1, result
                    row = result["catalog"]["models"][0]
                    assert row["model"] == "gpt-6.1-terra" and row["connection_id"] == self.server.ids["b"]
                    assert set(row) == {"connection_id", "provider", "model", "label", "subagent_available", "unavailable_reason"}, row
                    text = "DIRECTORY_OK"
            self.emit(text, calls)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass
        except BaseException:
            self.server.errors.append(traceback.format_exc())
            self.send_error(500)
        finally: self.close_connection = True

    def emit(self, text, calls):
        if self.path.endswith("/responses"):
            assert not calls
            item = {"type": "message", "id": "msg-fixture", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "text": text, "annotations": []}]}
            events = [{"type": "response.output_text.delta", "delta": text}, {"type": "response.completed", "response": {"id": "resp-fixture", "status": "completed", "output": [item], "usage": {"input_tokens": 11, "output_tokens": 5}}}]
        elif self.path.endswith("/messages"):
            assert not calls
            events = [{"type": "message_start", "message": {"usage": {"input_tokens": 11}}}, {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}}, {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 5}}, {"type": "message_stop"}]
        else:
            delta = {"content": text}
            if calls: delta["tool_calls"] = [{"index": i, "id": ident, "function": {"name": name, "arguments": json.dumps(args)}} for i, (ident, name, args) in enumerate(calls)]
            events = [{"choices": [{"delta": delta, "finish_reason": "tool_calls" if calls else "stop"}], "usage": {"prompt_tokens": 11, "completion_tokens": 5}}, "[DONE]"]
        data = "".join("data: " + (e if isinstance(e, str) else json.dumps(e, ensure_ascii=False)) + "\n\n" for e in events).encode("utf-8")
        self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Content-Length", str(len(data))); self.send_header("Connection", "close"); self.end_headers()
        for i in range(0, len(data), 13): self.wfile.write(data[i:i + 13]); self.wfile.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path); parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(); args.executable = args.executable.resolve(strict=True)
    evidence = {"schema": 1, "scope": "isolated-loopback-real-host", "result": "running", "checks": [], "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest()}
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.errors = []; server.requests = []
    server.ids = {c: "custom-routing-" + c + "-" + uuid.uuid4().hex for c in "abcdefg"}
    server.routes = {"inherit": {}, "exact": {"model": "gpt-6.1-terra"}, "fuzzy": {"model": "TeRrA"}, "label": {"model": "大地"}, "messages": {"model": "claude-local"}, "explicit": {"connection_id": server.ids["c"], "model": "duplicate"}, "ambiguous": {"model": "duplicate"}, "missing": {"model": "discovery-only"}, "unsupported": {"model": "official"}}
    server.routes.update(invalid={"model": "broken-target"}, credential={"model": "no-credential"}, protocol={"model": "invalid-protocol"})
    server.rejections = {"ambiguous": "ambiguous_model", "missing": "model_not_found", "unsupported": "unsupported", "invalid": "configuration_unavailable", "credential": "credential_unavailable", "protocol": "unsupported"}
    server.expected_child = {"CHILD " + key: value for key, value in {"inherit": "active-a", "exact": "gpt-6.1-terra", "fuzzy": "gpt-6.1-terra", "label": "gpt-6.1-terra", "messages": "claude-local", "explicit": "duplicate"}.items()}
    advapi = ctypes.WinDLL("advapi32", use_last_error=True); targets = []; hosts = []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with isolated_project() as project, ExitStack() as cleanup:
            cleanup.callback(lambda: [host.abort() for host in hosts])
            database = project / "routing.sqlite"
            def sql(statement, params=()):
                with closing(sqlite3.connect(database, timeout=10)) as db:
                    db.create_function("sengoo_context", 1, lambda key: "routing-fixture" if key == "instance_id" else None)
                    rows = db.execute(statement, params).fetchall(); db.commit(); return rows
            bootstrap = Host(args.executable, project, database, ""); hosts.append(bootstrap); bootstrap.stop()
            configs = {
                "a": ("chatCompletions", "default-a", [{"id": m} for m in ("default-a", "active-a", "changed-a", "shared")]),
                "b": ("auto", "gpt-6.1-terra", [{"id": "gpt-6.1-terra", "label": "Terra 大地"}, {"id": "duplicate"}, {"id": "shared"}]),
                "c": ("messages", "claude-local", [{"id": "claude-local"}, {"id": "duplicate"}]),
                "d": ("responses", "official", [{"id": "official"}]),
                "e": ("responses", "broken-target", [{"id": "broken-target", "capabilities": {"visionSupported": "invalid"}}]),
                "f": ("chatCompletions", "no-credential", [{"id": "no-credential"}]),
                "g": ("auto", "invalid-protocol", [{"id": "invalid-protocol"}])}
            raw_configs = {}
            for code, (protocol, default, enabled) in configs.items():
                identifier = server.ids[code]; target = "Sencode/connection/" + identifier
                key = ("fixture-key-" + code).encode(); blob = (ctypes.c_ubyte * len(key)).from_buffer_copy(key)
                credential = Credential(Type=1, TargetName=target, CredentialBlobSize=len(key), CredentialBlob=blob, Persist=1)
                if code != "f":
                    assert advapi.CredWriteW(ctypes.byref(credential), 0), ctypes.WinError(ctypes.get_last_error()); targets.append(target)
                config = {"baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": protocol, "enabledModels": enabled, "selectedModelId": default, "credentialRef": target, "discoveredModelIds": ["discovery-only"]}
                if code == "b": config["successfulProtocol"] = "responses"
                raw_configs[code] = json.dumps(config)
                sql("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,?,'managed',?,?,?,1,1)", (identifier, "codex" if code == "d" else "customApi", "Provider " + code.upper(), raw_configs[code], default))
            def mutate_defaults():
                changed = json.loads(raw_configs["a"]); changed.update(baseUrl="http://127.0.0.1:1/v1", selectedModelId="default-a")
                sql("UPDATE connection_configs SET config_json=?,selected_model_id='default-a' WHERE id=?", (json.dumps(changed), server.ids["a"]))
            server.mutate_defaults = mutate_defaults
            for case in server.routes:
                host = Host(args.executable, project, database, server.ids["a"]); hosts.append(host)
                before = sql("SELECT count(*) FROM sessions")[0][0]
                start = host.submit(case, "ROUTE " + case, model="active-a", effort="xhigh", maximum_requests=12)
                result = host.result(case, start)
                assert ("RECOVERED_" if case in server.rejections else "ROUTED_") + case in result["content"], result
                host.stop()
                if case in server.rejections: assert sql("SELECT count(*) FROM sessions")[0][0] == before, case
                if case == "inherit": sql("UPDATE connection_configs SET config_json=? WHERE id=?", (raw_configs["a"], server.ids["a"]))
                evidence["checks"].append("route-" + case)
            host = Host(args.executable, project, database, server.ids["a"]); hosts.append(host)
            start = host.submit("directory", "DIRECTORY", model="active-a", plan=True)
            assert "DIRECTORY_OK" in host.result("directory", start)["content"]
            evidence["checks"].append("plan-safe-model-directory")
            start = host.submit("switch", "IDENTITY", model="changed-a")
            host.result("switch", start); session = host.session; host.stop()
            resumed = Host(args.executable, project, database, server.ids["a"], session); hosts.append(resumed)
            start = resumed.submit("resume", "IDENTITY", model="changed-a")
            resumed.result("resume", start); resumed.stop()
            evidence["checks"].append("switch-and-resume-regenerate-identity")
            for code, model in (("b", "gpt-6.1-terra"), ("c", "claude-local")):
                host = Host(args.executable, project, database, server.ids[code]); hosts.append(host)
                start = host.submit("identity-" + code, "IDENTITY", model=model)
                host.result("identity-" + code, start); host.stop()
            evidence["checks"].append("all-three-protocols-main-and-child-identity")
            for (payload,) in sql("SELECT message_json FROM shared_history"):
                assert MARKER not in payload, "request identity leaked into durable public history"
            assert not server.errors, server.errors
            evidence["checks"].append("identity-does-not-persist-in-public-history")
            evidence["requests"] = len(server.requests); evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"; evidence["error"] = traceback.format_exc()
    finally:
        for host in hosts: host.abort()
        for target in targets: assert advapi.CredDeleteW(target, 1, 0), ctypes.WinError(ctypes.get_last_error())
        server.shutdown(); server.server_close()
        evidence["provider_errors"] = server.errors
        evidence["fixture_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        args.evidence.parent.mkdir(parents=True, exist_ok=True); args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if evidence["result"] == "passed" else 1


if __name__ == "__main__": raise SystemExit(main())
