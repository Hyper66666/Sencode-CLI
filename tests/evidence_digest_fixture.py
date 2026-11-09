"""Loopback provider + final host: large child output, evidence pages and restart."""
import argparse
from contextlib import closing
import ctypes
import hashlib
import http.server
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import uuid

from cli_fixture import Credential
from engine_fixture import Host, clean_generated_directory

REPORT = json.dumps(dict(schema=1, outcome="completed", summary="CHILD_LARGE_OK",
    changed_paths=["once.txt"], checks=[], blocker="", next_action=""))


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_): pass

    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = request["messages"]
            child = "You are a level-one child." in messages[0]["content"]
            results = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
            tool = None
            if child:
                self.server.child_requests += 1
                if not results:
                    tool = ("child-output", "run_command", {"shell": "powershell", "timeout_ms": 10000,
                        "command": "[IO.File]::AppendAllText('once.txt','once'); [Console]::Out.Write(('x' * 106138)); exit 0"})
                elif len(results) == 1:
                    projected = results[0]
                    assert projected["content_truncated"] and not projected["is_error"]
                    assert projected["retained_result_bytes"] > 65536
                    assert len(json.dumps(projected).encode()) < 12000
                    self.server.reference = projected["evidence_ref"]
                    tool = ("child-page-0", "read_evidence", dict(self.server.reference, offset=0, limit=16384))
                elif len(results) == 2:
                    page = results[-1]
                    assert page["status"] == "available" and page["offset"] == 0
                    assert page["sha256"] == self.server.reference["sha256"]
                    tool = ("child-page-last", "read_evidence", dict(self.server.reference,
                        offset=page["total_bytes"] - 200, limit=4096))
                else:
                    page = results[-1]
                    assert len(results) == 3 and page["status"] == "available" and page["done"]
                    self.server.child_pages_ok = True
            elif any(m["role"] == "user" and m["content"] == "RESUME_LARGE" for m in messages):
                self.server.resumed = True
                assert any(m["role"] == "tool" and "evidence_ref" in m["content"] for m in messages)
            elif not results:
                tool = ("parent-spawn", "spawn_agent", {"role": "general", "prompt": "Generate fixture output once, read evidence and report."})
            elif any(r.get("status") == "available" and r.get("sha256") == self.server.reference.get("sha256") for r in results):
                self.server.parent_page_ok = True
            else:
                done = next((c for r in results for c in r.get("children", []) if c.get("done")), None)
                if done:
                    assert done["error"] == 0 and done["report"]["valid"]
                    assert done["report"]["summary"] == "CHILD_LARGE_OK"
                    tool = ("parent-page", "read_evidence", dict(self.server.reference, offset=0, limit=4096))
                else:
                    self.server.waits += 1
                    tool = (f"parent-wait-{self.server.waits}", "wait_agents", {"timeout_ms": 1000})
            if tool:
                identifier, name, arguments = tool
                delta = {"tool_calls": [{"index": 0, "id": identifier,
                    "function": {"name": name, "arguments": json.dumps(arguments)}}]}
                finish = "tool_calls"
            else:
                delta = {"content": REPORT if child else ("RESUMED_OK" if self.server.resumed else "PARENT_LARGE_OK")}
                finish = "stop"
            event = {"choices": [{"delta": delta, "finish_reason": finish}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 10}}
            data = ("data: " + json.dumps(event) + "\n\ndata: [DONE]\n\n").encode()
            self.send_response(200); self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(data))); self.send_header("Connection", "close")
            self.end_headers(); self.wfile.write(data)
        except BaseException as error:
            self.server.errors.append(repr(error)); self.send_error(500)
        finally:
            self.close_connection = True


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, required=True); args = parser.parse_args()
    executable = args.executable.resolve(); root = Path(tempfile.mkdtemp(prefix="sencode-evidence-世界-"))
    evidence = {"schema": 1, "scope": "isolated-loopback-final-host-large-child",
        "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(), "checks": []}
    identifier = "custom-digest-" + uuid.uuid4().hex; target = "Sencode/connection/" + identifier
    key = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=key, Persist=1)
    assert advapi.CredWriteW(ctypes.byref(credential), 0)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.errors = []; server.reference = {}; server.waits = 0; server.child_requests = 0
    server.child_pages_ok = False; server.parent_page_ok = False; server.resumed = False
    threading.Thread(target=server.serve_forever, daemon=True).start()
    hosts = []; success = False; database = root / "isolated.sqlite3"
    try:
        bootstrap = Host(executable, root, database, ""); hosts.append(bootstrap); bootstrap.stop()
        config = dict(version=2, baseUrl=f"http://127.0.0.1:{server.server_port}/v1",
            protocol="chatCompletions", credentialRef=target, selectedModelId="fixture",
            enabledModels=[{"id": "fixture"}])
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda k: "fixture" if k == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Fixture',?,'fixture',1,1)", (identifier, json.dumps(config))); db.commit()
        host = Host(executable, root, database, identifier); hosts.append(host)
        start = host.submit("large", "PARENT_LARGE", allow_commands=True)
        result = host.wait("result", "large", start, timeout=45)
        assert result["success"] and result["content"] == "PARENT_LARGE_OK", result
        assert server.child_pages_ok and server.parent_page_ok and server.child_requests == 4
        with closing(sqlite3.connect(database)) as db:
            raw = db.execute("SELECT result FROM shared_tool_ledger WHERE call_id='child-output' AND session_id=? AND state='complete'", (server.reference["session_id"],)).fetchone()[0]
            digest = hashlib.sha256(raw.encode()).hexdigest()
            assert digest == server.reference["sha256"] and len(raw.encode()) > 65536
            original = json.loads(json.loads(raw)["content"])
            assert original["stdout"] == "x" * 106138 and original["exit_code"] == 0
            assert db.execute("SELECT active,cleanup_required FROM shared_executions WHERE session_id=?", (server.reference["session_id"],)).fetchone() == (0, 0)
        assert (root / "once.txt").read_text(encoding="utf-8") == "once"
        evidence["checks"] += ["large-child-output-projected-with-full-source-digest", "child-first-and-last-pages", "parent-authorized-child-evidence", "successful-child-and-parent-complete"]
        host.stop()
        resumed = Host(executable, root, database, identifier, host.session); hosts.append(resumed)
        start = resumed.submit("resumed", "RESUME_LARGE", allow_commands=True)
        restored = resumed.wait("result", "resumed", start, timeout=20)
        assert restored["success"] and restored["content"] == "RESUMED_OK", restored
        assert (root / "once.txt").read_text(encoding="utf-8") == "once" and server.child_requests == 4
        assert not server.errors
        resumed.stop(); evidence["checks"].append("restart-projects-history-without-replaying-command")
        evidence["result"] = "passed"; evidence["retained_result_bytes"] = len(raw.encode()); success = True
    except BaseException as error:
        evidence["result"] = "failed"; evidence["error"] = repr(error); raise
    finally:
        for host in hosts:
            if host.process.poll() is None: host.stop()
        server.shutdown(); server.server_close(); advapi.CredDeleteW(target, 1, 0)
        evidence["provider_errors"] = server.errors
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        if success: clean_generated_directory(root)
    print("Large child evidence, exact SHA256 pages, parent continuation and restart without command replay passed")


if __name__ == "__main__": main()
