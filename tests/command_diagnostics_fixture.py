"""Final CLI, isolated loopback provider: shell boundaries and lifecycle results."""
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


COMMANDS = {
    "script": {"shell": "powershell", "timeout_ms": 10000,
        "command": "Get-Content -LiteralPath fixture.txt\n[Console]::Error.Write('later-command failure 世界'); exit 7"},
    "rg": {"shell": "powershell", "timeout_ms": 10000,
        "command": "rg -n needle fixture.txt"},
    "bash": {"timeout_ms": 10000, "command": "printf 'default-bash-世界'"},
    "descendant": {"shell": "powershell", "timeout_ms": 3000,
        "command": "Start-Process -FilePath $env:ComSpec -ArgumentList '/d /c ping.exe -n 21 127.0.0.1 >nul' -WindowStyle Hidden; [Console]::Out.Write('parent-finished'); exit 0"},
}


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    errors = []
    results = {}
    requests = []

    def log_message(self, *_): pass

    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = request["messages"]
            last_user = max(i for i, m in enumerate(messages) if m["role"] == "user")
            case = messages[last_user]["content"]
            self.requests.append(case)
            results = [m for m in messages[last_user + 1:] if m["role"] == "tool"]
            if not results:
                delta = {"tool_calls": [{"index": 0, "id": "command-" + case,
                    "function": {"name": "run_command", "arguments": json.dumps(COMMANDS[case])}}]}
                finish = "tool_calls"
            else:
                assert len(results) == 1, "completed commands were replayed"
                result = json.loads(results[0]["content"])
                body = json.loads(result["content"])
                self.results[case] = result
                if case == "script":
                    assert body["exit_code"] == 7 and not body["timed_out"]
                    assert body["stderr"] == "later-command failure 世界" and "needle" in body["stdout"]
                elif case == "rg":
                    assert body["exit_code"] == 0 and not body["timed_out"] and "1:needle" in body["stdout"]
                    assert "runtime mode" not in body["stderr"]
                elif case == "bash":
                    assert body["stdout"] == "default-bash-世界" and body["exit_code"] == 0
                elif case == "descendant":
                    assert body["exit_code"] == 0 and body["timed_out"]
                    assert body["termination_reason"] == "timeout_descendants" and body["timeout_ms"] == 3000
                delta = {"content": "CORRECTED_" + case}
                finish = "stop"
            event = {"choices": [{"delta": delta, "finish_reason": finish}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 10}}
            data = ("data: " + json.dumps(event) + "\n\ndata: [DONE]\n\n").encode()
            self.send_response(200); self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(data))); self.send_header("Connection", "close")
            self.end_headers(); self.wfile.write(data)
        except BaseException as error:
            self.errors.append(repr(error)); self.send_error(500)
        finally:
            self.close_connection = True


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, required=True); args = parser.parse_args()
    executable = args.executable.resolve()
    root = Path(tempfile.mkdtemp(prefix="sencode-command-世界-"))
    evidence = {"schema": 1, "scope": "isolated-loopback-final-cli-real-shells",
        "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(), "checks": []}
    identifier = "custom-command-" + uuid.uuid4().hex; target = "Sencode/connection/" + identifier
    key = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=key, Persist=1)
    assert advapi.CredWriteW(ctypes.byref(credential), 0)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    hosts = []; success = False; database = root / "isolated.sqlite3"
    try:
        bootstrap = Host(executable, root, database, ""); hosts.append(bootstrap); bootstrap.stop()
        (root / "fixture.txt").write_text("needle 世界\n", encoding="utf-8")
        config = dict(version=2, baseUrl=f"http://127.0.0.1:{server.server_port}/v1",
            protocol="chatCompletions", credentialRef=target, selectedModelId="fixture",
            enabledModels=[{"id": "fixture"}])
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda k: "fixture" if k == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Fixture',?,'fixture',1,1)", (identifier, json.dumps(config))); db.commit()
        host = Host(executable, root, database, identifier); hosts.append(host)
        for case in COMMANDS:
            start = host.submit(case, case, allow_commands=True)
            result = host.wait("result", case, start, timeout=30)
            assert result["success"] and result["content"] == "CORRECTED_" + case, result
            evidence["checks"].append(case + "-attributed-and-returned-to-model")
        with closing(sqlite3.connect(database)) as db:
            rows = db.execute("SELECT call_id,state,result FROM shared_tool_ledger WHERE session_id=? ORDER BY call_id", (host.session,)).fetchall()
            assert len(rows) == len(COMMANDS)
            assert all(state == "complete" and json.loads(raw) == Provider.results[call.removeprefix("command-")] for call, state, raw in rows)
        assert len(Provider.requests) == 2 * len(COMMANDS) and not Provider.errors
        host.stop(); evidence["checks"].append("exactly-once-durable-results-and-clean-host-shutdown")
        evidence["result"] = "passed"; success = True
    except BaseException as error:
        evidence["result"] = "failed"; evidence["error"] = repr(error); raise
    finally:
        for host in hosts:
            if host.process.poll() is None: host.stop()
        server.shutdown(); server.server_close(); advapi.CredDeleteW(target, 1, 0)
        evidence["provider_errors"] = Provider.errors
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        if success: clean_generated_directory(root)
    print("Command diagnostics: real PowerShell/Bash/rg, descendant cleanup, model correction and exact-once ledger passed")


if __name__ == "__main__": main()
