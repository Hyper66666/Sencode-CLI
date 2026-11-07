"""Isolated real-console editor, Vim and transcript-focus integration gate.

The owned hidden console drives a Sengoo-only synthetic UI executable. It opens
no application database or API and records real Windows console cells.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback

from tui_console_fixture import (
    Console, JobExtendedLimits, checked, environment_for, kernel_api,
    remove_owned_tree, write_json,
)
from fullscreen_console_fixture import wait


def composer(screen):
    return "\n".join(row["text"] for row in screen["rows"] if row["text"].lstrip().startswith(("│ > ", "│   ")))


def worker(args):
    evidence = {"schema": 1, "scope": "synthetic-sengoo-editor-real-console", "result": "running",
                "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(), "checks": [], "snapshots": {}}
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
        baseline = console.modes()
        environment = environment_for(args.scratch)
        keymap = args.scratch / "explicit-keymap.json"
        payload = '{"version":1,"mode":"default","bindings":[{"key":"alt+b","action":"word_left"}]}'
        keymap.write_text(payload, encoding="utf-8")
        environment["SENCODE_KEYMAP"] = str(keymap)
        process = subprocess.Popen([str(args.executable)], cwd=args.scratch, env=environment)
        wait(console, process, lambda s: "S E N C O D E" in s["text"] and "MESSAGE" in s["text"], "home")

        # Explicit safe custom mapping changes only the composer.
        console.inject("one two")
        wait(console, process, lambda s: "one two" in composer(s), "custom-map draft")
        console.key(0x42, "b", 2)
        console.inject("X")
        custom = wait(console, process, lambda s: "one Xtwo" in composer(s), "Alt+B composer mapping")
        evidence["snapshots"]["custom-composer-map"] = custom
        evidence["checks"].append("validated-alt-map-only-edits-composer")
        console.key(0x55, "\x15", 8)
        console.key(0x23)  # End before the default clear-to-start chord.
        console.key(0x55, "\x15", 8)

        # First Enter completes; the second changes an in-memory editor mode.
        console.inject("/keys vi")
        wait(console, process, lambda s: "COMMAND ARGUMENTS" in s["text"] and "vim" in s["text"], "keys argument list")
        console.key(0x0D, "\r")
        completed = wait(console, process, lambda s: "/keys vim" in composer(s) and "COMMAND ARGUMENTS" not in s["text"], "keys first Enter completion")
        assert "VIM INSERT" not in completed["text"], completed["text"]
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "VIM INSERT" in s["text"] and "/keys vim" not in composer(s), "keys second Enter selection")
        evidence["checks"].append("keys-discovery-two-enter-local-mode-selection")

        console.inject("x中文")
        wait(console, process, lambda s: "x中文" in composer(s), "Vim Unicode draft")
        console.key(0x1B, "\x1b")
        normal = wait(console, process, lambda s: "VIM NORMAL" in s["text"], "visible NORMAL mode")
        console.inject("h")
        console.inject("x")
        wait(console, process, lambda s: "x中" in composer(s) and "x中文" not in composer(s), "Unicode modal delete")
        console.inject("u")
        unicode = wait(console, process, lambda s: "x中文" in composer(s), "Unicode modal undo")
        evidence["snapshots"]["unicode-vim-undo"] = unicode
        evidence["checks"].append("visible-vim-mode-and-grapheme-delete-undo")

        console.inject("\x1b[200~dd\n/permissions auto-edit\x1b[201~")
        pasted = wait(console, process, lambda s: "VIM INSERT" in s["text"] and "/permissions auto-edit" in composer(s) and "dd" in composer(s), "literal modal paste")
        assert "PERMISSION REQUIRED" not in pasted["text"] and "YOU" not in pasted["text"]
        evidence["snapshots"]["literal-modal-paste"] = pasted
        evidence["checks"].append("bracketed-paste-is-literal-and-enters-insert")
        console.key(0x23)
        console.key(0x55, "\x15", 8)
        wait(console, process, lambda s: "Ask anything" in composer(s), "clear pasted draft")

        # Focus is reserved for an approval; Vim/custom keys cannot approve.
        console.command("approval")
        wait(console, process, lambda s: "PERMISSION REQUIRED" in s["text"] and "› Deny this operation" in s["text"], "fresh default deny approval")
        console.inject("y")
        console.key(0x42, "b", 2)
        console.key(0x0D, "\r")
        denied = wait(console, process, lambda s: "FIXTURE PERMISSION DENIED" in s["text"], "editor keys cannot approve")
        assert "FIXTURE PERMISSION ALLOWED" not in denied["text"]
        evidence["checks"].append("approval-focus-default-deny-blocks-editor-bindings")

        # A picker owns NORMAL-mode input and keeps its original safe default.
        console.inject("/keys")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Command completed" in s["text"] and "EDITOR KEYS" not in s["text"], "keys command completion")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "EDITOR KEYS" in s["text"] and "› Keep current editor / close" in s["text"], "safe editor picker")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "EDITOR KEYS" not in s["text"] and "VIM INSERT" in s["text"], "editor picker keeps mode")
        evidence["checks"].append("editor-picker-safe-default-and-independent-focus")

        console.command("stream")
        wait(console, process, lambda s: "editor stream line 5" in s["text"] and "NEXT MESSAGE" in s["text"], "streaming")
        console.inject("kept draft 中文")
        streaming = wait(console, process, lambda s: "kept draft 中文" in composer(s), "draft while streaming")
        saved_cursor = streaming["cursor"]["x"]
        console.key(0x1B, "\x1b")
        normal_stream = wait(console, process, lambda s: "VIM NORMAL" in s["text"] and "NEXT MESSAGE" in s["text"], "Vim Escape preserves active request")
        assert "Ctrl+C cancel" in normal_stream["text"]
        evidence["checks"].append("vim-escape-is-normal-without-cancelling-stream")

        console.key(0x52, "\x12", 8)
        wait(console, process, lambda s: "READING" in s["text"] and "kept draft 中文" in composer(s), "separate transcript focus")
        console.inject("gg")
        wait(console, process, lambda s: "reading history" in s["text"], "read oldest output")
        console.key(0x0D, "\r")
        console.inject("dd")
        console.inject("\x1b[200~must-stay-out-of-composer\x1b[201~")
        read = wait(console, process, lambda s: "READING" in s["text"] and "kept draft 中文" in composer(s), "read focus cannot send or edit")
        assert "must-stay-out-of-composer" not in read["text"] and "1 queued" not in read["text"]
        evidence["snapshots"]["reading-draft-preserved"] = read
        console.inject("q")
        returned = wait(console, process, lambda s: "READING" not in s["text"] and "VIM NORMAL" in s["text"], "read returns to original composer")
        assert "kept draft 中文" in composer(returned) and returned["cursor"]["x"] == saved_cursor
        evidence["checks"].append("reading-focus-scroll-and-paste-preserve-draft-cursor")
        console.key(0x43, "\x03", 8)
        wait(console, process, lambda s: "NEXT MESSAGE" not in s["text"] and "kept draft 中文" in composer(s), "explicit Ctrl+C exits busy state")
        # A preserved history anchor replaces the transient status line. Follow
        # output explicitly before checking the cancellation status itself.
        console.key(0x23, "", 8)
        cancelled = wait(console, process, lambda s: "Cancelled" in s["text"] and "NEXT MESSAGE" not in s["text"], "explicit Ctrl+C cancel")
        assert "kept draft 中文" in composer(cancelled)
        evidence["checks"].append("explicit-ctrl-c-cancels-vim-stream-and-preserves-draft")

        # Reset is session-only; it neither writes nor deletes the user map.
        console.inject("i")
        console.key(0x55, "\x15", 8)
        console.inject("/keys reset")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Candidate completed" in s["text"] and "/keys reset" in composer(s), "reset completion")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Default editor" in s["text"] and "VIM NORMAL" not in s["text"] and "VIM INSERT" not in s["text"], "reset to default editor")
        assert keymap.read_text(encoding="utf-8") == payload
        console.command("stream")
        wait(console, process, lambda s: "NEXT MESSAGE" in s["text"], "default-mode stream")
        console.inject("default kept")
        wait(console, process, lambda s: "default kept" in composer(s), "default-mode draft")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "NEXT MESSAGE" not in s["text"] and "default kept" in composer(s), "unchanged default Escape cancellation")
        evidence["checks"].append("session-only-reset-and-default-escape-compatibility")
        console.key(0x55, "\x15", 8)
        console.command("/quit")
        wait(console, process, lambda s: "Command completed" in s["text"] and "/quit" in composer(s), "quit completion")
        console.key(0x0D, "\r")
        assert process.wait(timeout=8) == 0
        assert console.modes() == baseline, (baseline, console.modes())
        evidence["checks"].append("console-modes-restored-after-editor-session")
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None:
            evidence["last_screen"] = console.read(viewport=True)
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        write_json(args.evidence, evidence)


def controller(args):
    kernel = kernel_api()
    scratch = Path(tempfile.mkdtemp(prefix="sencode-editor-console-")).resolve()
    job = checked(kernel.CreateJobObjectW(None, None))
    process = None
    try:
        ready = scratch / "ready"
        limits = JobExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000
        checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), str(args.executable), "--worker", "--scratch", str(scratch), "--ready", str(ready), "--evidence", str(args.evidence)], startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE)
        checked(kernel.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)))
        ready.write_text("assigned", encoding="ascii")
        code = process.wait(timeout=90)
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        if code or evidence["result"] != "passed":
            raise AssertionError(evidence.get("error", f"Worker failed {code}"))
        print(f"Real editor console: {len(evidence['checks'])} checks passed")
        print(f"Evidence: {args.evidence}")
    finally:
        checked(kernel.CloseHandle(job))
        if process is not None:
            process.wait(timeout=5)
        remove_owned_tree(scratch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[1] / "target/ui-editor/editor-console-evidence.json")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    args.executable = args.executable.resolve(strict=True)
    args.evidence = args.evidence.resolve()
    worker(args) if args.worker else controller(args)


if __name__ == "__main__":
    main()
