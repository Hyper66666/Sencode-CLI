"""Second Enter and compression feedback in an owned Windows console."""
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
from live_steering_fixture import Provider
from fullscreen_console_fixture import wait
from tui_console_fixture import Console, checked, environment_for, write_json


def worker(args):
    evidence = {"schema": 1, "result": "running", "platform": "windows-x64",
        "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
        "scope": "Owned native Windows console, synthetic loopback API, disposable database",
        "checks": [], "snapshots": {}}
    process = None; credential_written = False
    identifier = "custom-input-" + uuid.uuid4().hex; target = "Sencode/connection/" + identifier
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests = []; server.errors = []; server.release = threading.Event(); server.summary_release = threading.Event()
    server.summary_started = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]; advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]; advapi.CredDeleteW.restype = wintypes.BOOL

    def record(name): evidence["checks"].append({"name": name, "status": "passed"})

    def submit(text):
        console.key(0x55, "\x15", 8); console.inject(text); console.key(0x0D, "\r")

    def slash(text):
        console.key(0x55, "\x15", 8); console.inject(text)
        wait(console, process, lambda s: "COMMANDS" in s["text"], "command completion")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "COMMANDS" not in s["text"], "completed command")
        console.key(0x0D, "\r")

    try:
        deadline = time.monotonic() + 8
        while not args.ready.exists():
            assert time.monotonic() < deadline; time.sleep(.02)
        environment = environment_for(args.scratch)
        os.environ.clear(); os.environ.update(environment)
        project = args.scratch / "workspace-中文"; project.mkdir(); database = args.scratch / "catalog.sqlite3"
        common = ["--cwd", str(project), "--database", str(database), "--connection", identifier]
        bootstrap = subprocess.run([str(args.executable), *common, "--version"], capture_output=True, timeout=10)
        assert bootstrap.returncode == 0
        # --version intentionally does not open the database.
        from engine_fixture import Host
        initializer = Host(args.executable, project, database, ""); initializer.stop(); initializer.abort()
        key = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
        credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=key, Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(credential), 0)); credential_written = True
        config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "chatCompletions",
            "selectedModelId": "fixture", "credentialRef": target, "enabledModels": [{"id": "fixture"}]}
        with sqlite3.connect(database) as db:
            db.create_function("sengoo_context", 1, lambda k: "input-fixture" if k == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Fixture',?,'fixture',1,1)", (identifier, json.dumps(config))); db.commit()
        console = Console(); console.resize(120, 38); console.clear(); baseline = console.modes()
        process = subprocess.Popen([str(args.executable), *common], cwd=project)
        wait(console, process, lambda s: "MESSAGE" in s["text"], "home", 20)
        submit("STEER_STREAM")
        wait(console, process, lambda s: "STREAMING_BEFORE_INSERT" in s["text"], "streaming")
        console.inject("补充条件 GUI"); console.key(0x0D, "\r")
        queued = wait(console, process, lambda s: "QUEUED / 1" in s["text"], "first Enter queued")
        assert len(server.requests) == 1; evidence["snapshots"]["queued"] = queued
        console.key(0x0D, "\r")
        inserting = wait(console, process, lambda s: "INSERTING /" in s["text"], "second Enter insertion")
        assert len(server.requests) == 1; evidence["snapshots"]["inserting"] = inserting
        console.key(0x0D, "\r"); console.inject("未发送草稿")
        server.release.set()
        done = wait(console, process, lambda s: "APPLIED: 补充条件 GUI" in s["text"] and "NEXT MESSAGE" not in s["text"], "same task continuation")
        assert len(server.requests) == 2 and "未发送草稿" in done["text"] and "INSERTING /" not in done["text"]
        record("second-enter-steers-once-without-abort-and-preserves-new-draft")
        for index in range(5):
            text = f"history-{index} " + "verified context 中文 " * 16
            submit(text); wait(console, process, lambda s: "APPLIED: history-" + str(index) in s["text"] and "NEXT MESSAGE" not in s["text"], "completed history")
        slash("/compact")
        assert server.summary_started.wait(5); time.sleep(.12)
        compacting = wait(console, process, lambda s: "Compacting" in s["text"], "compaction activity")
        assert not any(r["text"].strip().startswith(("Working ", "Thinking ")) for r in compacting["rows"])
        console.inject("压缩期间草稿")
        wait(console, process, lambda s: "压缩期间草稿" in s["text"] and "Compacting" in s["text"], "responsive summary input")
        evidence["snapshots"]["compacting"] = compacting; server.summary_release.set()
        compacted = wait(console, process, lambda s: "上下文已压缩" in s["text"] and "NEXT MESSAGE" not in s["text"], "compaction completion")
        assert "Context auto-compacted;" not in compacted["text"] and "Context compacted;" not in compacted["text"] and "private summary analysis" not in compacted["text"] and "压缩期间草稿" in compacted["text"]
        evidence["snapshots"]["compacted"] = compacted
        record("compacting-covers-private-reasoning-and-completion-uses-chinese-information")
        slash("/consult")
        notice = wait(console, process, lambda s: "Use /consult QUESTION." in s["text"], "red notice")
        for label in ("NOTICE", "Use /consult QUESTION."):
            row = next(r for r in notice["rows"] if label in r["text"])
            cells = [a & 15 for c, a in row["cells"] if chr(c).strip()]
            assert cells and all(c == 4 for c in cells), (label, cells)
        evidence["snapshots"]["notice"] = notice; record("notice-heading-and-content-are-red-console-cells")
        console.key(0x55, "\x15", 8); console.key(0x44, "\x04", 8); process.wait(timeout=12)
        assert process.returncode == 0 and console.modes() == baseline
        record("terminal-modes-restored"); assert not server.errors, server.errors; evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"; evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None:
            evidence["last_screen"] = console.read(viewport=True)
    finally:
        server.release.set(); server.summary_release.set()
        if process is not None and process.poll() is None: process.terminate(); process.wait(timeout=5)
        if credential_written: checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown(); server.server_close(); evidence["provider_errors"] = server.errors
        evidence["fixture_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        write_json(args.evidence, evidence)
    return 0 if evidence["result"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, required=True); parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scratch", type=Path); parser.add_argument("--ready", type=Path); args = parser.parse_args()
    args.executable = args.executable.resolve(strict=True); args.evidence = args.evidence.resolve()
    if args.worker: return worker(args)
    harness.__file__ = __file__; return harness.controller(args)


if __name__ == "__main__": raise SystemExit(main())
