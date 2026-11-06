"""Independent management command gate; real Git and an owned hidden console."""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from tui_console_fixture import Console, JobExtendedLimits, checked, kernel_api


def cleanup(root: Path):
    for directory, _, files in os.walk(root, topdown=False, followlinks=False):
        for name in files:
            path = Path(directory) / name
            path.chmod(0o600)
            path.unlink()
        Path(directory).rmdir()


def git(cwd: Path, *arguments: str):
    result = subprocess.run([shutil.which("git"), "-c", "core.hooksPath=NUL", *arguments], cwd=cwd, capture_output=True, timeout=15)
    assert result.returncode == 0, (arguments, result.stderr)
    return result


def repo(path: Path):
    path.mkdir()
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Isolated CLI Fixture")
    git(path, "config", "user.email", "cli-fixture@example.invalid")
    (path / "hello.txt").write_text("hello 中文\n", encoding="utf-8")
    git(path, "add", "--", "hello.txt")
    git(path, "commit", "-m", "fixture")


def args_for(executable: Path, root: Path, source: Path, *arguments: str):
    return [str(executable), "worktree", *arguments, "--cwd", str(source), "--database", str(root / "state.sqlite3")]


def headless(executable: Path, root: Path):
    source = root / "主 空格 workspace"
    repo(source)
    target = root / "新 子工作区"

    def run(expected: int, *arguments: str):
        result = subprocess.run(args_for(executable, root, source, *arguments), capture_output=True,
                                encoding="utf-8", timeout=20)
        assert result.returncode == expected, (arguments, result.returncode, result.stdout, result.stderr)
        return result

    listed = run(0, "list", "--json")
    assert json.loads(listed.stdout)["capability"] == "ready"
    denied = run(1, "create", str(target), "--json")
    assert "explicit --yes" in json.loads(denied.stdout)["message"] and not target.exists()
    planned = run(1, "create", str(target), "--yes", "--plan", "--json")
    assert json.loads(planned.stdout)["status"] == "refused" and not target.exists()
    made = run(0, "create", str(target), "--yes", "--branch", "codex/exact-cli", "--json")
    assert json.loads(made.stdout)["status"] == "complete"
    assert git(target, "symbolic-ref", "--short", "HEAD").stdout.strip() == b"codex/exact-cli"
    run(2, "remove", str(target), "--yes", "--branch", "bad")
    assert target.is_dir()
    denied_remove = run(1, "remove", str(target), "--json")
    assert json.loads(denied_remove.stdout)["status"] == "refused" and target.is_dir()
    planned_remove = run(1, "remove", str(target), "--yes", "--plan", "--json")
    assert json.loads(planned_remove.stdout)["status"] == "refused" and target.is_dir()
    run(0, "remove", str(target), "--yes", "--json")
    assert not target.exists()
    text = run(0, "list").stdout
    assert "[main]" in text and source.as_posix() in text.replace("\\", "/"), repr(text)
    run(2, "create")
    run(2, "list", "--yes")
    return 11


def wait(console, process, text: str):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        snapshot = console.read()
        if text in snapshot["text"]:
            return snapshot
        assert process.poll() is None, (process.returncode, snapshot["text"])
        time.sleep(0.02)
    raise AssertionError(("console timeout", text, console.read()["text"]))


def worker(arguments):
    ready = arguments.root / "ready"
    while not ready.exists():
        time.sleep(0.01)
    console = Console()
    console.resize(110)
    baseline = console.modes()
    source = arguments.root / "TTY 主工作区"
    repo(source)
    target = arguments.root / "TTY 子工作区"
    process = None
    try:
        for operation, answer, expected_exists in [("create", "no", False), ("create", "yes", True), ("remove", "yes", False)]:
            console.clear()
            process = subprocess.Popen(args_for(arguments.executable, arguments.root, source, operation, str(target)))
            shown = wait(console, process, "Type yes to approve")
            assert '"target":' in shown["text"] and '"operation":' in shown["text"]
            time.sleep(0.05)  # Fresh explicit input after the approval barrier.
            console.command(answer)
            code = process.wait(timeout=15)
            assert code == (1 if answer == "no" else 0), code
            assert target.exists() is expected_exists
            assert console.modes() == baseline, "terminal was not restored after management command"
            process = None
        (arguments.root / "tty-result.json").write_text(json.dumps({"status": "passed", "checks": 3}), encoding="utf-8")
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)


def controller(arguments):
    root = Path(tempfile.mkdtemp(prefix="sencode-worktree-cli-用户 空格-"))
    kernel = kernel_api()
    job = checked(kernel.CreateJobObjectW(None, None))
    process = None
    try:
        checks = headless(arguments.executable, root)
        tty = root / "tty"
        tty.mkdir()
        limits = JobExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000
        checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), str(arguments.executable), "--worker", "--root", str(tty)],
                                   startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE)
        checked(kernel.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)))
        (tty / "ready").write_text("owned", encoding="ascii")
        assert process.wait(timeout=50) == 0
        result = json.loads((tty / "tty-result.json").read_text(encoding="utf-8"))
        assert result["status"] == "passed"
        print(f"worktree CLI: {checks} headless argument/Plan/approval checks + {result['checks']} real hidden-console approve/decline/restore checks passed")
    finally:
        checked(kernel.CloseHandle(job))
        if process is not None:
            process.wait(timeout=5)
        cleanup(root)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--root", type=Path)
    arguments = parser.parse_args()
    arguments.executable = arguments.executable.resolve(strict=True)
    if arguments.worker:
        worker(arguments)
    else:
        controller(arguments)


if __name__ == "__main__":
    main()
