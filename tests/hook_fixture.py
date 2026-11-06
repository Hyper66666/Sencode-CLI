"""Isolated Windows native-worker fixtures; never opens a user profile.

The transport probe is deliberately private and is not evidence that public
permission paths or installed commands work. Those are separate host gates.
"""
from contextlib import closing, contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time


@contextmanager
def fixture_directory():
    root = Path(tempfile.mkdtemp(prefix="sencode-hook-fixture-")).resolve()
    try:
        yield root
    except BaseException:
        print("Failed fixture retained:", root, file=sys.stderr)
        raise
    else:
        inventory = sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True)
        for item in inventory:
            assert root in item.resolve().parents, ("fixture cleanup escaped", item)
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
            else:
                raise AssertionError(("unexpected fixture entry", item))
        root.rmdir()


def run(executable, *args, ok=True):
    result = subprocess.run([str(executable), *map(str, args)], capture_output=True,
                            encoding="utf-8", timeout=15)
    if ok:
        assert result.returncode == 0, (args, result.returncode, result.stdout, result.stderr)
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transport(executable, worker):
    with fixture_directory() as temporary:
        root = Path(temporary)
        image = root / "guard.exe"
        shutil.copyfile(worker, image)
        manifest_path = root / "sencode-worker.json"
        manifest = {"schema": 1, "id": "guard", "version": "0.1.0", "language": "sengoo",
                    "protocol": "sencode.native-worker/1", "executable": image.name,
                    "sha256": digest(image), "timeout_ms": 3500,
                    "before_tool": ["read_file", "write_file"], "after_tool": ["read_file"]}
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        database = root / "shared.sqlite3"
        registered = json.loads(run(executable, "add", database, manifest_path).stdout)
        assert len(registered["workers"]) == 1 and not registered["workers"][0]["enabled"]
        run(executable, "enable", database, "guard")
        assert not (root / "sentinel").exists(), "management must not spawn"
        for mode in ["continue", "block", "fragment", "host_call", "crash", "malformed",
                     "oversized", "stderr", "wrong_id", "unknown", "duplicate", "exit_after_result", "sleep", "tree"]:
            event = {"schema": 1, "protocol": "sencode.native-worker/1", "type": "hook",
                     "id": "fixture-" + mode, "worker_id": "guard",
                     "manifest_sha256": digest(manifest_path), "event": "before_tool",
                     "input": {"hook_fixture_mode": mode,
                               "hook_fixture_sentinel": str(root / (mode + ".sentinel"))}}
            path = root / "event.json"
            path.write_text(json.dumps(event), encoding="utf-8")
            result = json.loads(run(executable, "transport", database, "guard", root, path).stdout)
            expected = "blocked" if mode == "block" else "continued" if mode in {"continue", "fragment", "host_call"} else "failed"
            assert result["status"] == expected, (mode, result)
            assert result["cleanup_confirmed"], (mode, result)
            assert "stderr is private" not in json.dumps(result)
            if expected in {"continued", "blocked"}:
                assert "中文😀" in result["notice"]
        time.sleep(2)
        assert not (root / "tree.sentinel.grandchild").exists(), "owned grandchild escaped cleanup"
        original = manifest_path.read_bytes()
        manifest_path.write_bytes(original + b" ")
        failed = run(executable, "transport", database, "guard", root, path, ok=False)
        assert failed.returncode != 0, "changed manifest must require review"
        manifest_path.write_bytes(original)
        with image.open("ab") as stream:
            stream.write(b"changed")
        assert run(executable, "transport", database, "guard", root, path, ok=False).returncode != 0
        with closing(sqlite3.connect(database)) as connection:
            assert connection.execute("select count(*) from shared_executions").fetchone()[0] == 0
        print("hook transport/Unicode/pressure/tree cleanup/fingerprint fixtures passed")


if __name__ == "__main__":
    transport(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
