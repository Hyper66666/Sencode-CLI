"""Real Windows pipe approvals through the native hook/controller boundary.

Uses only isolated state, deterministic compiled workers and local files.
Not a live provider, installed CLI, or extension SDK compatibility test.
"""
from contextlib import closing
import json
from pathlib import Path
import queue
import shutil
import sqlite3
import subprocess
import sys
import threading
import time

from hook_fixture import fixture_directory, digest, run


def rows(database, query, args=()):
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute(query, args).fetchall()


def controller(host, database, root, mode, call_path, answer=True, before_answer=None, cancel=False, cancel_sentinel=None):
    child = subprocess.Popen([str(host), str(database), str(root), mode, str(call_path)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             encoding="utf-8", bufsize=1)
    events = queue.Queue()
    def drain():
        for line in child.stdout:
            events.put(line)
        events.put(None)
    threading.Thread(target=drain, daemon=True).start()
    observed = []
    interactions = 0
    # An approval queued before a nonce exists cannot become a launch grant.
    child.stdin.write(json.dumps({"type": "approval", "id": "fixture-approval-1", "approved": True}) + "\n")
    child.stdin.flush()
    deadline = time.monotonic() + 30
    while True:
        assert time.monotonic() < deadline, ("host fixture timeout", observed)
        line = events.get(timeout=30)
        if line is None:
            break
        event = json.loads(line)
        observed.append(event)
        if event.get("type") == "approval":
            interactions += 1
            assert event["tool"] == "internal:extension_worker", event
            preview = event["text"]
            assert "not sandboxed" in preview and "manifest_sha256" in preview
            assert "disclosed_event" in preview and "worker_id" in preview
            if before_answer:
                before_answer(interactions, event)
            response = ({"type": "cancel", "id": "fixture"} if cancel else
                        {"type": "approval", "id": event["id"], "request_id": "fixture", "approved": answer})
            child.stdin.write(json.dumps(response) + "\n")
            child.stdin.flush()
            if cancel_sentinel and interactions == 1:
                def cancel_running():
                    until = time.monotonic() + 5
                    while not cancel_sentinel.exists() and time.monotonic() < until:
                        time.sleep(.01)
                    child.stdin.write(json.dumps({"type": "cancel", "id": "fixture"}) + "\n")
                    child.stdin.flush()
                threading.Thread(target=cancel_running, daemon=True).start()
    child.wait(timeout=5)
    stderr = child.stderr.read()
    assert child.returncode == 0, (child.returncode, observed, stderr)
    reports = [item for item in observed if item.get("type") == "fixture-result"]
    assert len(reports) == 1, observed
    assert reports[0]["requests"] == 7 and reports[0]["tokens"] == 91, reports
    return reports[0], observed, interactions


def fixture(host, management, worker):
    with fixture_directory() as root:
        image = root / "guard.exe"
        shutil.copyfile(worker, image)
        manifest_path = root / "sencode-worker.json"
        manifest = {"schema": 1, "id": "guard", "version": "0.1.0", "language": "sengoo",
                    "protocol": "sencode.native-worker/1", "executable": image.name,
                    "sha256": digest(image), "timeout_ms": 3000,
                    "before_tool": ["read_file", "write_file"], "after_tool": ["read_file", "write_file"]}
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        management_database = root / "management.sqlite3"
        empty = json.loads(run(management, "manage", management_database, "list", "", "no").stdout)
        assert empty["workers"] == [] and not Path(str(management_database) + ".extensions.sqlite3").exists()
        assert run(management, "manage", management_database, "inspect", "missing", "no", ok=False).returncode != 0
        assert not Path(str(management_database) + ".extensions.sqlite3").exists()
        registered = json.loads(run(management, "manage", management_database, "add", manifest_path, "no").stdout)
        assert not registered["enabled"]
        refused = run(management, "manage", management_database, "enable", "guard", "no", ok=False)
        assert refused.returncode != 0 and json.loads(refused.stdout)["permission_required"]
        trusted = json.loads(run(management, "manage", management_database, "enable", "guard", "yes").stdout)
        assert trusted["enabled"] and not list(root.glob("*.sentinel"))
        run(management, "manage", management_database, "disable", "guard", "no")
        run(management, "manage", management_database, "remove", "guard", "no")
        print("hook management fixture passed: side-effect-free reads, disabled registration, explicit trust, no spawn")
        for case in ["approve", "refuse", "plan", "child", "headless", "block", "after_crash",
                     "trust_changed", "cancel", "running_cancel", "complete", "running", "hook-prior", "hook-done", "invalid"]:
            database = root / (case + ".sqlite3")
            run(management, "add", database, manifest_path)
            run(management, "enable", database, "guard")
            target = root / (case + ".txt")
            sentinel = root / (case + ".sentinel")
            arguments = {"path": target.name, "content": "parent output", "hook_fixture_mode": "block" if case == "block" else "continue",
                         "hook_fixture_sentinel": str(sentinel)}
            if case in {"plan", "child"}:
                target.write_text("read-only input", encoding="utf-8")
            if case == "after_crash":
                arguments["hook_fixture_after_mode"] = "crash"
            if case == "running_cancel":
                arguments["hook_fixture_mode"] = "sleep"
            call = {"id": "parent-" + case, "name": "read_file" if case in {"plan", "child"} else "write_file",
                    "arguments": "broken-json" if case == "invalid" else json.dumps(arguments)}
            call_path = root / "call.json"
            call_path.write_text(json.dumps(call), encoding="utf-8")
            def before_answer(number, event):
                # Both the image and every ancestor must be pinned while approval waits.
                if number == 1:
                    try:
                        with image.open("ab") as stream:
                            stream.write(b"must-not-replace")
                    except PermissionError:
                        pass
                    else:
                        raise AssertionError("worker image was replaceable during approval")
                    try:
                        root.rename(root.with_name(root.name + "-must-not-move"))
                    except PermissionError:
                        pass
                    else:
                        raise AssertionError("worker ancestor directory was replaceable during approval")
                if case == "trust_changed" and number == 1:
                    run(management, "disable", database, "guard")
            report, events, interactions = controller(host, database, root,
                case if case in {"plan", "child", "headless", "complete", "running", "hook-prior", "hook-done"} else "control",
                call_path, answer=case != "refuse", before_answer=before_answer, cancel=case == "cancel",
                cancel_sentinel=sentinel if case == "running_cancel" else None)
            session = report["session"]
            parent = rows(database, "SELECT state,result FROM shared_tool_ledger WHERE session_id=? AND call_id=?", (session, call["id"]))
            hooks = rows(database, "SELECT state FROM shared_tool_ledger WHERE session_id=? AND name='internal:extension_worker'", (session,))
            assert rows(database, "SELECT cleanup_required FROM shared_executions WHERE session_id=?", (session,)) == [(0,)], (case, report)
            if case in {"approve", "after_crash"}:
                assert target.exists(), (case, report, events)
                assert target.read_text(encoding="utf-8") == "parent output"
                assert parent and parent[0][0] == "complete" and len(hooks) == 2
                assert interactions == 2 and len(sentinel.read_text().splitlines()) == 2
                assert report["goal_status"] == (2 if case == "after_crash" else 1)
            elif case == "complete":
                assert not sentinel.exists() and not target.exists() and interactions == 0
                assert report["result"]["content"] == "saved original outcome"
            elif case == "running":
                assert not sentinel.exists() and not target.exists() and interactions == 0
                assert not report["is_ok"] and report["error"] == 12
            elif case == "invalid":
                assert parent and parent[0][0] == "complete" and not sentinel.exists() and interactions == 0
            else:
                assert not parent, (case, parent)
                assert report["goal_status"] == 2, (case, report)
                assert not target.exists() if case not in {"plan", "child"} else target.read_text() == "read-only input"
                assert sentinel.exists() == (case in {"block", "running_cancel"}), (case, report)
                assert interactions == (0 if case in {"plan", "child", "headless", "hook-prior", "hook-done"} else 1), (case, events)
            print("hook controller fixture passed:", case)
        print("hook fresh approval/policy/no replay/after persistence/Goal fixture passed")


if __name__ == "__main__":
    fixture(*(Path(item).resolve() for item in sys.argv[1:4]))
