"""Verify stable reading entries at 80/120/160 columns in a real owned console.

The Sengoo driver renders synthetic messages and a timed stream only. It never
opens storage, credentials or a provider. Evidence is actual console cells.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import time
import traceback

from tui_console_fixture import Console, Coord, JobExtendedLimits, checked, environment_for, kernel_api, remove_owned_tree, write_json
from fullscreen_console_fixture import wait


def worker(args):
    evidence = {"schema": 1, "scope": "rendering-only-real-console-resize", "platform": "windows-x64",
                "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                "result": "running", "checks": [], "snapshots": {}}
    process = None
    try:
        deadline = time.monotonic() + 10
        while not args.ready.exists():
            if time.monotonic() > deadline:
                raise AssertionError("Owned Job was not established")
            time.sleep(0.02)
        console = Console()
        console.resize(80, 30)
        console.clear()
        baseline = console.modes()
        process = subprocess.Popen([str(args.executable)], cwd=args.scratch, env=environment_for(args.scratch))
        wait(console, process, lambda s: "END-12" in s["text"] and "READING" in s["text"], "initial alternate screen")
        # Open the active alternate buffer after the child has selected it.
        # The worker's inherited output handle can remain bound to its primary
        # buffer, whose resize must not be mistaken for an alternate resize.
        console.kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        console.kernel.CreateFileW.restype = wintypes.HANDLE
        original_output = console.output
        active_output = console.kernel.CreateFileW("CONOUT$", 0xC0000000, 3, None, 3, 0, None)
        assert active_output not in (None, ctypes.c_void_p(-1).value), ctypes.get_last_error()
        console.output = active_output
        class ConsoleFont(ctypes.Structure):
            _fields_ = [("index", wintypes.DWORD), ("size", Coord)]
        console.kernel.GetConsoleWindow.restype = wintypes.HWND
        console.kernel.GetCurrentConsoleFont.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(ConsoleFont)]
        console.kernel.GetCurrentConsoleFont.restype = wintypes.BOOL
        window = console.kernel.GetConsoleWindow()
        assert window, "Owned console window is unavailable"
        user = ctypes.WinDLL("user32", use_last_error=True)
        user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        for width, height in ((80, 30), (120, 35), (160, 28), (80, 30)):
            # Make room before growing. For shrinking the owned window must
            # move first: an alternate viewport cannot be wider than its buffer.
            if width > console.info().dwSize.X:
                checked(console.kernel.SetConsoleScreenBufferSize(console.output, Coord(width, 2000)))
            font = ConsoleFont()
            checked(console.kernel.GetCurrentConsoleFont(console.output, False, ctypes.byref(font)))
            outer, client = wintypes.RECT(), wintypes.RECT()
            checked(user.GetWindowRect(window, ctypes.byref(outer)))
            checked(user.GetClientRect(window, ctypes.byref(client)))
            # Resize this hidden owned window as a user terminal resize would.
            # This lets conhost update both its primary and alternate viewport.
            checked(user.SetWindowPos(window, None, 0, 0,
                    width * font.size.X + outer.right - outer.left - client.right,
                    height * font.size.Y + outer.bottom - outer.top - client.bottom, 0x16))
            screen = wait(console, process, lambda s: "END-12" in s["text"] and "READING" in s["text"]
                          and "preserved 中文 draft" in s["text"] and s["width"] == width,
                          f"stable reading entry at {width} columns")
            assert "END-13" not in screen["text"] and "newer stream row" not in screen["text"], screen["text"]
            # Give the synthetic stream time to grow before checking the same
            # anchor again, rather than accepting just one transitional frame.
            time.sleep(0.1)
            screen = console.read(viewport=True)
            assert "END-12" in screen["text"] and "END-13" not in screen["text"]
            evidence["snapshots"][f"columns-{width}-{len(evidence['checks'])}"] = screen
            evidence["checks"].append(f"{width}-columns-reading-entry-draft-focus-preserved-during-stream")
        console.inject("q")
        wait(console, process, lambda s: "READING" not in s["text"] and "preserved 中文 draft" in s["text"], "return to original draft")
        console.key(0x43, "\x03", 8)
        wait(console, process, lambda s: "NEXT MESSAGE" not in s["text"], "cancel synthetic stream")
        console.key(0x55, "\x15", 8)
        console.inject("/quit")
        wait(console, process, lambda s: "COMMANDS" in s["text"], "quit menu")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "/quit" in s["text"] and "COMMANDS" not in s["text"], "quit completion only")
        assert process.poll() is None, "First Enter must not execute quit"
        console.key(0x0D, "\r")
        assert process.wait(timeout=10) == 0
        console.output = original_output
        checked(console.kernel.CloseHandle(active_output))
        assert console.modes() == baseline
        evidence["checks"].append("focus-return-cancel-two-enter-exit-and-console-restoration")
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        try:
            evidence["last_screen"] = console.read(viewport=True)
            info = console.info()
            evidence["console_geometry"] = {"buffer": [info.dwSize.X, info.dwSize.Y], "maximum": [info.dwMaximumWindowSize.X, info.dwMaximumWindowSize.Y]}
        except BaseException:
            pass
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        write_json(args.evidence, evidence)


def controller(args):
    kernel = kernel_api()
    scratch = Path(tempfile.mkdtemp(prefix="sencode-resize-console-"))
    job = checked(kernel.CreateJobObjectW(None, None))
    process = None
    try:
        limits = JobExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000
        checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), str(args.executable), "--worker",
                                    "--scratch", str(scratch), "--ready", str(scratch / "ready"),
                                    "--evidence", str(args.evidence)], startupinfo=startup,
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
        checked(kernel.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)))
        (scratch / "ready").write_text("assigned", encoding="ascii")
        code = process.wait(timeout=60)
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        assert code == 0 and evidence["result"] == "passed", evidence.get("error", str(code))
        print(f"Real resize console: {len(evidence['checks'])} checks passed")
        print(f"Evidence: {args.evidence}")
    finally:
        checked(kernel.CloseHandle(job))
        if process is not None:
            process.wait(timeout=5)
        remove_owned_tree(scratch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[1] / "target/worktree-tui/resize-console-evidence.json")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("A real Windows console is required")
    args.executable = args.executable.resolve(strict=True)
    args.evidence = args.evidence.resolve()
    if args.worker:
        worker(args)
    else:
        controller(args)


if __name__ == "__main__":
    main()
