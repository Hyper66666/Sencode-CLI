"""Owned hidden-console gate for the real Sengoo full-screen renderer.

Production mode drives the complete CLI, an isolated SQLite database and a
loopback provider; driver mode exercises a synthetic UI program. Neither mode
uses user state or an external service. Screen cells come from Windows console
readback rather than an ANSI emulator.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
from ctypes import wintypes
import hashlib
import http.server
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sqlite3
import struct
import sys
import tempfile
import time
import threading
import traceback
import uuid
import zlib

from tui_console_fixture import (
    Console, JobExtendedLimits, checked, environment_for, kernel_api,
    remove_owned_tree, write_json,
)
from cli_fixture import Credential


class SlowProvider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    calls = []
    requests = []
    paths = []
    latency_lock = threading.Lock()
    latency_active = 0
    latency_maximum = 0
    render_times = {}

    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.headers.get("Authorization") != "Bearer fixture-key":
            self.send_error(401)
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.requests.append(body)
        self.paths.append(self.path)
        messages = body.get("messages", [])
        latest_content = next((x.get("content", "") for x in reversed(messages) if x.get("role") == "user"), "")
        latest = "".join(part.get("text", "") for part in latest_content if part.get("type") == "text") if isinstance(latest_content, list) else latest_content
        latest_index = max((i for i, x in enumerate(messages) if x.get("role") == "user"), default=-1)
        current_tools = any(x.get("role") == "tool" for x in messages[latest_index + 1:])
        self.calls.append(latest)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Connection", "close")
        self.end_headers()
        latency = latest == "latency fixture"
        if latency:
            with self.latency_lock:
                type(self).latency_active += 1
                type(self).latency_maximum = max(type(self).latency_maximum, type(self).latency_active)
        try:
            if latest.startswith("image submission fixture"):
                assert isinstance(latest_content, list), latest_content
                image_parts = [part for part in latest_content if part.get("type") == "image_url"]
                assert len(image_parts) == 1, latest_content
                assert base64.b64decode(image_parts[0]["image_url"]["url"].split(",", 1)[1]).startswith(b"\x89PNG\r\n\x1a\n"), image_parts
                self.event({"choices": [{"delta": {"content": "image bytes verified"}, "finish_reason": "stop"}]})
            elif latest == "local conveniences fixture":
                self.event({"choices": [{"delta": {"content": "Local answer\n```python\nprint('中文')\n```\n"}, "finish_reason": "stop"}]})
            elif latest == "approval fixture" and not current_tools:
                event = {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "write-approval", "function": {
                    "name": "write_file", "arguments": json.dumps({"path": "must-not-write.txt", "content": "denied"})}}]}, "finish_reason": "tool_calls"}]}
                self.event(event)
            elif latest in {"checkpoint fixture 1", "checkpoint fixture 2"} and not current_tools:
                suffix = latest.rsplit(" ", 1)[1]
                self.event({"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "checkpoint-write-" + suffix, "function": {
                    "name": "write_file", "arguments": json.dumps({"path": "checkpoint.txt", "content": "after-" + suffix, "expected_content": "before"})}}]}, "finish_reason": "tool_calls"}]})
            elif latest == "diff fixture" and not current_tools:
                self.event({"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "diff-edit", "function": {
                    "name": "apply_patch", "arguments": json.dumps({"path": "preview.txt", "old": "old value", "new": "new value"})}}]}, "finish_reason": "tool_calls"}]})
            elif latest in {"question choice fixture", "question custom fixture", "question cancel fixture"}:
                if not current_tools:
                    time.sleep(0.25)
                    self.event({"choices": [{"delta": {"tool_calls": [{"index": 0, "id": latest.replace(" ", "-"), "function": {
                        "name": "ask_user", "arguments": json.dumps({"question": "选择下一步", "options": [
                            {"label": "保留现有实现", "description": "继续使用当前布局"},
                            {"label": "优化增量渲染", "description": "只刷新变化的内容"},
                            {"label": "重做整体界面", "description": "重新安排页面布局"}]}, ensure_ascii=False)}}]}, "finish_reason": "tool_calls"}]})
                else:
                    result = json.loads(next(value["content"] for value in reversed(messages) if value.get("role") == "tool"))
                    expected = "优化增量渲染" if latest == "question choice fixture" else "先保留布局，只修复卡顿"
                    assert latest != "question cancel fixture" and not result["is_error"] and result["content"] == expected, result
                    self.event({"choices": [{"delta": {"content": "question verified: " + expected}, "finish_reason": "stop"}]})
            elif latest == "render fixture":
                prelude = "# Streaming Markdown\n\n" + "".join(
                    f"Stable paragraph {index}: 中文 **stable block** and `code`.\n\n"
                    for index in range(100)) + "```text\n"
                self.event({"choices": [{"delta": {"content": prelude}, "finish_reason": None}]})
                for index in range(30):
                    type(self).render_times[index] = time.monotonic()
                    self.event({"choices": [{"delta": {"content": f"render-step-{index:03d} 中文 streamed tail\n"}, "finish_reason": None}]})
                    time.sleep(0.04)
                self.event({"choices": [{"delta": {"content": "```\nRender complete.\n"}, "finish_reason": "stop"}]})
            else:
                slow = latest in {"slow fixture", "queue fixture", "queue edit fixture", "pending insertion fixture"}
                values = (f"consult {body.get('model', 'fixture')} line {index} 中文\n" for index in range(200)) if latency else ((f"slow line {index} 中文\n" for index in range(20 if latest == "queue fixture" else 100)) if slow else ["你好！😀 欢迎使用 Sencode。\n" if latest == "你好" else ("Queue edit answer 中文\n" if latest == "production edited task" else ("Queued answer 中文\n" if latest == "queued after picker" else "Seed answer 中文\n"))])
                for value in values:
                    self.event({"choices": [{"delta": {"content": value}, "finish_reason": None}]})
                    if slow or latency:
                        time.sleep(0.02 if latency else 0.08)
                self.event({"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 18, "completion_tokens": 9}})
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # Cancellation is part of this fixture.
        finally:
            if latency:
                with self.latency_lock:
                    type(self).latency_active -= 1
        self.close_connection = True

    def event(self, value):
        self.wfile.write(("data: " + json.dumps(value, ensure_ascii=False) + "\n\n").encode("utf-8"))
        self.wfile.flush()


def wait(console, process, predicate, description, timeout=12):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = console.read(viewport=True)
        if predicate(last):
            return last
        if process.poll() is not None:
            raise AssertionError(f"UI exited {process.returncode} waiting for {description}: {last['text']}")
        time.sleep(0.025)
    raise AssertionError(f"Timed out waiting for {description}: {last['text']}")


def down_to(console, process, label):
    console.key(0x28)
    return wait(console, process, lambda s: "› " + label in s["text"], "selected " + label)


def worker(args):
    if args.production:
        return production_worker(args)
    evidence = {"schema": 1, "result": "running", "checks": [], "snapshots": {}}
    process = None
    try:
        deadline = time.monotonic() + 8
        while not args.ready.exists():
            if time.monotonic() > deadline:
                raise AssertionError("Owned Job was not established")
            time.sleep(0.02)
        console = Console()
        console.resize(110, 35)
        console.clear()
        original_modes = console.modes()
        process = subprocess.Popen([str(args.executable)], cwd=str(args.scratch), env=environment_for(args.scratch))
        home = wait(console, process, lambda s: "S E N C O D E" in s["text"] and "MESSAGE" in s["text"], "centered home")
        evidence["snapshots"]["home"] = home
        assert any("█████  █████" in row["text"] for row in home["rows"]), home["text"]
        assert home["cursor"]["y"] >= home["window"]["bottom"] - 4
        evidence["checks"].append("centered-art-and-fixed-composer")

        console.inject("/mod")
        menu = wait(console, process, lambda s: "COMMANDS" in s["text"] and "/model" in s["text"], "slash menu")
        evidence["snapshots"]["menu"] = menu
        console.key(0x0D, "\r")
        completed = wait(console, process, lambda s: "Command completed" in s["text"] and "COMMANDS" not in s["text"], "first Enter completion")
        assert "MODEL PICKER OPENED" not in completed["text"]
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "MODEL PICKER OPENED" in s["text"], "second Enter execution")
        evidence["checks"].append("slash-list-and-two-step-enter")

        console.inject("/permissions auto")
        wait(console, process, lambda s: "COMMAND ARGUMENTS" in s["text"] and "auto-edit" in s["text"], "command argument candidates")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "/permissions auto-edit" in s["text"] and "COMMAND ARGUMENTS" not in s["text"], "argument first Enter completion")
        console.key(0x55, "\x15", 8)
        console.inject("Read @src/m")
        wait(console, process, lambda s: "WORKSPACE REFERENCES" in s["text"] and "src/main.sg" in s["text"], "workspace reference candidates")
        console.key(0x0D, "\r")
        referenced = wait(console, process, lambda s: "Read @src/main.sg" in s["text"] and "WORKSPACE REFERENCES" not in s["text"], "reference first Enter completion")
        assert "YOU" not in referenced["text"], referenced["text"]
        evidence["snapshots"]["reference-completion"] = referenced
        evidence["checks"].append("argument-and-reference-enter-only-completes")
        console.key(0x55, "\x15", 8)
        console.command("stream")
        first = wait(console, process, lambda s: "stream line 0" in s["text"] and "NEXT MESSAGE" in s["text"], "stream starts")
        console.inject("draft 中文")
        streaming = wait(console, process, lambda s: "draft 中文" in s["text"] and "stream line 3" in s["text"], "draft while streaming")
        evidence["snapshots"]["streaming-draft"] = streaming
        evidence["checks"].append("streaming-output-and-editable-draft")

        console.key(0x0D, "\r")
        wait(console, process, lambda s: "1 queued" in s["text"], "queue draft while busy")
        console.inject("kept composer 中文")
        console.key(0x51, "\x11", 8)
        wait(console, process, lambda s: "QUEUED TASKS" in s["text"], "queue manager")
        down_to(console, process, "Task 1")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "QUEUED TASK 1" in s["text"] and "Edit queued task" in s["text"], "queued task actions")
        down_to(console, process, "View complete task")
        down_to(console, process, "Edit queued task")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "EDIT QUEUED TASK" in s["text"] and "draft 中文" in s["text"], "queued task editor")
        console.key(0x55, "\x15", 8)
        console.inject("edited queued 中文")
        console.key(0x0D, "\r")
        queue_saved = wait(console, process, lambda s: "QUEUED TASKS" in s["text"] and "edited queued 中文" in s["text"] and "kept composer 中文" in s["text"], "save queue edit without submitting")
        evidence["snapshots"]["queue-edited"] = queue_saved
        evidence["checks"].append("queue-editor-saves-without-submitting-and-preserves-draft")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "QUEUED TASKS" not in s["text"] and "NEXT MESSAGE" in s["text"], "close paused queue")
        console.key(0x1B, "\x1b")
        cancelled = wait(console, process, lambda s: "Paused / cancelled" in s["text"] and "kept composer 中文" in s["text"] and "queue paused" in s["text"], "cancel preserves draft")
        evidence["snapshots"]["cancelled"] = cancelled
        evidence["checks"].append("cancel-preserves-draft-and-partial-text")

        console.key(0x51, "\x11", 8)
        wait(console, process, lambda s: "QUEUED TASKS" in s["text"], "review saved queued task")
        down_to(console, process, "Task 1")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "QUEUED TASK 1" in s["text"], "review queued actions")
        down_to(console, process, "View complete task")
        down_to(console, process, "Edit queued task")
        down_to(console, process, "Cancel this queued task")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "QUEUED TASKS" in s["text"] and "edited queued 中文" not in s["text"], "cancel queued task")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "QUEUED TASKS" not in s["text"], "close empty paused queue")
        evidence["checks"].append("cancel-queued-task-without-execution")
        console.key(0x55, "\x15", 8)
        console.command("markdown")
        rendered = wait(console, process, lambda s: "Markdown fixture" in s["text"] and "+new value" in s["text"] and "Use bold and code." in s["text"], "Markdown blocks")
        assert "```diff" not in rendered["text"] and "**bold**" not in rendered["text"]
        assert "│ kind" in rendered["text"] and "│ text" in rendered["text"], rendered["text"]
        evidence["snapshots"]["markdown-code-diff-table"] = rendered
        evidence["checks"].append("native-console-markdown-code-diff-and-table")

        console.command("/quit")
        wait(console, process, lambda s: "Command completed" in s["text"] and "/quit" in s["text"], "complete quit")
        console.key(0x0D, "\r")
        assert process.wait(timeout=8) == 0
        assert console.modes() == original_modes, (original_modes, console.modes())
        evidence["checks"].append("terminal-modes-restored")
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        write_json(args.evidence, evidence)


def production_worker(args):
    evidence = {"schema": 1, "scope": "final-main-loopback-provider", "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(), "result": "running", "checks": [], "snapshots": {}}
    process = None
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
    advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi.CredDeleteW.restype = wintypes.BOOL
    target = "Sencode/connection/fullscreen-fixture-" + str(uuid.uuid4())
    credential_written = False
    written_targets = []
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), SlowProvider)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        deadline = time.monotonic() + 8
        while not args.ready.exists():
            if time.monotonic() > deadline:
                raise AssertionError("Owned Job was not established")
            time.sleep(0.02)
        console = Console()
        console.resize(110, 35)
        console.clear()
        baseline = console.modes()
        workspace = args.scratch / "outside-workspace-中文"
        workspace.mkdir()
        (workspace / "src").mkdir()
        (workspace / "src" / "input.sg").write_text("def main() -> i64 { 0 }\n", encoding="utf-8")
        (workspace / "checkpoint.txt").write_text("before", encoding="utf-8")
        (workspace / "preview.txt").write_text("context\nold value\nending\n", encoding="utf-8")
        def png_chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        image_path = args.scratch / "original screenshot 中文.png"
        original_png = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + png_chunk(b"IDAT", zlib.compress(b"\x00\x10\x20\x30")) + png_chunk(b"IEND", b"")
        image_path.write_bytes(original_png)
        second_image_path = args.scratch / "second original screenshot 中文.png"
        second_image_path.write_bytes(original_png)
        database = args.scratch / "isolated.sqlite"
        environment = environment_for(args.scratch)
        common = ["--database", str(database), "--cwd", str(workspace)]
        initialized = subprocess.run([str(args.executable), *common, "doctor"], cwd=workspace, env=environment, capture_output=True, timeout=20)
        assert initialized.returncode == 0, initialized.stderr.decode(errors="replace")
        key = (ctypes.c_ubyte * len(b"fixture-key")).from_buffer_copy(b"fixture-key")
        credential = Credential(Type=1, TargetName=target, CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(credential), 0))
        credential_written = True
        written_targets.append(target)
        for lane in range(1, 4):
            lane_credential = Credential(Type=1, TargetName=target + f"-{lane}", CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
            checked(advapi.CredWriteW(ctypes.byref(lane_credential), 0))
            written_targets.append(target + f"-{lane}")
        identifier = target.rsplit("/", 1)[1]
        config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1", "protocol": "chatCompletions", "successfulProtocol": "chatCompletions", "selectedModelId": "fixture", "credentialRef": target, "enabledModels": [{"id": name, "label": name, "capabilities": {"visionSupported": True}} for name in ("fixture", "fixture-fast", "fixture-large")]}
        with sqlite3.connect(database) as db:
            db.create_function("sengoo_context", 1, lambda name: "fullscreen-fixture" if name == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','fullscreen loopback',?,'fixture',1,1)", (identifier, json.dumps(config)))
            for lane in range(1, 4):
                lane_config = dict(config, selectedModelId=f"fixture-{lane}", credentialRef=target + f"-{lane}", enabledModels=[{"id": f"fixture-{lane}"}])
                db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed',?,?,?,1,1)", (identifier + f"-{lane}", f"fullscreen lane {lane}", json.dumps(lane_config), f"fixture-{lane}"))
            db.commit()
        seeded = subprocess.run([str(args.executable), *common, "--connection", identifier, "-p", "seed fixture", "--output-format", "json"], cwd=workspace, env=environment, capture_output=True, timeout=25)
        assert seeded.returncode == 0, seeded.stdout.decode(errors="replace") + seeded.stderr.decode(errors="replace")
        seed = json.loads(seeded.stdout.decode("utf-8").strip().splitlines()[-1])["session_id"]
        with sqlite3.connect(database) as db:
            db.create_function("sengoo_context", 1, lambda name: "fullscreen-fixture" if name == "instance_id" else None)
            db.execute("UPDATE sessions SET title='seed-history' WHERE id=?", (seed,))
            db.commit()

        def launch(*arguments):
            console.clear()
            return subprocess.Popen([str(args.executable), *common, "--connection", identifier, *arguments], cwd=workspace, env=environment)

        def slash(name):
            console.inject(name)
            wait(console, process, lambda s: ("COMMANDS" in s["text"] or "COMMAND ARGUMENTS" in s["text"]) and name in s["text"], name + " menu")
            console.key(0x0D, "\r")
            wait(console, process, lambda s: "completed" in s["text"].lower() and "COMMANDS" not in s["text"] and "COMMAND ARGUMENTS" not in s["text"] and name in s["text"], name + " completion")
            console.key(0x0D, "\r")

        def stop():
            nonlocal process
            console.key(0, "\x15", 8)
            slash("/quit")
            assert process.wait(timeout=15) == 0
            assert console.modes() == baseline, (baseline, console.modes())
            process = None

        process = launch()
        home = wait(console, process, lambda s: "S E N C O D E" in s["text"] and "MESSAGE" in s["text"], "production home")
        evidence["snapshots"]["home"] = home
        evidence["checks"].append("final-main-centered-home")
        console.inject("/permissions auto")
        wait(console, process, lambda s: "COMMAND ARGUMENTS" in s["text"] and "auto-edit" in s["text"], "production argument candidates")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "/permissions auto-edit" in s["text"] and "COMMAND ARGUMENTS" not in s["text"], "production argument completion")
        console.key(0x55, "\x15", 8)
        evidence["checks"].append("production-command-argument-enter-only-completes")
        console.inject("Read @src/in")
        wait(console, process, lambda s: "WORKSPACE REFERENCES" in s["text"] and "src/input.sg" in s["text"], "real workspace reference catalog")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Read @src/input.sg" in s["text"] and "WORKSPACE REFERENCES" not in s["text"], "reference completion without request")
        assert SlowProvider.calls == ["seed fixture"], SlowProvider.calls
        console.key(0x55, "\x15", 8)
        evidence["checks"].append("workspace-reference-catalog-and-no-submit-completion")
        slash("/model")
        catalog = wait(console, process, lambda s: "MODELS  /" in s["text"] and "fixture-fast" in s["text"] and "fixture-large" in s["text"], "all enabled models")
        provider_rows = [next(i for i, row in enumerate(catalog["rows"]) if label in row["text"]) for label in
                         ("fullscreen loopback", "fullscreen lane 1", "fullscreen lane 2", "fullscreen lane 3")]
        assert provider_rows == sorted(set(provider_rows)), catalog["text"]
        assert provider_rows[0] < next(i for i, row in enumerate(catalog["rows"]) if "fixture-large" in row["text"]) < provider_rows[1], catalog["text"]
        evidence["snapshots"]["models"] = catalog
        console.key(0x0D, "\r")
        effort = wait(console, process, lambda s: "Thinking effort / fixture" in s["text"] and "xhigh" in s["text"] and "max" in s["text"], "reasoning second level")
        evidence["snapshots"]["effort"] = effort
        assert SlowProvider.calls == ["seed fixture"], SlowProvider.calls
        console.key(0x28)
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "fixture  high" in s["text"].splitlines()[0] and "Selected fixture  high" in s["text"] and "Thinking effort /" not in s["text"], "atomic model and effort selection")
        console.command("你好")
        greeting = wait(console, process, lambda s: "你好！" in s["text"] and "NEXT MESSAGE" not in s["text"], "Chinese-leading answer remains in TUI")
        assert "YOU" in greeting["rows"][3]["text"] and "你好" in greeting["rows"][4]["text"], greeting["text"]
        assert SlowProvider.requests[-1]["reasoning_effort"] == "high", SlowProvider.requests[-1]
        evidence["snapshots"]["unicode-greeting"] = greeting
        evidence["checks"].append("vertical-all-supplier-models-top-origin-effort-and-unicode-error20-regression")
        # Simulate sencode-config saving another supplier while the CLI stays
        # open. Duplicate model ids must retain this supplier's request route.
        refreshed_credential = Credential(Type=1, TargetName=target + "-refreshed", CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(refreshed_credential), 0))
        written_targets.append(target + "-refreshed")
        with sqlite3.connect(database) as db:
            db.create_function("sengoo_context", 1, lambda name: "fullscreen-fixture" if name == "instance_id" else None)
            refreshed = dict(config, baseUrl=f"http://127.0.0.1:{server.server_port}/refreshed/v1", credentialRef=target + "-refreshed",
                             enabledModels=[{"id": "fixture", "capabilities": {"visionSupported": True}}, {"id": "fresh-model"}])
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','refreshed supplier',?,'fixture',2,2)",
                       (identifier + "-refreshed", json.dumps(refreshed)))
            db.commit()
        slash("/model")
        console.inject("refreshed supplier")
        refreshed_menu = wait(console, process, lambda s: "fresh-model" in s["text"] and "refreshed supplier" in s["text"], "configuration client supplier refresh")
        evidence["snapshots"]["refreshed-supplier"] = refreshed_menu
        console.key(0x1B, "\x1b")
        cancelled = wait(console, process, lambda s: "MODELS  /" not in s["text"], "cancel refreshed model menu")
        assert "fixture  high" in cancelled["rows"][0]["text"], cancelled["text"]
        slash("/model")
        console.inject("refreshed supplier")
        wait(console, process, lambda s: "fresh-model" in s["text"], "refreshed supplier filtered again")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Thinking effort / fixture" in s["text"], "duplicate model supplier effort")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Selected fixture" in s["text"] and "Thinking effort /" not in s["text"], "refreshed supplier selected")
        console.command("provider routing fixture")
        wait(console, process, lambda s: SlowProvider.calls[-1] == "provider routing fixture" and "provider routing fixture" in s["text"] and "NEXT MESSAGE" not in s["text"] and "Worked for" in s["text"], "refreshed supplier routed request")
        assert SlowProvider.paths[-1].startswith("/refreshed/v1/") and SlowProvider.requests[-1]["model"] == "fixture", SlowProvider.paths
        evidence["checks"].append("configuration-refresh-cancel-and-duplicate-model-supplier-request-routing")
        slash("/resume")
        wait(console, process, lambda s: "Resume a project session" in s["text"], "resume picker")
        console.inject("seed-history")
        wait(console, process, lambda s: "seed-history" in s["text"], "resume filter")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Seed answer 中文" in s["text"] and "Resume a project session" not in s["text"], "history restore")
        evidence["checks"].append("model-and-resume-pickers-with-history")
        console.command("slow fixture")
        wait(console, process, lambda s: "slow line 0 中文" in s["text"] and "NEXT MESSAGE" in s["text"], "real HTTP streaming")
        console.inject("draft 中文")
        streamed = wait(console, process, lambda s: "slow line 4 中文" in s["text"] and "draft 中文" in s["text"], "real streaming draft")
        evidence["snapshots"]["streaming"] = streamed
        composer_footer = "\n".join(row["text"] for row in streamed["rows"][-2:])
        assert "thinking" not in composer_footer.lower(), composer_footer
        assert not any(symbol in composer_footer for symbol in "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"), composer_footer
        evidence["checks"].append("composer-footer-has-no-thinking-label-or-spinner")
        evidence["checks"].append("real-provider-incremental-output-and-live-draft")
        console.key(0, "\x15", 8)
        slash("/model")
        wait(console, process, lambda s: "MODELS  /" in s["text"] and "NEXT MESSAGE" in s["text"], "busy model menu")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "MODELS  /" not in s["text"], "close busy model picker")
        console.inject("kept draft 中文")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "Paused / cancelled" in s["text"] and "kept draft 中文" in s["text"], "cancel and preserve draft", timeout=20)
        evidence["checks"].append("model-menu-during-stream-and-cancellation")
        console.key(0, "\x15", 8)
        console.command("render fixture")
        visible_updates = {}
        render_deadline = time.monotonic() + 15
        while time.monotonic() < render_deadline:
            screen = console.read(viewport=True)
            seen_at = time.monotonic()
            steps = [int(value) for value in re.findall(r"render-step-(\d{3})", screen["text"])]
            if steps:
                newest = max(steps)
                if newest not in visible_updates and newest in SlowProvider.render_times:
                    visible_updates[newest] = (seen_at - SlowProvider.render_times[newest]) * 1000
            if "Render complete." in screen["text"] and "NEXT MESSAGE" not in screen["text"]:
                break
            assert process.poll() is None, screen["text"]
            time.sleep(0.005)
        else:
            raise AssertionError("Growing Markdown response did not finish: " + screen["text"])
        lags = sorted(visible_updates.values())
        assert len(lags) >= 10 and 29 in visible_updates, visible_updates
        lag_p95 = lags[math.ceil(len(lags) * 0.95) - 1]
        evidence["stream_render"] = {"provider_interval_ms": 40, "stable_paragraphs": 100,
            "visible_updates": len(lags), "p95_lag_ms": lag_p95, "maximum_lag_ms": max(lags)}
        assert lag_p95 < 200, evidence["stream_render"]
        evidence["snapshots"]["growing-markdown"] = screen
        evidence["checks"].append("growing-markdown-shows-live-intermediate-output-without-character-playback")
        console.command("question choice fixture")
        console.inject("question draft 中文")
        choices = wait(console, process, lambda s: "QUESTION" in s["text"] and "优化增量渲染" in s["text"], "model-provided answer choices")
        evidence["snapshots"]["model-question-options"] = choices
        console.key(0x28)
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "question verified: 优化增量渲染" in s["text"] and "NEXT MESSAGE" not in s["text"] and "question draft 中文" in s["text"], "arrow and Enter answer with draft retained")
        console.key(0, "\x15", 8)
        console.command("question custom fixture")
        wait(console, process, lambda s: "QUESTION" in s["text"] and "重做整体界面" in s["text"], "second question choices")
        for _ in range(3):
            console.key(0x28)
        console.key(0x0D, "\r")
        console.inject("先保留布局，只修复卡顿")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "question verified: 先保留布局，只修复卡顿" in s["text"] and "NEXT MESSAGE" not in s["text"], "custom model question answer")
        evidence["checks"].append("model-question-arrow-enter-custom-and-composer-isolation")
        console.command("question cancel fixture")
        wait(console, process, lambda s: "QUESTION" in s["text"] and "保留现有实现" in s["text"], "question to cancel")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "Paused / cancelled" in s["text"] and "NEXT MESSAGE" not in s["text"], "question cancellation pauses turn")
        assert SlowProvider.calls.count("question cancel fixture") == 1, SlowProvider.calls
        evidence["checks"].append("model-question-Esc-cancels-without-sending-an-answer")
        console.command("pending insertion fixture")
        wait(console, process, lambda s: "NEXT MESSAGE" in s["text"] and "slow line 0 中文" in s["text"], "turn for pending insertion")
        console.command("新增条件：只修改渲染")
        pending = wait(console, process, lambda s: "QUEUED" in s["text"] and "新增条件：只修改渲染" in s["text"], "grey pending insertion above composer")
        pending_index = next(i for i, row in enumerate(pending["rows"]) if "新增条件：只修改渲染" in row["text"])
        composer_index = next(i for i, row in enumerate(pending["rows"]) if "NEXT MESSAGE" in row["text"])
        assert pending_index < composer_index, pending["text"]
        assert any((chr(character) if isinstance(character, int) else character).strip() and attribute & 0x0f == 8 for character, attribute in pending["rows"][pending_index]["cells"]), pending["rows"][pending_index]
        evidence["snapshots"]["pending-insertion"] = pending
        slash("/model")
        wait(console, process, lambda s: "MODELS  /" in s["text"], "picker while insertion pending")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "MODELS  /" not in s["text"] and "QUEUED" in s["text"] and "NEXT MESSAGE" in s["text"], "overlay Esc leaves pending and active turn intact")
        console.inject("保留草稿")
        wait(console, process, lambda s: "保留草稿" in s["text"], "draft before recall")
        console.key(0x1B, "\x1b")
        recalled = wait(console, process, lambda s: "QUEUED" not in s["text"] and "新增条件：只修改渲染" in s["text"] and "保留草稿" in s["text"] and "NEXT MESSAGE" in s["text"], "Esc recalls insertion while preserving draft and active turn")
        assert "新增条件：只修改渲染" not in SlowProvider.calls, SlowProvider.calls
        evidence["snapshots"]["recalled-insertion"] = recalled
        console.key(0x43, "\x03", 8)
        wait(console, process, lambda s: "Paused / cancelled" in s["text"] and "NEXT MESSAGE" not in s["text"] and "保留草稿" in s["text"], "explicit cancellation after recall")
        console.key(0x23)  # End selects the end of the complete multiline draft.
        console.key(0, "\x15", 8)
        evidence["checks"].append("pending-grey-preview-overlay-focus-Esc-recall-and-draft-merge")
        console.command("local conveniences fixture")
        wait(console, process, lambda s: "Local answer" in s["text"] and "NEXT MESSAGE" not in s["text"], "answer for local code selector")
        model_calls = len(SlowProvider.calls)
        console.inject("暂存长草稿 中文")
        console.key(0x53, "\x13", 8)
        wait(console, process, lambda s: "stashed" in s["text"].lower() and "│ > 暂存长草稿" not in s["text"], "Ctrl+S temporarily stashes draft")
        slash("/history")
        wait(console, process, lambda s: "PROJECT PROMPTS" in s["text"], "project prompt history selector")
        console.inject("local conveniences fixture")
        wait(console, process, lambda s: "local conveniences fixture" in s["text"], "history search")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "History prompt inserted" in s["text"] and "PROJECT PROMPTS" not in s["text"] and "│ > local conveniences fixture" in s["text"], "history Enter inserts without sending")
        assert len(SlowProvider.calls) == model_calls, SlowProvider.calls
        console.key(0x53, "\x13", 8)
        wait(console, process, lambda s: "│ > 暂存长草稿 中文" in s["text"], "stash exchanges without loss")
        console.key(0x53, "\x13", 8)
        wait(console, process, lambda s: "│ > local conveniences fixture" in s["text"], "stash restores the exchanged draft")
        console.key(0, "\x15", 8)
        slash("/copy code")
        wait(console, process, lambda s: "COPY CODE" in s["text"] and "python" in s["text"], "complete code block selector")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "COPY CODE" not in s["text"], "copy selector cancel leaves clipboard untouched")
        assert len(SlowProvider.calls) == model_calls, SlowProvider.calls
        evidence["checks"].append("local-project-history-stash-exchange-and-code-selector-no-model-calls")
        console.command("approval fixture")
        wait(console, process, lambda s: "PERMISSION REQUIRED" in s["text"], "write permission")
        console.inject("yes")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "PERMISSION REQUIRED" not in s["text"] and "NEXT MESSAGE" not in s["text"], "default deny completion", timeout=20)
        assert not (workspace / "must-not-write.txt").exists()
        evidence["checks"].append("fresh-default-deny-approval-isolated-from-draft")
        console.command("diff fixture")
        preview = wait(console, process, lambda s: "PERMISSION REQUIRED" in s["text"] and "- old value" in s["text"] and "+ new value" in s["text"], "numbered color diff approval")
        assert (workspace / "preview.txt").read_text(encoding="utf-8") == "context\nold value\nending\n"
        for marker, foreground in (("- old value", 4), ("+ new value", 2)):
            row = next(row for row in preview["rows"] if marker in row["text"])
            assert re.search(r"\b2\s+" + re.escape(marker), row["text"]), row
            start = row["text"].index(marker)
            diff_cells = row["cells"][start:start + len(marker)]
            assert any((attrs & 7) == foreground and (chr(character) if isinstance(character, int) else character).strip() for character, attrs in diff_cells), row
            assert all((attrs & 0xf0) == 0 for _, attrs in diff_cells), row
        evidence["snapshots"]["diff-approval"] = preview
        console.key(0x26)
        console.key(0x0D, "\r")
        applied = wait(console, process, lambda s: "+ new value" in s["text"] and "PERMISSION REQUIRED" not in s["text"] and "NEXT MESSAGE" not in s["text"], "applied diff card")
        assert (workspace / "preview.txt").read_text(encoding="utf-8") == "context\nnew value\nending\n"
        evidence["snapshots"]["diff-applied"] = applied
        evidence["checks"].append("real-edit-numbered-red-green-diff-before-approval-and-after-application")
        slash("/queue resume")
        wait(console, process, lambda s: "Queue resumed" in s["text"], "explicitly resume dispatch after earlier cancellations")
        console.command("queue fixture")
        wait(console, process, lambda s: "NEXT MESSAGE" in s["text"] and "slow line 0 中文" in s["text"], "queued turn starts")
        console.command("queued after picker")
        wait(console, process, lambda s: "1 queued" in s["text"], "one queued task")
        slash("/model")
        wait(console, process, lambda s: "MODELS  /" in s["text"] and "NEXT MESSAGE" not in s["text"], "picker holds focus after completion")
        time.sleep(0.15)
        assert "queued after picker" not in SlowProvider.calls, SlowProvider.calls
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "Queued answer 中文" in s["text"] and "NEXT MESSAGE" not in s["text"], "queued turn dispatches after picker closes")
        assert SlowProvider.calls.count("queued after picker") == 1, SlowProvider.calls
        evidence["checks"].append("queued-work-waits-for-picker-and-dispatches-once")

        console.command("queue edit fixture")
        wait(console, process, lambda s: "NEXT MESSAGE" in s["text"] and "slow line 0 中文" in s["text"], "production queue editor starts")
        console.command("production queued task")
        wait(console, process, lambda s: "1 queued" in s["text"], "production queued task")
        console.inject("production draft 中文")
        console.key(0x51, "\x11", 8)
        wait(console, process, lambda s: "QUEUED TASKS" in s["text"], "production queue manager")
        down_to(console, process, "Task 1")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "QUEUED TASK 1" in s["text"], "production queue actions")
        down_to(console, process, "View complete task")
        down_to(console, process, "Edit queued task")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "EDIT QUEUED TASK" in s["text"], "production queued editor")
        console.key(0x55, "\x15", 8)
        console.inject("production edited task")
        console.key(0x0D, "\r")
        saved_queue = wait(console, process, lambda s: "QUEUED TASKS" in s["text"] and "production edited task" in s["text"] and "production draft 中文" in s["text"], "production queued save")
        assert "production edited task" not in SlowProvider.calls and "production queued task" not in SlowProvider.calls
        evidence["snapshots"]["production-queue-edited"] = saved_queue
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "QUEUED TASKS" not in s["text"], "close production queue manager")
        console.key(0x55, "\x15", 8)
        console.command("production cancelled task")
        wait(console, process, lambda s: "2 queued" in s["text"], "second production queued task")
        console.inject("production draft 中文")
        console.key(0x51, "\x11", 8)
        wait(console, process, lambda s: "QUEUED TASKS" in s["text"], "production queue cancellation")
        down_to(console, process, "Task 1")
        down_to(console, process, "Task 2")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "QUEUED TASK 2" in s["text"], "second queue actions")
        down_to(console, process, "View complete task")
        down_to(console, process, "Edit queued task")
        down_to(console, process, "Cancel this queued task")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "QUEUED TASKS" in s["text"] and "production cancelled task" not in s["text"], "cancel second queued task")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "QUEUED TASKS" not in s["text"], "close cancelled queue")
        console.key(0x43, "\x03", 8)
        wait(console, process, lambda s: "NEXT MESSAGE" not in s["text"] and "queue paused" in s["text"], "active request stops while edited queue stays paused", timeout=20)
        assert "production edited task" not in SlowProvider.calls and "production cancelled task" not in SlowProvider.calls
        console.key(0x51, "\x11", 8)
        wait(console, process, lambda s: "QUEUED TASKS" in s["text"], "explicit production queue resume")
        down_to(console, process, "Task 1")
        down_to(console, process, "Resume queued tasks")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Queue edit answer 中文" in s["text"] and "NEXT MESSAGE" not in s["text"] and "production draft 中文" in s["text"], "edited production task executes once")
        assert SlowProvider.calls.count("production edited task") == 1 and "production cancelled task" not in SlowProvider.calls
        console.key(0x55, "\x15", 8)
        evidence["checks"].append("production-queue-edit-cancel-explicit-resume-and-draft-isolation")

        def checkpoint_write(number):
            console.command("checkpoint fixture " + str(number))
            wait(console, process, lambda s: "PERMISSION REQUIRED" in s["text"], "checkpoint write permission")
            console.key(0x26)
            wait(console, process, lambda s: "› Allow this operation" in s["text"], "explicit checkpoint write allowance")
            console.key(0x0D, "\r")
            wait(console, process, lambda s: "PERMISSION REQUIRED" not in s["text"] and "NEXT MESSAGE" not in s["text"], "checkpoint write completion", timeout=20)
            assert (workspace / "checkpoint.txt").read_text(encoding="utf-8") == "after-" + str(number)

        checkpoint_write(1)
        slash("/rewind")
        wait(console, process, lambda s: "Choose a file edit" in s["text"] and "checkpoint.txt" in s["text"], "checkpoint chooser")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Confirm exact file restore" in s["text"], "checkpoint confirmation")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Confirm exact file restore" not in s["text"], "default checkpoint cancellation")
        assert (workspace / "checkpoint.txt").read_text(encoding="utf-8") == "after-1"
        slash("/rewind")
        wait(console, process, lambda s: "Choose a file edit" in s["text"], "checkpoint chooser again")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Confirm exact file restore" in s["text"], "checkpoint confirmation again")
        down_to(console, process, "Restore this file checkpoint")
        console.key(0x0D, "\r")
        restored = wait(console, process, lambda s: "File checkpoint restored" in s["text"], "checkpoint restored")
        assert (workspace / "checkpoint.txt").read_text(encoding="utf-8") == "before"
        evidence["snapshots"]["rewind-restored"] = restored
        evidence["checks"].append("native-file-checkpoint-default-cancel-and-explicit-restore")

        checkpoint_write(2)
        (workspace / "checkpoint.txt").write_text("external change", encoding="utf-8")
        slash("/rewind")
        wait(console, process, lambda s: "Choose a file edit" in s["text"] and "checkpoint.txt" in s["text"], "external-change checkpoint chooser")
        console.key(0x0D, "\r")
        conflict = wait(console, process, lambda s: "Checkpoint cannot be restored" in s["text"] and "Choose a file edit" not in s["text"], "external-change restore refusal")
        assert "Confirm exact file restore" not in conflict["text"]
        assert (workspace / "checkpoint.txt").read_text(encoding="utf-8") == "external change"
        evidence["snapshots"]["rewind-external-conflict"] = conflict
        evidence["checks"].append("native-file-checkpoint-refuses-external-change")

        console.inject("/consult latency fixture")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "NEXT MESSAGE" in s["text"] and SlowProvider.latency_active == 4, "four concurrent loopback SSE streams")
        samples = []
        expected = ""
        for index in range(40):
            assert SlowProvider.latency_active == 4, (index, SlowProvider.latency_active)
            character = "abcdefghijklmnopqrstuvwxyz0123456789ABCD"[index]
            expected += character
            started = time.perf_counter_ns()
            console.inject(character)
            deadline = time.perf_counter() + 1
            while True:
                screen = console.read(viewport=True)
                if expected in screen["text"]:
                    samples.append((time.perf_counter_ns() - started) / 1_000_000)
                    break
                if time.perf_counter() > deadline:
                    raise AssertionError("Input did not become visible under four SSE streams")
                time.sleep(0.001)
        ordered = sorted(samples)
        p95 = ordered[math.ceil(0.95 * len(ordered)) - 1]
        evidence["input_latency"] = {
            "samples": len(samples), "samples_ms": samples, "p50_ms": ordered[len(ordered) // 2],
            "p95_ms": p95, "maximum_ms": max(samples), "maximum_active_provider_streams": SlowProvider.latency_maximum,
            "method": "WriteConsoleInputW injection to first ReadConsoleOutputW viewport containing the appended composer text; 1 ms polling; foreground final CLI with four active loopback SSE consult requests",
            "scope": "Local Windows console and loopback provider load; no claim about remote API or terminal hosts not measured here",
        }
        assert p95 < 50, evidence["input_latency"]
        evidence["snapshots"]["four-stream-input"] = screen
        evidence["checks"].append("four-real-sse-streams-input-visible-p95-below-50ms")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "NEXT MESSAGE" not in s["text"] and expected in s["text"], "cancel four streams and retain draft", timeout=20)
        console.key(0x55, "\x15", 8)
        model_calls = len(SlowProvider.calls)
        console.inject('\x1b[200~"' + str(image_path) + '"\x1b[201~')
        chip = wait(console, process, lambda s: "[image1]" in s["text"], "original image path becomes a chip")
        chip_row = next(row for row in chip["rows"] if "[image1]" in row["text"])
        chip_column = chip_row["text"].index("[image1]")
        assert all((attribute & 7) == 1 for _, attribute in chip_row["cells"][chip_column:chip_column + 8]), chip_row
        evidence["snapshots"]["blue-image-chip"] = chip
        console.key(0x08, "\x08")
        wait(console, process, lambda s: "[image1]" not in s["text"], "single Backspace removes entire image chip")
        assert image_path.read_bytes() == original_png and len(SlowProvider.calls) == model_calls
        console.inject("image submission fixture ")
        console.inject('\x1b[200~"' + str(second_image_path) + '"\x1b[201~')
        wait(console, process, lambda s: "[image2]" in s["text"], "image chip numbering remains stable")
        second_image_path.unlink()
        console.key(0x0D, "\r")
        # Permission status has priority in the bounded footer. Assert the
        # actual restored draft and visible error, not a clipped prose suffix.
        rejected_image = wait(console, process, lambda s: "image submission fixture  [image2]" in s["text"] and "Image file is missing" in s["text"] and "NEXT MESSAGE" not in s["text"], "missing image restores the chip and draft before a provider call")
        assert len(SlowProvider.calls) == model_calls, SlowProvider.calls
        evidence["snapshots"]["missing-image-draft-retained"] = rejected_image
        second_image_path.write_bytes(original_png)
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "image bytes verified" in s["text"] and "NEXT MESSAGE" not in s["text"], "explicit submission sends actual image bytes")
        assert image_path.read_bytes() == original_png and second_image_path.read_bytes() == original_png
        assert not (workspace / ".sencode" / "attachments").exists()
        evidence["checks"].append("original-image-blue-atomic-chip-and-real-multimodal-request-no-project-copy")
        evidence["checks"].append("missing-image-preflight-retains-draft-and-makes-no-provider-call")
        stop()
        evidence["checks"].append("final-main-terminal-restoration")

        process = launch("-r")
        wait(console, process, lambda s: "Resume a project session" in s["text"], "sen -r shortcut")
        console.key(0x1B, "\x1b")
        stop()
        evidence["checks"].append("resume-flag-shortcut-and-second-exit-restoration")
        evidence["requests"] = SlowProvider.calls
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None:
            try:
                evidence["last_screen"] = console.read(viewport=True)
            except BaseException:
                pass
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        for written_target in reversed(written_targets):
            checked(advapi.CredDeleteW(written_target, 1, 0))
        server.shutdown()
        server.server_close()
        write_json(args.evidence, evidence)


def controller(args):
    kernel = kernel_api()
    scratch = Path(tempfile.mkdtemp(prefix="sencode-fullscreen-"))
    ready = scratch / "ready"
    job = checked(kernel.CreateJobObjectW(None, None))
    process = None
    try:
        limits = JobExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000
        checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        child_args = [sys.executable, str(Path(__file__).resolve()), str(args.executable),
                                    "--worker", "--scratch", str(scratch), "--ready", str(ready),
                                    "--evidence", str(args.evidence)]
        if args.production:
            child_args.append("--production")
        process = subprocess.Popen(child_args, startupinfo=startup,
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
        checked(kernel.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)))
        ready.write_text("assigned", encoding="ascii")
        code = process.wait(timeout=150)
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        if code or evidence["result"] != "passed":
            raise AssertionError(evidence.get("error", f"Worker failed {code}"))
        print(f"Real full-screen console: {len(evidence['checks'])} checks passed")
        print(f"Evidence: {args.evidence}")
    finally:
        checked(kernel.CloseHandle(job))
        if process is not None:
            process.wait(timeout=5)
        remove_owned_tree(scratch)


def main():
    if os.name != "nt":
        raise SystemExit("This gate requires an actual Windows console")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[1] / "target/fullscreen-console-evidence.json")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--ready", type=Path)
    parser.add_argument("--production", action="store_true", help="Drive final CLI with an isolated DB and loopback provider")
    args = parser.parse_args()
    args.executable = args.executable.resolve(strict=True)
    args.evidence = args.evidence.resolve()
    if args.worker:
        worker(args)
    else:
        controller(args)


if __name__ == "__main__":
    main()
