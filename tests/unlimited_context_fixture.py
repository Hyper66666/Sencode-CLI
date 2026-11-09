"""Final native host: >50 tool turns, automatic compaction and old Goal recovery."""
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

SUMMARY = (
    "1. Goal and scope: inspect fixture.txt repeatedly in this isolated workspace. "
    "2. Decisions: read only, preserve complete tool pairs and current user instructions. "
    "3. Files: fixture.txt contains synthetic Chinese text and stable content. "
    "4. Evidence: preceding read_file results succeeded; no files were modified. "
    "5. Open issues: none; continue until the provider's final completion. "
    "6. Next step: retain latest tool call identifiers and do not replay completed calls. "
    "7. Attribution and resources: synthetic loopback model, no user data, "
    "shared request counters include every compaction request. "
) * 2


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    reads = 0
    summaries = 0
    errors = []

    def log_message(self, *_): pass

    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = request["messages"]
            if messages[0]["content"].startswith("You summarize coding sessions"):
                type(self).summaries += 1
                assert not request.get("tools"), "summary must not execute tools"
                event = {"choices": [{"delta": {"content": SUMMARY}, "finish_reason": "stop"}]}
            elif self.reads < 60:
                type(self).reads += 1
                event = {"choices": [{"delta": {"tool_calls": [{"index": 0,
                    "id": f"read-{self.reads}", "function": {"name": "read_file",
                    "arguments": json.dumps({"path": "fixture.txt"})}}]}, "finish_reason": "tool_calls"}]}
            else:
                event = {"choices": [{"delta": {"content": "UNLIMITED_FINISHED"}, "finish_reason": "stop"}]}
            event["usage"] = {"prompt_tokens": 100, "completion_tokens": 10}
            data = ("data: " + json.dumps(event) + "\n\ndata: [DONE]\n\n").encode()
            self.send_response(200); self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(data))); self.send_header("Connection", "close")
            self.end_headers(); self.wfile.write(data)
        except BaseException as error:
            self.errors.append(type(error).__name__)
            self.send_error(500)
        finally: self.close_connection = True


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, required=True); args = parser.parse_args()
    executable = args.executable.resolve(); root = Path(tempfile.mkdtemp(prefix="sencode-unlimited-"))
    evidence = {"schema": 1, "scope": "isolated-loopback-final-host",
                "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(), "checks": []}
    identifier = "custom-unlimited-" + uuid.uuid4().hex; target = "Sencode/connection/" + identifier
    key = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=key, Persist=1)
    assert advapi.CredWriteW(ctypes.byref(credential), 0)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    hosts = []; success = False; database = root / "isolated.sqlite3"
    try:
        bootstrap = Host(executable, root, database, ""); hosts.append(bootstrap); bootstrap.stop()
        (root / "fixture.txt").write_text("fixture 世界 é\n" * 80, encoding="utf-8")
        (root / ".sencode").mkdir(exist_ok=True)
        (root / ".sencode" / "context.json").write_text(json.dumps({"schema": 1,
            "context_window_tokens": 14000, "max_input_bytes": 28000,
            "threshold_percent": 80, "min_summary_chars": 100}), encoding="utf-8")
        config = dict(version=2, baseUrl=f"http://127.0.0.1:{server.server_port}/v1",
            protocol="chatCompletions", credentialRef=target, selectedModelId="fixture",
            enabledModels=[{"id": "fixture"}])
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda k: "fixture" if k == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Fixture',?,'fixture',1,1)", (identifier, json.dumps(config))); db.commit()
        host = Host(executable, root, database, identifier); hosts.append(host)
        start = host.submit("unlimited", "Read the synthetic fixture until done")
        result = host.wait("result", "unlimited", start, timeout=90)
        assert result["success"] and result["content"] == "UNLIMITED_FINISHED", result
        assert Provider.reads == 60 and Provider.summaries >= 2
        with closing(sqlite3.connect(database)) as db:
            mode = json.loads(db.execute("SELECT mode_json FROM shared_modes WHERE session_id=?", (host.session,)).fetchone()[0])
            ledger = db.execute("SELECT count(*) FROM shared_tool_ledger WHERE session_id=? AND state='complete'", (host.session,)).fetchone()[0]
            assert ledger == 60 and mode["context"]["schema"] == 2
            assert len(mode["request_attempts"]["attempts"]) == 61 + Provider.summaries
            # Legacy default cap was stored without explicit-limit provenance.
            mode["goal"] = dict(objective="legacy goal", requests=75, max_requests=50,
                tokens=1234, token_budget=0, status=3, checks=[], same_failure_count=0)
            db.create_function("sengoo_context", 1, lambda k: "fixture" if k == "instance_id" else None)
            db.execute("UPDATE shared_modes SET mode_json=? WHERE session_id=?", (json.dumps(mode), host.session)); db.commit()
        evidence["checks"].extend(["default-host-past-50-requests", "60-completed-read-tools-once",
            "repeated-auto-compaction-continues", "request-summary-usage-counts-preserved"])
        host.stop()
        resumed = Host(executable, root, database, identifier, host.session); hosts.append(resumed)
        start = resumed.submit("legacy", "Continue saved goal without a request cap", goal="legacy goal")
        # A Goal asks for acceptance after an ordinary answer; bound this test
        # by explicitly cancelling after its first accepted continued request.
        resumed.wait("request_completed", "legacy", start, timeout=20)
        resumed.send({"type": "cancel", "id": "legacy"})
        resumed.wait("result", "legacy", start, timeout=20)
        with closing(sqlite3.connect(database)) as db:
            mode = json.loads(db.execute("SELECT mode_json FROM shared_modes WHERE session_id=?", (host.session,)).fetchone()[0])
            assert mode["goal"]["requests"] > 75 and mode["goal"]["max_requests"] == 0
            assert mode["goal"]["tokens"] >= 1234 and not mode["goal"]["request_limit_explicit"]
        evidence["checks"].append("old-default-goal-cap-removed-without-resetting-usage")
        assert not Provider.errors, Provider.errors
        evidence["result"] = "passed"; evidence["read_tools"] = Provider.reads; evidence["summaries"] = Provider.summaries
        success = True
    except BaseException as error:
        evidence["result"] = "failed"; evidence["error"] = repr(error); raise
    finally:
        for host in hosts:
            if host.process.poll() is None: host.stop()
        server.shutdown(); server.server_close(); advapi.CredDeleteW(target, 1, 0)
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        if success: clean_generated_directory(root)
    print("Unlimited native requests, compaction and legacy Goal recovery passed")


if __name__ == "__main__": main()
