"""Public long-session resume/context gate in an owned Windows console.

Creates an isolated project/catalog/profile and inserts only synthetic messages.
No connection, credential, API server, clipboard or user terminal is used.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback

from fullscreen_console_fixture import wait
from tui_console_fixture import (
    Console, JobExtendedLimits, checked, environment_for, kernel_api,
    remove_owned_tree, write_json,
)


def worker(args):
    evidence = {
        "schema": 1, "result": "running", "platform": "windows-x64",
        "binary": str(args.executable),
        "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
        "fixture_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Synthetic project-local history; public plain and native hidden-console CLI; no API, credential or user state",
        "message_count": args.count, "checks": [], "snapshots": {},
    }
    process = None

    def record(name, condition, detail=None):
        value = {"name": name, "status": "passed" if condition else "failed"}
        if not condition:
            value["detail"] = detail
        evidence["checks"].append(value)

    def run_plain(directory, *arguments, prompt="/context\n/exit\n"):
        result = subprocess.run(
            [str(args.executable), "--cwd", str(directory), "--database", str(database), "--tui", "plain", *arguments],
            cwd=directory, env=environment, input=prompt, capture_output=True,
            text=True, encoding="utf-8", timeout=30,
        )
        assert result.returncode == 0, {"code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        return result.stdout

    def context_checks(label, output):
        evidence[label] = output
        # Redirected public output is JSON; native plain mode may format text.
        # Validate either public form without requiring a terminal emulator.
        try:
            document = json.loads(output.strip())
        except json.JSONDecodeError:
            document = None
        if isinstance(document, dict) and isinstance(document.get("messages"), list):
            count = document.get("total_messages", len(document["messages"]))
            content = "\n".join(value.get("content", "") for value in document["messages"])
        else:
            matched = re.search(r"(\d+) saved messages", output)
            count = int(matched.group(1)) if matched else None
            content = output
        record(label + "-reports-complete-message-count", count == args.count, {"observed_total": count})
        record(label + "-shows-newest-revision-not-first-message", latest in content and first not in content,
               {"has_latest": latest in content, "has_first": first in content})

    try:
        deadline = time.monotonic() + 10
        while not args.ready.exists():
            assert time.monotonic() < deadline, "Owned process Job was not established"
            time.sleep(.02)
        environment = environment_for(args.scratch)
        os.environ.clear()
        os.environ.update(environment)
        original = args.scratch / "before 项目"
        renamed = args.scratch / "after 改名项目"
        original.mkdir()
        database = args.scratch / "isolated.sqlite"
        run_plain(original, prompt="/exit\n")
        first = "FIRST_HISTORY_0001 不应冒充最新记录"
        latest = f"LATEST_TAIL_{args.count} 中文尾句"
        with sqlite3.connect(database) as connection:
            connection.create_function("sengoo_context", 1, lambda key: "owned-long-history-fixture" if key == "instance_id" else None)
            sessions = connection.execute("SELECT id,project_id FROM sessions").fetchall()
            assert len(sessions) == 1, sessions
            session, project = sessions[0]
            assert connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0
            rows = []
            for index in range(1, args.count + 1):
                text = first if index == 1 else latest if index == args.count else f"saved-{index:04d}"
                # Reverse creation timestamps deliberately: revision determines
                # conversation order, rather than UUID or wall-clock order.
                rows.append((f"owned-long-{index:06d}", session, "user" if index % 2 else "assistant", text,
                             args.count - index + 1, args.count - index + 1, index))
            connection.executemany(
                "INSERT INTO messages(id,session_id,role,text,created_at,completed_at,revision) VALUES(?,?,?,?,?,?,?)", rows,
            )
            connection.execute("UPDATE sessions SET title='owned long history',updated_at=updated_at+1 WHERE id=?", (session,))
            connection.commit()
        evidence["session_id"] = session
        context_checks("plain-context-before-rename", run_plain(original, "resume", session))

        console = Console()
        console.resize(120, 42)
        console.clear()
        baseline = console.modes()

        def native_resume(directory, label, *arguments):
            nonlocal process
            console.clear()
            process = subprocess.Popen(
                [str(args.executable), "--cwd", str(directory), "--database", str(database), *arguments],
                cwd=directory, env=environment,
            )
            try:
                screen = wait(console, process, lambda value: "SENCODE" in value["text"] and "MESSAGE" in value["text"], "public long-history resume", timeout=20)
                evidence["snapshots"][label + "-tail"] = screen
                record(label + "-shows-newest-without-first-message", latest in screen["text"] and first not in screen["text"], screen["text"])
                # The newest window and complete stored count remain visible
                # together; normal Ready/status changes cannot erase the hint.
                text = screen["text"].lower()
                record(label + "-discloses-bounded-recent-window-and-total",
                       "latest history" in text and f"{args.count} saved" in text, screen["text"])
            finally:
                if process.poll() is None:
                    console.key(0x44, "\x04", 8)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        process.wait(timeout=5)
                record(label + "-terminal-restoration", process.returncode == 0 and console.modes() == baseline,
                       {"exit_code": process.returncode, "before": baseline, "after": console.modes()})

        native_resume(original, "native-before-rename", "resume", session)
        assert original.resolve().parent == args.scratch.resolve() and renamed.parent == args.scratch and not renamed.exists()
        original.rename(renamed)
        context_checks("plain-context-after-rename", run_plain(renamed, "-c"))
        native_resume(renamed, "native-after-rename", "-c")
        with sqlite3.connect(database) as connection:
            current = connection.execute("SELECT id,project_id FROM sessions").fetchall()
            total = connection.execute("SELECT COUNT(*) FROM messages WHERE session_id=?", (session,)).fetchone()[0]
            connections = connection.execute("SELECT COUNT(*) FROM connection_configs").fetchone()[0]
        archive_path = renamed / ".sencode" / "history.sqlite3"
        with sqlite3.connect(archive_path.as_uri() + "?mode=ro", uri=True) as archive:
            archived_total = archive.execute("SELECT COUNT(*) FROM ph_messages WHERE session_id=?", (session,)).fetchone()[0]
            archived_latest = archive.execute("SELECT text FROM ph_messages WHERE session_id=? ORDER BY revision DESC LIMIT 1", (session,)).fetchone()[0]
            archived_session = archive.execute("SELECT id,project_id FROM ph_sessions").fetchall()
        record("project-local-archive-keeps-complete-history-and-stable-identity-after-rename",
               current == [(session, project)] and archived_session == current and total == archived_total == args.count and archived_latest == latest,
               {"catalog_sessions": current, "archive_sessions": archived_session, "catalog_count": total,
                "archive_count": archived_total, "archive_latest": archived_latest})
        record("no-provider-connection-or-credential-required", connections == 0, {"connections": connections})
        evidence["result"] = "passed" if all(value["status"] == "passed" for value in evidence["checks"]) else "failed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None:
            try:
                evidence["last_screen"] = console.read(viewport=True)
            except BaseException:
                pass
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        write_json(args.evidence, evidence)
    return 0 if evidence["result"] == "passed" else 1


def controller(args):
    kernel = kernel_api()
    scratch = Path(tempfile.mkdtemp(prefix="sencode-long-history-")).resolve()
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
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), str(args.executable), "--worker", "--scratch", str(scratch),
             "--ready", str(ready), "--count", str(args.count), "--evidence", str(args.evidence)],
            startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        checked(kernel.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)))
        ready.write_text("assigned", encoding="ascii")
        code = process.wait(timeout=150)
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        print(json.dumps({"result": evidence["result"], "checks": [{"name": value["name"], "status": value["status"]} for value in evidence["checks"]], "error": evidence.get("error"),
                          "evidence": str(args.evidence)}, ensure_ascii=True, indent=2))
        return code
    finally:
        checked(kernel.CloseHandle(job))
        if process is not None:
            process.wait(timeout=5)
        remove_owned_tree(scratch)


def main():
    if os.name != "nt":
        raise SystemExit("This public fixture requires a real owned Windows console")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[1] / "target/long-history/public.json")
    parser.add_argument("--count", type=int, default=1008)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    if args.count < 1001:
        parser.error("--count must exceed the former 1000-message limit")
    args.executable = args.executable.resolve(strict=True)
    args.evidence = args.evidence.resolve()
    return worker(args) if args.worker else controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
