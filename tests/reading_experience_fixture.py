"""Reading/diff/activity gate in an owned hidden Windows console.

Uses isolated state and a synthetic loopback provider, never user credentials.
The existing harness owns the console Job and inventoried temporary tree.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import http.server
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import threading
import time
import traceback
import uuid

import agent_reliability_fixture as harness
from cli_fixture import Credential
from fullscreen_console_fixture import wait
from terminal_pane_console_fixture import resize_fullscreen
from tui_console_fixture import Console, checked, environment_for, write_json


BEFORE = "\n".join(f"line_{i}=old" for i in range(1, 19)) + "\n"
AFTER = BEFORE.replace("line_3=old", "line_3=new").replace("line_15=old", "line_15=new")


class Provider(harness.Provider):
    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            history = body["messages"]
            latest = max(i for i, value in enumerate(history) if value["role"] == "user")
            prompt = history[latest]["content"]
            results = [x for x in history[latest + 1:] if x["role"] == "tool"]
            self.server.requests.append(body)
            if prompt == "REQUEST_FAILURE_FIXTURE":
                self.send_error(400, "Synthetic request failure")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            if prompt == "ACTIVITY_FIXTURE":
                self.wfile.write(b'data: {"choices":[{"delta":{"reasoning_content":"private fixture"}}]}\n\n')
                self.wfile.flush()
                time.sleep(1.0)
                self.event("PUBLIC_ACTIVITY\n")
                time.sleep(.7)
                self.event("ACTIVITY_DONE\n", done=True)
            elif prompt == "READING_FIXTURE":
                stages = [("read_file", {"path": "fixture.txt"}),
                          ("list_directory", {"path": "."}),
                          ("search", {"query": "line_3"})]
                if results:
                    assert not json.loads(results[-1]["content"])["is_error"], results
                if len(results) < len(stages):
                    name, args = stages[len(results)]
                    time.sleep(.15)
                    self.event(tool=(f"read-{len(results)}", name, args))
                else:
                    self.event("READING_DONE\n", done=True)
            elif prompt == "DIFF_FIXTURE":
                if not results:
                    self.event(tool=("diff-edit", "write_file", {"path": "fixture.txt", "content": AFTER, "expected_content": BEFORE}))
                else:
                    assert not json.loads(results[-1]["content"])["is_error"], results
                    self.event("# 修改结果\n已更新 `fixture.txt`。\nDIFF_DONE\n", done=True)
            else:
                raise AssertionError("Unexpected synthetic prompt")
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except BaseException:
            self.server.errors.append(traceback.format_exc())
        finally:
            self.close_connection = True


def worker(args):
    evidence = {"schema": 1, "result": "running", "scope": "owned-console synthetic loopback",
                "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                "fixture_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "checks": [], "snapshots": {}}
    process = None
    credential_written = False
    target = "Sencode/connection/reading-" + uuid.uuid4().hex
    identifier = target.rsplit("/", 1)[1]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests, server.errors = [], []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
    advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi.CredDeleteW.restype = wintypes.BOOL

    def record(name, condition, detail=None):
        evidence["checks"].append({"name": name, "status": "passed" if condition else "failed", "detail": detail})

    def submit(prompt):
        console.key(0x1B, "\x1b")
        console.key(0x55, "\x15", 8)
        console.inject(prompt)
        wait(console, process, lambda screen: prompt in screen["text"], "draft")
        console.key(0x0D, "\r")

    try:
        deadline = time.monotonic() + 8
        while not args.ready.exists():
            assert time.monotonic() < deadline
            time.sleep(.02)
        environment = environment_for(args.scratch)
        os.environ.clear()
        os.environ.update(environment)
        workspace = args.scratch / "workspace-中文"
        workspace.mkdir()
        (workspace / "fixture.txt").write_bytes(BEFORE.encode("utf-8"))
        database = args.scratch / "isolated.sqlite"
        common = ["--cwd", str(workspace), "--database", str(database), "--connection", identifier]
        initial = subprocess.run([str(args.executable), *common, "doctor"], capture_output=True, timeout=25)
        assert initial.returncode == 0, initial.stderr.decode(errors="replace")
        key = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
        credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=key, Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(credential), 0))
        credential_written = True
        config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                  "protocol": "chatCompletions", "successfulProtocol": "chatCompletions",
                  "selectedModelId": "fixture", "credentialRef": target,
                  "enabledModels": [{"id": "fixture"}]}
        with sqlite3.connect(database) as db:
            db.create_function("sengoo_context", 1, lambda key: "reading-fixture" if key == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','reading fixture',?,'fixture',1,1)", (identifier, json.dumps(config)))
        console = Console()
        console.resize(120, 46)
        console.clear()
        baseline = console.modes()
        process = subprocess.Popen([str(args.executable), *common], cwd=workspace)
        wait(console, process, lambda screen: "MESSAGE" in screen["text"], "home", 20)
        submit("ACTIVITY_FIXTURE")
        thinking = wait(console, process, lambda screen: "Thinking" in screen["text"], "explicit reasoning")
        working = wait(console, process, lambda screen: "PUBLIC_ACTIVITY" in screen["text"] and "Working" in screen["text"], "public text stage")
        done = wait(console, process, lambda screen: "ACTIVITY_DONE" in screen["text"] and "Worked for" in screen["text"], "static duration")
        record("provider-signals-thinking-then-working-without-hidden-text", "private fixture" not in thinking["text"] + working["text"])
        for name, screen in [("thinking", thinking), ("working", working), ("done", done)]:
            evidence["snapshots"][name] = screen
            top = max(i for i, row in enumerate(screen["rows"]) if "╭" in row["text"])
            record(name + "-composer-has-no-activity-and-retains-spacer", not screen["rows"][top - 1]["text"].strip() and all(word not in "\n".join(r["text"] for r in screen["rows"][top:]) for word in ("Working", "Thinking", "Worked for")))
        submit("READING_FIXTURE")
        folded = wait(console, process, lambda screen: "READING_DONE" in screen["text"] and "Explored" in screen["text"] and "NEXT MESSAGE" not in screen["text"], "reading group")
        record("consecutive-reading-has-truthful-collapsed-counts", "1 file" in folded["text"] and "1 directory" in folded["text"] and "1 search" in folded["text"] and "read_file" not in folded["text"])
        evidence["snapshots"]["folded"] = folded
        console.key(0x4F, "\x0f", 8)
        opened = wait(console, process, lambda screen: "read_file" in screen["text"] and "list_directory" in screen["text"], "expanded group")
        record("keyboard-toggle-reveals-operation-details", "fixture.txt" in opened["text"])
        console.key(0x4F, "\x0f", 8)
        wait(console, process, lambda screen: "read_file" not in screen["text"], "closed group")
        submit("DIFF_FIXTURE")
        approval = wait(console, process, lambda screen: "PERMISSION REQUIRED" in screen["text"], "diff approval")
        record("diff-remains-manually-approved", (workspace / "fixture.txt").read_text(encoding="utf-8") == BEFORE)
        evidence["snapshots"]["approval"] = approval
        console.key(0x28)
        console.key(0x0D, "\r")
        edited = wait(console, process, lambda screen: "DIFF_DONE" in screen["text"] and "NEXT MESSAGE" not in screen["text"], "diff complete")
        evidence["snapshots"]["edited"] = edited
        record("multi-hunk-diff-has-file-summary-and-correct-text", "Edited fixture.txt" in edited["text"] and "+2" in edited["text"] and "line_3=new" in edited["text"] and "line_15=new" in edited["text"] and (workspace / "fixture.txt").read_text(encoding="utf-8") == AFTER)
        changes = [row for row in edited["rows"] if "line_3=old" in row["text"] or "line_3=new" in row["text"]]
        def foreground_at(row, marker):
            offset = row["text"].index(marker)
            return int(row["cells"][offset][1]) & 7
        record("diff-changes-have-foreground-colors-without-row-background", len(changes) == 2 and all(all((int(attr) & 0xF0) == 0 for _, attr in row["cells"]) for row in changes) and all(foreground_at(row, "line_3=") == (4 if "line_3=old" in row["text"] else 2) for row in changes))
        for width in (80, 160, 120):
            resize_fullscreen(console, width, 46)
            screen = wait(console, process, lambda screen: screen["width"] == width and "MESSAGE" in screen["text"], "resized reading workbench")
            evidence["snapshots"][f"width-{width}"] = screen
            record(f"actual-console-{width}-columns", all(len(row["cells"]) == width for row in screen["rows"]))
        submit("REQUEST_FAILURE_FIXTURE")
        failed = wait(console, process, lambda screen: "Model request failed" in screen["text"] and "NEXT MESSAGE" not in screen["text"], "classified failure")
        record("provider-error-does-not-claim-unknown-tool-side-effects", "code 400" in failed["text"] and "automatic replay is forbidden" not in failed["text"])
        assert not server.errors, server.errors
        console.key(0x44, "\x04", 8)
        process.wait(timeout=12)
        record("terminal-restored", process.returncode == 0 and console.modes() == baseline)
        evidence["result"] = "passed" if all(x["status"] == "passed" for x in evidence["checks"]) else "failed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None:
            evidence["last_screen"] = console.read(viewport=True)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        if credential_written:
            checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown()
        server.server_close()
        evidence["provider_errors"] = server.errors
        write_json(args.evidence, evidence)
    return 0 if evidence["result"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    args.executable = args.executable.resolve(strict=True)
    args.evidence = args.evidence.resolve()
    if args.worker:
        return worker(args)
    # Reuse its Job/console/temp ownership lifecycle with this worker entrypoint.
    harness.__file__ = __file__
    return harness.controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
