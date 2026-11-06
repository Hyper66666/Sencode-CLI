"""Installed native run_command with bundled ripgrep and System32-only PATH.

Uses a fresh catalog, temporary credential, disposable files and a loopback
provider. No user configuration, external API or compiler is used by the CLI.
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
import traceback
import uuid

from agent_reliability_fixture import Provider as BaseProvider
from cli_fixture import Credential
from tui_console_fixture import checked, environment_for, remove_owned_tree, write_json


class Provider(BaseProvider):
    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = body["messages"]
            latest = max(i for i, message in enumerate(messages) if message["role"] == "user")
            prompt = messages[latest]["content"]
            case = self.server.cases[prompt]
            results = [message for message in messages[latest + 1:] if message["role"] == "tool"]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            if not results:
                self.event(tool=(prompt.replace(" ", "-"), "run_command", {
                    "command": case["command"], "shell": case["shell"], "timeout_ms": 15000}))
            else:
                assert len(results) == 1, results
                value = json.loads(results[0]["content"])
                details = json.loads(value["content"])
                assert details["exit_code"] == case["exit"], details
                assert not details["timed_out"] and not details["cancelled"], details
                assert not details["stderr"].strip(), details
                assert case["expect"] in details["stdout"], details
                assert value["is_error"] == (case["exit"] != 0), value
                self.server.results[prompt] = details
                self.event("SEARCH_VERIFIED", done=True)
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except BaseException:
            self.server.errors.append(traceback.format_exc())
        finally:
            self.close_connection = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    bundled = executable.parent / "rg.exe"
    assert bundled.is_file(), "Test the complete installed package, including rg.exe"
    assert hashlib.sha256(bundled.read_bytes()).hexdigest() == "f162b54de2adfc72d78adb1dbada2dedda111ae0a5e2f6e9500f4f909664c5d2"
    root = Path(tempfile.mkdtemp(prefix="sencode-rg-中文-")).resolve()
    database = root / "isolated.sqlite"
    environment = environment_for(root)
    parent_path = os.environ.get("PATH")
    isolated_path = environment["PATH"]
    assert str(executable.parent).lower() not in isolated_path.lower()
    target = "Sencode/connection/search-fixture-" + uuid.uuid4().hex
    identifier = target.rsplit("/", 1)[1]
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
    advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi.CredDeleteW.restype = wintypes.BOOL
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.cases, server.results, server.errors = {}, {}, []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    written = False
    evidence = {"schema": 1, "result": "running", "host": os.environ.get("COMPUTERNAME"),
                "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                "ripgrep_sha256": hashlib.sha256(bundled.read_bytes()).hexdigest(),
                "inherited_path": isolated_path, "checks": [], "scope": "installed CLI, real shell/tool execution, loopback provider"}
    common = [str(executable), "--database", str(database), "--cwd", str(root)]

    def run(*arguments):
        result = subprocess.run([*common, *arguments], cwd=root, env=environment,
                                capture_output=True, encoding="utf-8", timeout=45)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr, server.errors)
        return json.loads(result.stdout.strip().splitlines()[-1])

    try:
        (root / "页面.html").write_text("<title>中文页面</title>\n<h1>fixture</h1>\n<script></script>\n<canvas></canvas>\n", encoding="utf-8")
        doctor = run("doctor")
        assert doctor["ripgrep"]["available"] and doctor["ripgrep"]["source"] == "bundled", doctor
        assert Path(doctor["ripgrep"]["executable"]).samefile(bundled)
        evidence["checks"].append("doctor-resolves-installed-image-relative-ripgrep")
        secret = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
        checked(advapi.CredWriteW(ctypes.byref(Credential(Type=1, TargetName=target, CredentialBlobSize=11,
                                                       CredentialBlob=secret, Persist=1)), 0))
        written = True
        config = {"baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "chatCompletions",
                  "selectedModelId": "fixture", "credentialRef": target, "enabledModels": [{"id": "fixture"}]}
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "search-fixture" if key == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Search fixture',?,'fixture',1,1)",
                       (identifier, json.dumps(config)))
            db.commit()
        for shell in ("bash", "powershell"):
            # Bash expands the screenshot's wildcard. Explicit Windows shells
            # use rg's own glob flag because they do not expand native argv.
            search_command = 'rg -n -m 4 "<title>|h1|script|canvas" *.html' if shell == "bash" else 'rg -n -m 4 -g "*.html" "<title>|h1|script|canvas" .'
            cases = [("screenshot" if shell == "bash" else "native-glob", search_command, 0, "中文页面"),
                     ("no-match", 'rg -n "absent-fixture-needle" "页面.html"', 1, "")]
            cases.append(("unicode", "rg -n '中文页面' '页面.html'", 0, "1:<title>中文页面</title>"))
            for name, command, exit_code, expected in cases:
                prompt = "search fixture " + shell + " " + name
                server.cases[prompt] = {"shell": shell, "command": command, "exit": exit_code, "expect": expected}
                reply = run("--connection", identifier, "--allow-commands", "-p", prompt, "--output-format", "json")
                assert reply["success"] and "SEARCH_VERIFIED" in reply.get("content", reply.get("text", "")), (reply, server.errors)
                assert prompt in server.results, server.errors
                evidence["checks"].append(shell + "-" + name)
        assert not server.errors, server.errors
        assert environment["PATH"] == isolated_path and os.environ.get("PATH") == parent_path
        evidence["checks"].append("parent-and-caller-path-unchanged")
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        raise
    finally:
        if written:
            checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown()
        server.server_close()
        evidence["provider_errors"] = server.errors
        evidence["tool_results"] = server.results
        write_json(args.evidence.resolve(), evidence)
        remove_owned_tree(root)
    print(json.dumps({"result": evidence["result"], "checks": len(evidence["checks"]), "evidence": str(args.evidence)}))


if __name__ == "__main__":
    main()
