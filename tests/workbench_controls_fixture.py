"""Owned native Windows console gate for Agent cards, effort and permissions.

Only disposable projects, an isolated catalog, a random fixture credential and
a loopback synthetic provider are used. No user state, clipboard or paid API.
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
import re
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import uuid

import agent_reliability_fixture as harness
from cli_fixture import Credential
from fullscreen_console_fixture import wait
from tui_console_fixture import Console, checked, environment_for, write_json


class Provider(harness.Provider):
    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            length = int(self.headers["Content-Length"])
            assert 0 < length <= 1048576
            request = json.loads(self.rfile.read(length))
            self.server.requests.append(request)
            history = request["messages"]
            latest = max(i for i, value in enumerate(history) if value["role"] == "user")
            prompt = history[latest]["content"]
            results = [value for value in history[latest + 1:] if value["role"] == "tool"]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            tool = None
            if prompt == "agent controls fixture":
                if not results:
                    self.event("PARENT_CHILD_START\n")
                    tool = ("parent-spawn", "spawn_agent", {"role": "explore", "prompt": "child controls fixture"})
                else:
                    value = json.loads(results[-1]["content"])
                    children = value.get("children", [])
                    if children and all(child["done"] for child in children):
                        assert all(child["error"] == 0 for child in children), children
                        self.event("PARENT_CHILD_DONE\n", done=True)
                    else:
                        assert len(results) < 15, "Child failed to settle within fixture request budget"
                        tool = (f"parent-wait-{len(results)}", "wait_agents", {"timeout_ms": 1000})
            elif prompt == "child controls fixture":
                if not results:
                    self.server.child_started.set()
                    for part in ("子代理正在只读检查", "中文源码和项目结构", "，准备读取文件。\n"):
                        self.event(part)
                        time.sleep(.18)
                    tool = ("child-read", "read_file", {"path": "fixture.txt"})
                else:
                    value = json.loads(results[-1]["content"])
                    assert not value["is_error"] and "fixture content 中文" in value["content"], value
                    self.server.child_read_verified = True
                    self.event("已核实文件内容；子代理只读检查完成。\n")
                    time.sleep(.35)
                    self.event(done=True)
            elif prompt == "manual approval fixture":
                if not results:
                    self.event("MANUAL_ACTIVE_BEFORE_TOOL\n")
                    self.server.manual_started.set()
                    time.sleep(.8)
                    tool = ("manual-write", "write_file", {"path": "manual-edit.txt", "content": "must require manual approval\n"})
                else:
                    self.event("MANUAL_RESULT\n", done=True)
            elif prompt == "auto edit fixture":
                if not results:
                    tool = ("auto-write", "write_file", {"path": "auto-edit.txt", "content": "auto edit fixture\n"})
                else:
                    assert not json.loads(results[-1]["content"])["is_error"], results
                    self.event("AUTO_EDIT_DONE\n", done=True)
            elif prompt == "slow captured target fixture":
                self.event("SLOW_CAPTURED_TARGET_ACTIVE\n")
                self.server.slow_started.set()
                assert self.server.slow_release.wait(timeout=20), "Slow target gate was not released"
                self.event("SLOW_CAPTURED_TARGET_DONE\n", done=True)
            elif prompt == "after target switch fixture":
                self.event("NEXT_CAPTURED_TARGET_DONE\n", done=True)
            elif prompt == "manual model fixture":
                self.event("MANUAL_MODEL_DONE\n", done=True)
            elif prompt in {"default effort fixture", "xhigh effort fixture"}:
                self.event("DEFAULT_EFFORT_DONE\n" if prompt.startswith("default") else "XHIGH_EFFORT_DONE\n", done=True)
            else:
                raise AssertionError(("Unexpected fixture prompt", prompt))
            if tool:
                self.event(tool=tool)
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except BaseException:
            self.server.errors.append(traceback.format_exc())
        finally:
            self.close_connection = True


def worker(args):
    evidence = {
        "schema": 1, "result": "running", "platform": "windows-x64",
        "host": os.environ.get("COMPUTERNAME"), "binary": str(args.executable),
        "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
        "fixture_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Owned hidden native Windows console and disposable workspace; synthetic loopback API only",
        "checks": [], "snapshots": {},
    }
    process = None
    credential_written = False
    target = "Sencode/connection/workbench-controls-" + uuid.uuid4().hex
    identifier = target.rsplit("/", 1)[1]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests, server.errors = [], []
    server.child_started, server.manual_started = threading.Event(), threading.Event()
    server.slow_started, server.slow_release = threading.Event(), threading.Event()
    server.child_read_verified = False
    threading.Thread(target=server.serve_forever, daemon=True).start()
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
    advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi.CredDeleteW.restype = wintypes.BOOL

    def record(name, condition, detail=None):
        item = {"name": name, "status": "passed" if condition else "failed"}
        if detail is not None:
            item["detail"] = detail
        evidence["checks"].append(item)

    def footer(screen):
        lines = screen["text"].splitlines()
        bottoms = [i for i, value in enumerate(lines) if "╰" in value]
        return "\n".join(lines[bottoms[-1] + 1:]) if bottoms else ""

    def footer_color(screen, label):
        row = screen["rows"][-2]
        return next(int(attribute) & 0xF for character, attribute in row["cells"] if character == ord(label[0]))

    def header(screen, effort):
        return any("fixture" in row["text"] and effort in row["text"] for row in screen["rows"][:3])

    def exact_header(screen, model, effort):
        return any(re.search(r"(?<![\w-])" + re.escape(model) + r"(?![\w-])", row["text"]) and effort in row["text"] for row in screen["rows"][:3])

    def composer(screen):
        lines = screen["text"].splitlines()
        starts = [i for i, value in enumerate(lines) if "╭" in value]
        ends = [i for i, value in enumerate(lines) if "╰" in value]
        return "\n".join(lines[starts[-1]:ends[-1] + 1]) if starts and ends else ""

    def plain_request(prompt):
        return [body for body in server.requests if body["messages"][-1].get("content") == prompt]

    def clear_draft():
        console.key(0x55, "\x15", 8)
        time.sleep(.12)

    def submit(prompt):
        clear_draft()
        console.inject(prompt)
        wait(console, process, lambda screen: prompt in screen["text"], "fixture composer")
        console.key(0x0D, "\r")

    def completed(marker, timeout=15):
        return wait(console, process, lambda screen: marker in screen["text"] and "NEXT MESSAGE" not in screen["text"], marker, timeout)

    def shift_tab():
        console.key(0x09, "\t", 0x10)
        time.sleep(.14)
        return console.read(viewport=True)

    def slash(name, value=""):
        clear_draft()
        console.inject(name)
        wait(console, process, lambda screen: "COMMANDS" in screen["text"], name + " command menu")
        console.key(0x0D, "\r")
        wait(console, process, lambda screen: "COMMANDS" not in screen["text"] and name in composer(screen), name + " completed")
        if value:
            console.inject(value)
            screen = wait(console, process, lambda screen: name + " " + value in composer(screen), name + " arguments")
            if "COMMAND ARGUMENTS" in screen["text"]:
                console.key(0x0D, "\r")
                wait(console, process, lambda screen: "COMMAND ARGUMENTS" not in screen["text"], name + " arguments completed")
        console.key(0x0D, "\r")

    def pick_model_effort(model, effort):
        slash("/model")
        wait(console, process, lambda screen: "MODELS  /" in screen["text"], "model picker")
        if model:
            console.inject(model)
            wait(console, process, lambda screen: "MODELS  /  " + model in screen["text"] and "› " + model in screen["text"], "filtered model")
        console.key(0x0D, "\r")
        wait(console, process, lambda screen: "Thinking effort /" in screen["text"] and effort in screen["text"], "effort picker")
        console.inject(effort)
        wait(console, process, lambda screen: "› " + effort in screen["text"], "filtered effort")
        console.key(0x0D, "\r")
        return wait(console, process, lambda screen: "Thinking effort /" not in screen["text"], "effort applied")

    try:
        deadline = time.monotonic() + 8
        while not args.ready.exists():
            assert time.monotonic() < deadline, "Owned Job was not established"
            time.sleep(.02)
        environment = environment_for(args.scratch)
        os.environ.clear()
        os.environ.update(environment)
        workspace = args.scratch / "workspace-中文"
        workspace.mkdir()
        (workspace / "fixture.txt").write_text("fixture content 中文\n", encoding="utf-8")
        database = args.scratch / "isolated.sqlite"
        common = ["--cwd", str(workspace), "--database", str(database), "--connection", identifier]
        initialized = subprocess.run([str(args.executable), *common, "doctor"], capture_output=True, timeout=25)
        assert initialized.returncode == 0, initialized.stderr.decode(errors="replace")
        key = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
        credential = Credential(Type=1, TargetName=target, CredentialBlobSize=11, CredentialBlob=key, Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(credential), 0))
        credential_written = True
        config = {
            "version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
            "protocol": "chatCompletions", "successfulProtocol": "chatCompletions",
            "selectedModelId": "fixture", "credentialRef": target,
            "enabledModels": [{"id": model, "label": model, "capabilities": {
                "reasoningEffort": True, "supportedReasoningEfforts": ["medium", "xhigh"]}}
                for model in ("fixture", "fixture-next")],
        }
        with sqlite3.connect(database) as connection:
            connection.create_function("sengoo_context", 1, lambda name: "workbench-controls" if name == "instance_id" else None)
            connection.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','workbench fixture',?,'fixture',1,1)", (identifier, json.dumps(config)))
            connection.commit()
        console = Console()
        console.resize(140, 46)
        console.clear()
        baseline = console.modes()
        process = subprocess.Popen([str(args.executable), *common], cwd=workspace)
        home = wait(console, process, lambda screen: "MESSAGE" in screen["text"], "workbench home", 20)
        evidence["snapshots"]["home"] = home
        record("initial-footer-displays-manual-permissions", "手动审批" in footer(home) and "Shift+Tab" in footer(home))
        record("manual-permission-footer-is-light-blue", footer_color(home, "手动审批") == 11)

        submit("default effort fixture")
        default = completed("DEFAULT_EFFORT_DONE")
        evidence["snapshots"]["default-effort"] = default
        sent = plain_request("default effort fixture")
        record("default-medium-header-and-actual-provider-request", header(default, "medium") and len(sent) == 1 and sent[0].get("reasoning_effort") == "medium", {"header": default["rows"][0]["text"], "sent_effort": sent[0].get("reasoning_effort") if sent else None})

        draft = "permission draft 中文"
        console.inject(draft)
        wait(console, process, lambda screen: draft in screen["text"], "permission cycle draft")
        cycle = [shift_tab(), shift_tab(), shift_tab()]
        evidence["snapshots"]["permission-cycle"] = cycle
        record("shift-tab-cycles-manual-auto-full-manual-with-draft-preserved", all(mode in footer(screen) and draft in screen["text"] for mode, screen in zip(("自动审批", "完全权限", "手动审批"), cycle)), {"footers": [footer(screen) for screen in cycle]})
        record("auto-yellow-full-red-manual-light-blue-console-colors", [footer_color(screen, label) for screen, label in zip(cycle, ("自动审批", "完全权限", "手动审批"))] == [6, 4, 11])
        clear_draft()

        slash("/permissions", "backend")
        backend = wait(console, process, lambda screen: "/permissions backend" not in composer(screen), "native backend policy rejection")
        evidence["snapshots"]["native-backend-policy-rejected"] = backend
        backend_picker = "Confirm managed-account permission policy" in backend["text"]
        record("native-api-rejects-managed-backend-policy-and-keeps-native-footer", not backend_picker and "手动审批" in footer(backend) and "后端权限" not in footer(backend))
        if backend_picker:
            # A broken candidate must not leave the picker open and invalidate
            # the following checks. Record the failure, then dismiss it.
            console.key(0x1B, "\x1b")
            wait(console, process, lambda screen: "Confirm managed-account permission policy" not in screen["text"], "dismiss invalid backend picker")

        submit("slow captured target fixture")
        assert server.slow_started.wait(timeout=8), "Slow provider request not observed"
        slow_before = wait(console, process, lambda screen: "SLOW_CAPTURED_TARGET_ACTIVE" in screen["text"] and "NEXT MESSAGE" in screen["text"], "captured target active")
        switched = pick_model_effort("fixture-next", "xhigh")
        evidence["snapshots"]["captured-target-before-switch"] = slow_before
        evidence["snapshots"]["captured-target-after-switch"] = switched
        sent = plain_request("slow captured target fixture")
        record("busy-model-change-keeps-current-header-and-captured-provider-target", exact_header(slow_before, "fixture", "medium") and exact_header(switched, "fixture", "medium") and not exact_header(switched, "fixture-next", "xhigh") and len(sent) == 1 and sent[0].get("model") == "fixture" and sent[0].get("reasoning_effort") == "medium")
        server.slow_release.set()
        completed("SLOW_CAPTURED_TARGET_DONE")
        submit("after target switch fixture")
        switched_next = completed("NEXT_CAPTURED_TARGET_DONE")
        evidence["snapshots"]["captured-target-next-request"] = switched_next
        sent = plain_request("after target switch fixture")
        record("next-request-uses-new-model-and-effort-after-busy-switch", exact_header(switched_next, "fixture-next", "xhigh") and len(sent) == 1 and sent[0].get("model") == "fixture-next" and sent[0].get("reasoning_effort") == "xhigh")

        # This explicitly entered model is absent from enabledModels. It must
        # remain callable and inherit the connection's native medium default.
        slash("/model", "manual-fixture")
        manual_target = wait(console, process, lambda screen: exact_header(screen, "manual-fixture", "medium"), "manual model medium default")
        evidence["snapshots"]["manual-model-selected"] = manual_target
        submit("manual model fixture")
        manual_done = completed("MANUAL_MODEL_DONE")
        evidence["snapshots"]["manual-model-request"] = manual_done
        sent = plain_request("manual model fixture")
        record("manually-entered-unenabled-model-sends-with-default-medium", exact_header(manual_done, "manual-fixture", "medium") and len(sent) == 1 and sent[0].get("model") == "manual-fixture" and sent[0].get("reasoning_effort") == "medium")
        slash("/model", "fixture")
        wait(console, process, lambda screen: exact_header(screen, "fixture", "medium"), "enabled model restored")

        # Complete /model with one Enter, then explicitly submit it. Filter the
        # effort picker so old/new highlight defaults do not affect selection.
        pick_model_effort("fixture", "xhigh")
        submit("xhigh effort fixture")
        selected = completed("XHIGH_EFFORT_DONE")
        evidence["snapshots"]["xhigh-effort"] = selected
        sent = plain_request("xhigh effort fixture")
        record("selected-xhigh-header-and-actual-provider-request", header(selected, "xhigh") and len(sent) == 1 and sent[0].get("reasoning_effort") == "xhigh")

        submit("agent controls fixture")
        assert server.child_started.wait(timeout=10), "Child provider request not observed"
        live_draft = "child run draft 中文"
        console.inject(live_draft)
        samples = []
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            screen = console.read(viewport=True)
            samples.append(screen)
            if "PARENT_CHILD_DONE" in screen["text"] and "NEXT MESSAGE" not in screen["text"]:
                break
            assert process.poll() is None, "CLI exited during child turn"
            time.sleep(.035)
        else:
            raise AssertionError("Child workbench turn did not complete")
        evidence["snapshots"]["agent-live-samples"] = samples
        text = "\n".join(sample["text"] for sample in samples)
        internal = ('{"agent"', '"text_delta"', '"connection_id"', identifier)
        record("native-child-stream-and-read-complete-without-wire-json", server.child_read_verified and all(value not in text for value in internal) and "子代理" in text and "read_file" in text, {"read_verified": server.child_read_verified, "raw_markers_found": [value for value in internal if value in text]})
        counts = [len(re.findall(r"Agent #\d+", sample["text"])) for sample in samples]
        record("one-stable-child-card-and-live-draft-preserved", max(counts, default=0) == 1 and live_draft in samples[-1]["text"] and any("Agent #" in sample["text"] and "completed" in sample["text"] for sample in samples), {"maximum_agent_card_headers": max(counts, default=0)})
        clear_draft()

        # Start in manual. Change the next request mode while the provider is
        # still responding; the current request must still require approval.
        submit("manual approval fixture")
        assert server.manual_started.wait(timeout=8)
        active = shift_tab()
        evidence["snapshots"]["busy-next-permission"] = active
        record("busy-mode-change-shows-active-manual-and-next-auto", "手动审批" in footer(active) and "下轮" in footer(active) and "自动审批" in footer(active))
        record("busy-current-and-next-permissions-retain-own-colors", footer_color(active, "手动审批") == 11 and footer_color(active, "自动审批") == 6)
        approval = wait(console, process, lambda screen: "PERMISSION REQUIRED" in screen["text"], "captured manual request approval", 8)
        evidence["snapshots"]["approval-before-shift-tab"] = approval
        record("current-manual-request-still-requires-approval-after-busy-cycle", not (workspace / "manual-edit.txt").exists())
        after_shift = shift_tab()
        evidence["snapshots"]["approval-after-shift-tab"] = after_shift
        def selected_approval(screen):
            return [row["text"].strip() for row in screen["rows"] if "› " in row["text"]]
        record("approval-modal-shift-tab-does-not-cycle-or-change-selection", "PERMISSION REQUIRED" in after_shift["text"] and footer(approval) == footer(after_shift) and selected_approval(approval) == selected_approval(after_shift), {"before": selected_approval(approval), "after": selected_approval(after_shift)})
        console.key(0x0D, "\r")
        stopped = wait(console, process, lambda screen: "PERMISSION REQUIRED" not in screen["text"] and "NEXT MESSAGE" not in screen["text"], "default no refuses manual write", 10)
        record("default-no-after-shift-tab-never-writes", not (workspace / "manual-edit.txt").exists())
        evidence["snapshots"]["approval-ended"] = stopped
        # The auto choice was queued for later requests, so the next edit may
        # execute automatically while general commands remain untested here.
        submit("auto edit fixture")
        auto = completed("AUTO_EDIT_DONE", 10)
        evidence["snapshots"]["auto-next-request"] = auto
        record("next-request-uses-selected-auto-edit-policy", (workspace / "auto-edit.txt").read_text(encoding="utf-8") == "auto edit fixture\n" and "自动审批" in footer(auto))

        assert not server.errors, server.errors
        clear_draft()
        console.key(0x44, "\x04", 8)
        process.wait(timeout=12)
        record("native-terminal-modes-and-codepages-restored", process.returncode == 0 and console.modes() == baseline)
        evidence["result"] = "passed" if all(item["status"] == "passed" for item in evidence["checks"]) else "failed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None:
            try:
                evidence["last_screen"] = console.read(viewport=True)
            except BaseException:
                pass
    finally:
        server.slow_release.set()
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        if credential_written:
            checked(advapi.CredDeleteW(target, 1, 0))
        server.shutdown()
        server.server_close()
        evidence["provider_errors"] = server.errors
        evidence["requests"] = [{"model": request.get("model"), "reasoning_effort": request.get("reasoning_effort"), "messages": len(request.get("messages", []))} for request in server.requests]
        evidence["credential_removed"] = credential_written
        write_json(args.evidence, evidence)
    return 0 if evidence["result"] == "passed" else 1


def main():
    if os.name != "nt":
        raise SystemExit("This fixture requires an owned native Windows console")
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
    harness.__file__ = __file__
    return harness.controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
