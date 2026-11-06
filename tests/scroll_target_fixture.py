"""Real console scrolling and session target gate against the product executable.

Owns an isolated profile, console Job, project archives and random fixture-only
credentials. Provider requests go exclusively to a synthetic loopback server.
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
import re
import sqlite3
import struct
import subprocess
import threading
import time
import traceback
import uuid

import agent_reliability_fixture as harness
from cli_fixture import Credential
from fullscreen_console_fixture import wait
from terminal_pane_console_fixture import resize_fullscreen
from tui_console_fixture import Console, InputRecord, checked, environment_for, write_json


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *_): pass
    def event(self, text, done=False):
        value = {"choices": [{"delta": {"content": text}, "finish_reason": "stop" if done else None}]}
        if done: value["usage"] = {"prompt_tokens": 15, "completion_tokens": 10}
        self.wfile.write(("data: " + json.dumps(value, ensure_ascii=False) + "\n\n").encode())
        self.wfile.flush()
    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            prompt = [v["content"] for v in request["messages"] if v["role"] == "user"][-1]
            self.server.requests.append({"lane": self.path.split("/")[1], "model": request["model"],
                                         "effort": request.get("reasoning_effort"), "prompt": prompt})
            self.send_response(200); self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close"); self.end_headers()
            if prompt == "HISTORY":
                self.event("\n".join(f"hist-{i:03d} 中文 `code-{i:03d}`" for i in range(180)) + "\n", True)
            elif prompt == "SLOW":
                self.event("SLOW_RUNNING\n")
                deadline = time.monotonic() + 12
                while not self.server.release.wait(.05) and time.monotonic() < deadline: pass
                self.event("SLOW_DONE", True)
            else:
                self.event("TARGET_ACK " + prompt, True)
            self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError): pass
        except BaseException: self.server.errors.append(traceback.format_exc())
        finally: self.close_connection = True


def wheel(console, delta, count=1):
    records = (InputRecord * count)()
    for record in records:
        record.EventType = 2
        value = struct.pack("<hhIII", 4, 5, (delta & 0xffff) << 16, 0, 4)
        ctypes.memmove(ctypes.byref(record.Event), value, 16)
    written = wintypes.DWORD()
    checked(console.kernel.WriteConsoleInputW(console.input, records, count, ctypes.byref(written)))
    assert written.value == count


def worker(args):
    evidence = {"schema": 1, "scope": "isolated real Windows console, project archive and loopback model routing",
                "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                "fixture_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "result": "running", "checks": [], "snapshots": {}, "scroll_latency_ms": {}}
    process = None; console = None; credentials = []
    fixture_id = "custom-target-" + uuid.uuid4().hex
    ids = [fixture_id + suffix for suffix in ("-a", "-b")]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.requests = []; server.errors = []; server.release = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]; advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]; advapi.CredDeleteW.restype = wintypes.BOOL

    def record(name, ok=True, detail=None):
        evidence["checks"].append({"name": name, "status": "passed" if ok else "failed", "detail": detail})
        assert ok, (name, detail)
    try:
        deadline = time.monotonic() + 10
        while not args.ready.exists():
            assert time.monotonic() < deadline
            time.sleep(.02)
        environment = environment_for(args.scratch); os.environ.clear(); os.environ.update(environment)
        workspace = args.scratch / "before 项目"; workspace.mkdir()
        database = args.scratch / "catalog.sqlite3"

        def run(*options, stdin="/exit\n", db=None, cwd=None, ok=True):
            directory = cwd or workspace
            result = subprocess.run([str(args.executable), "--cwd", str(directory), "--database", str(db or database),
                                     "--tui", "plain", *map(str, options)], cwd=directory, env=environment,
                                    input=stdin, capture_output=True, encoding="utf-8", timeout=30)
            assert (result.returncode == 0) == ok, (options, result.returncode, result.stdout, result.stderr)
            return result
        def sql(text, values=(), db=None):
            with closing(sqlite3.connect(db or database, timeout=5)) as connection:
                connection.create_function("sengoo_context", 1, lambda key: "target-fixture" if key == "instance_id" else None)
                rows = connection.execute(text, values).fetchall(); connection.commit(); return rows
        def seed(db):
            for lane, identifier in zip(("a", "b"), ids):
                config = {"baseUrl": f"http://127.0.0.1:{server.server_port}/{lane}", "protocol": "chatCompletions",
                          "enabledModels": [{"id": "one"}, {"id": "two"}]}
                sql("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed',?,?,'one',1,1)",
                    (identifier, "Provider " + lane.upper(), json.dumps(config)), db)
            sql("INSERT INTO app_preferences(key,value,updated_at) VALUES('preferred_connection_id',?,1) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (ids[0],), db)
        def target(session, db=None):
            row = sql("SELECT json_extract(mode_json,'$.cli_target') FROM shared_modes WHERE session_id=?", (session,), db)
            return json.loads(row[0][0]) if row and row[0][0] else None
        def eventually(predicate, description):
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if predicate(): return
                assert process is None or process.poll() is None, description
                time.sleep(.01)
            raise AssertionError(description)

        run(); seed(database)
        for identifier in ids:
            raw = (ctypes.c_ubyte * 11).from_buffer_copy(b"fixture-key")
            credential = Credential(Flags=0, Type=1, TargetName="Sencode/connection/" + identifier,
                                    CredentialBlobSize=11, CredentialBlob=raw, Persist=2, UserName="fixture")
            checked(advapi.CredWriteW(ctypes.byref(credential), 0)); credentials.append(credential.TargetName)
        run("--connection", ids[0], "-p", "HISTORY", "--output-format", "json")
        session = sql("SELECT id FROM sessions WHERE last_sent_at IS NOT NULL ORDER BY last_sent_at DESC LIMIT 1")[0][0]
        console = Console(); console.clear(); resize_fullscreen(console, 120, 40); baseline = console.modes()

        def launch(*options):
            nonlocal process
            console.clear()
            process = subprocess.Popen([str(args.executable), "--cwd", str(workspace), "--database", str(database), *map(str, options)], cwd=workspace, env=environment)
            return wait(console, process, lambda s: "MESSAGE" in s["text"] and "SENCODE" in s["text"], "fullscreen startup")
        def stop():
            nonlocal process
            console.key(0x44, "\x04", 8); process.wait(timeout=12)
            assert process.returncode == 0 and console.modes() == baseline
            process = None
        def slash(name):
            console.key(0x55, "\x15", 8); console.inject(name)
            wait(console, process, lambda s: "COMMANDS" in s["text"] and name in s["text"], "command menu")
            console.key(0x0D, "\r")
            wait(console, process, lambda s: "Command completed" in s["text"] and "COMMANDS" not in s["text"], "command completion")
            console.key(0x0D, "\r")
        def choose_b_two():
            slash("/model")
            wait(console, process, lambda s: "MODELS" in s["text"] and "Provider B" in s["text"], "model picker")
            console.inject("two"); time.sleep(.04); console.key(0x27)
            console.key(0x0D, "\r")
            wait(console, process, lambda s: "Thinking effort / two" in s["text"], "effort picker")
            console.key(0x28); console.key(0x28); console.key(0x0D, "\r")
            return wait(console, process, lambda s: "Thinking effort /" not in s["text"] and "xhigh" in s["text"], "selected tuple")
        def markers(screen): return [int(v) for v in re.findall(r"hist-(\d{3})", "\n".join(r["text"] for r in screen["rows"][2:-6]))]
        def scroll_wait(predicate):
            deadline = time.perf_counter() + 5
            while time.perf_counter() < deadline:
                frame = console.read(viewport=True)
                if predicate(frame): return frame
                assert process.poll() is None
                time.sleep(.002)
            raise AssertionError("Wheel viewport did not settle: " + frame["text"])

        first = launch("resume", session)
        composer = next(r["text"] for r in first["rows"] if "│ > " in r["text"])
        record("empty-composer-has-no-placeholder", composer.strip(" │>") == "", composer)
        for width in (80, 120, 160):
            resize_fullscreen(console, width, 40)
            console.key(0x23, "", 8)
            tail = wait(console, process, lambda s: s["width"] == width and 179 in markers(s), "tail at width")
            start = markers(tail)[0]
            wheel(console, 10, 4)
            small = wait(console, process, lambda s: markers(s) and markers(s)[0] == start - 1, "fractional wheel line")
            record(f"fractional-wheel-{width}", markers(small)[0] == start - 1)
            latencies = []
            for _ in range(10):
                begin_at = markers(console.read(viewport=True))[0]; started = time.perf_counter()
                wheel(console, 120)
                scroll_wait(lambda s: markers(s) and markers(s)[0] == begin_at - 3)
                latencies.append((time.perf_counter() - started) * 1000)
            evidence["scroll_latency_ms"][str(width)] = {"samples": latencies, "p95": sorted(latencies)[int(.95 * (len(latencies)-1))]}
            previous = console.read(viewport=True)
            resize_fullscreen(console, width, 38); time.sleep(.05); resize_fullscreen(console, width, 40)
            refreshed = wait(console, process, lambda s: s["height"] == 40 and markers(s) == markers(previous), "full viewport reconstruction")
            record(f"scroll-region-equals-full-repaint-{width}", [r["cells"] for r in refreshed["rows"][2:-6]] == [r["cells"] for r in previous["rows"][2:-6]])
            evidence["snapshots"][f"scrolled-{width}"] = refreshed
            console.key(0x24, "", 8)
            oldest = wait(console, process, lambda s: 0 in markers(s), "full oldest page")
            record(f"oldest-page-stays-full-{width}", len(markers(oldest)) >= 20)
        record("wheel-p95-below-50ms", all(v["p95"] < 50 for v in evidence["scroll_latency_ms"].values()), evidence["scroll_latency_ms"])
        console.key(0x23, "", 8)
        choose_b_two()
        eventually(lambda: target(session) == {"schema": 1, "connection": ids[1], "model": "two", "effort": "xhigh"}, "idle selection persistence")
        stop(); requests_before = len(server.requests)
        remembered = launch("-c")
        record("continue-remembers-unsent-supplier-model-effort", "two  xhigh" in remembered["rows"][0]["text"] and len(server.requests) == requests_before)
        evidence["snapshots"]["remembered-unsent"] = remembered; stop()
        for option in (("resume", session), ("-r", session)):
            screen = launch(*option)
            record("resume-entry-" + option[0], "two  xhigh" in screen["rows"][0]["text"]); stop()
        run("--connection", ids[0], "-p", "OTHER")
        other = sql("SELECT id FROM sessions WHERE title='OTHER'")[0][0]
        launch("resume", other)
        slash("/resume")
        wait(console, process, lambda s: "Resume a project session" in s["text"], "session picker")
        console.inject("HISTORY"); console.key(0x0D, "\r")
        restored = wait(console, process, lambda s: "Resume a project session" not in s["text"] and "two  xhigh" in s["rows"][0]["text"], "per-session selection restoration")
        record("in-app-resume-restores-each-conversation-target", target(other)["connection"] == ids[0] and target(session)["connection"] == ids[1])
        slash("/branch")
        branch = None
        def find_branch():
            nonlocal branch
            rows = sql("SELECT session_id FROM shared_modes WHERE json_extract(mode_json,'$.session_origin.kind')='branch' AND json_extract(mode_json,'$.session_origin.source_session_id')=?", (session,))
            if rows: branch = rows[0][0]
            return branch is not None and target(branch) is not None
        eventually(find_branch, "branch target copy")
        record("public-branch-inherits-model-memory", target(branch) == target(session))
        stop()
        run("resume", session, "-p", "RESTORED", "--output-format", "json")
        record("restored-request-routes-to-remembered-provider", server.requests[-1] == {"lane": "b", "model": "two", "effort": "xhigh", "prompt": "RESTORED"})
        run("resume", session, "--model", "one", "-p", "MODEL_OVERRIDE")
        record("explicit-model-keeps-supplier-and-resets-effort", server.requests[-1] == {"lane": "b", "model": "one", "effort": "medium", "prompt": "MODEL_OVERRIDE"})
        run("resume", session, "--effort", "low", "-p", "EFFORT_OVERRIDE")
        record("explicit-effort-wins", server.requests[-1]["lane"] == "b" and server.requests[-1]["effort"] == "low")
        launch("--connection", ids[0], "--model", "one", "resume", session)
        eventually(lambda: target(session)["connection"] == ids[0] and target(session)["effort"] == "medium", "unsent command-line target persistence")
        stop()
        overridden = launch("resume", session)
        record("unsent-command-line-selection-is-remembered", "one  medium" in overridden["rows"][0]["text"])
        console.command("SLOW")
        active = wait(console, process, lambda s: "SLOW_RUNNING" in s["text"] and "NEXT MESSAGE" in s["text"], "active immutable target")
        record("busy-empty-composer-has-no-placeholder", next(r["text"] for r in active["rows"] if "│ > " in r["text"]).strip(" │>") == "")
        choose_b_two()
        record("busy-target-selection-does-not-rewrite-running-snapshot", target(session)["connection"] == ids[0] and target(session)["model"] == "one", target(session))
        server.release.set()
        wait(console, process, lambda s: "SLOW_DONE" in s["text"] and "NEXT MESSAGE" not in s["text"] and "two  xhigh" in s["rows"][0]["text"], "cleanup and target handoff")
        eventually(lambda: target(session)["connection"] == ids[1], "deferred target persistence")
        record("busy-choice-saved-after-cleanup", target(session)["model"] == "two" and target(session)["effort"] == "xhigh")
        stop()
        renamed = args.scratch / "after 改名😀"; workspace.rename(renamed); workspace = renamed
        run("resume", session, "-p", "RENAMED")
        record("project-rename-keeps-model-memory", server.requests[-1] == {"lane": "b", "model": "two", "effort": "xhigh", "prompt": "RENAMED"})
        imported_db = args.scratch / "imported.sqlite3"; seed_project = args.scratch / "seed"; seed_project.mkdir()
        run("doctor", db=imported_db, cwd=seed_project); seed(imported_db)
        refused = run("--import-history", "resume", session, db=imported_db, ok=False)
        record("existing-catalog-cannot-acquire-independent-authority", "another existing shared catalog" in refused.stderr)
        with closing(sqlite3.connect(database)) as connection: connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        retired = args.scratch / "retired-catalog.sqlite3"
        database.rename(retired)
        for suffix in ("-wal", "-shm"):
            owned = Path(str(database) + suffix)
            if owned.exists(): owned.rename(Path(str(retired) + suffix))
        run("--import-history", "resume", session, "-p", "IMPORTED", db=imported_db)
        record("independent-catalog-import-keeps-model-memory", target(session, imported_db)["effort"] == "xhigh" and server.requests[-1]["lane"] == "b")
        # Import now owns the mirror; finish through the imported catalog.
        database = imported_db
        sql("DELETE FROM connection_configs WHERE id=?", (ids[1],))
        unavailable = launch("resume", session)
        record("removed-provider-shown-without-silent-default", "two [unavailable]  xhigh" in unavailable["rows"][0]["text"])
        stop(); requests_before = len(server.requests)
        run("resume", session, "-p", "MUST_NOT_FALL_BACK", ok=False)
        record("removed-provider-request-fails-without-replay-or-fallback", len(server.requests) == requests_before)
        record("terminal-restored", console.modes() == baseline)
        assert not server.errors, server.errors
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"; evidence["error"] = traceback.format_exc()
        if console is not None and process is not None and process.poll() is None:
            evidence["last_screen"] = console.read(viewport=True)
    finally:
        server.release.set()
        if process is not None and process.poll() is None: process.terminate(); process.wait(timeout=5)
        for name in credentials: checked(advapi.CredDeleteW(name, 1, 0))
        server.shutdown(); server.server_close()
        evidence["provider_errors"] = server.errors; evidence["requests"] = server.requests
        write_json(args.evidence, evidence)
    return 0 if evidence["result"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path); parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--worker", action="store_true"); parser.add_argument("--scratch", type=Path); parser.add_argument("--ready", type=Path)
    args = parser.parse_args(); args.executable = args.executable.resolve(strict=True); args.evidence = args.evidence.resolve()
    if args.worker: return worker(args)
    harness.__file__ = __file__
    return harness.controller(args)


if __name__ == "__main__": raise SystemExit(main())
