"""Drive the actual Sengoo CLI's explicit-user ConPTY pane in an owned console.

Uses an isolated database/profile/workspace, no API connections or credentials.
Only the hidden test console receives input. Child output, process handles and
durable ledger rows provide independent evidence of execution and tree cleanup.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback

from tui_console_fixture import (
    Console, Coord, JobExtendedLimits, InputRecord, KeyEvent, CharUnion, checked, environment_for, kernel_api,
    remove_owned_tree, write_json,
)
from fullscreen_console_fixture import wait, down_to


def composer(screen):
    return "\n".join(row["text"] for row in screen["rows"] if row["text"].lstrip().startswith(("│ > ", "│   ")))


def output_line(screen, text):
    return any(row["text"].strip() == text for row in screen["rows"])


def powershell_prompt_after(screen, marker):
    found = False
    for row in screen["rows"]:
        text = row["text"].strip()
        if text == marker:
            found = True
        elif found and text.startswith("PS ") and text.endswith(">"):
            return True
    return False


def resize_fullscreen(console, columns, rows):
    # Active alternate buffers reject direct SetConsoleScreenBufferSize on this
    # Windows host. Resize only this owned, hidden conhost window instead, as a
    # normal window resize would; font-cell deltas avoid DPI/border assumptions.
    class FontInfo(ctypes.Structure):
        _fields_ = [("index", wintypes.DWORD), ("size", Coord)]
    console.kernel.GetConsoleWindow.argtypes = []
    console.kernel.GetConsoleWindow.restype = wintypes.HWND
    console.kernel.GetCurrentConsoleFont.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(FontInfo)]
    console.kernel.GetCurrentConsoleFont.restype = wintypes.BOOL
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user.GetWindowRect.restype = wintypes.BOOL
    user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user.SetWindowPos.restype = wintypes.BOOL
    window = console.kernel.GetConsoleWindow()
    assert window, "Owned conhost has no window handle"
    font = FontInfo()
    checked(console.kernel.GetCurrentConsoleFont(console.output, False, ctypes.byref(font)))
    for _ in range(3):
        info = console.info()
        current_columns = info.srWindow.Right - info.srWindow.Left + 1
        current_rows = info.srWindow.Bottom - info.srWindow.Top + 1
        if current_columns == columns and current_rows == rows:
            return
        rect = wintypes.RECT()
        checked(user.GetWindowRect(window, ctypes.byref(rect)))
        width = rect.right - rect.left + (columns - current_columns) * font.size.X
        height = rect.bottom - rect.top + (rows - current_rows) * font.size.Y
        checked(user.SetWindowPos(window, None, 0, 0, width, height, 0x0016))
        time.sleep(0.05)
    info = console.info()
    assert info.srWindow.Right - info.srWindow.Left + 1 == columns and info.srWindow.Bottom - info.srWindow.Top + 1 == rows, "Owned hidden window did not reach requested grid size"


def ledger(database):
    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as connection:
        return [{"name": name, "state": state, "result": json.loads(result) if result else None}
                for name, state, result in connection.execute("SELECT name,state,result FROM shared_tool_ledger WHERE name='user_terminal' ORDER BY updated_at,call_id")]


def wait_file(path, description, timeout=12):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_size:
            return path.read_text(encoding="utf-8-sig").strip()
        time.sleep(0.025)
    raise AssertionError(f"Timed out waiting for {description}: {path.name}")


def worker(args):
    evidence = {"schema": 1, "scope": "actual-main-user-terminal-owned-console",
                "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                "fixture_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "clipboard_probe": "Sequence number only; clipboard contents were neither read nor written",
                "resize_method": "Resize this test's hidden conhost window by font-cell pixel deltas; no user terminal is attached",
                "result": "running", "checks": [], "snapshots": {}}
    process = None
    handles = []
    kernel = kernel_api()
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.SetConsoleTitleW.argtypes = [wintypes.LPCWSTR]
    kernel.SetConsoleTitleW.restype = wintypes.BOOL
    kernel.GetConsoleTitleW.argtypes = [wintypes.LPWSTR, wintypes.DWORD]
    kernel.GetConsoleTitleW.restype = wintypes.DWORD
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.GetClipboardSequenceNumber.argtypes = []
    user.GetClipboardSequenceNumber.restype = wintypes.DWORD
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
        evidence["console_before"] = baseline
        title = "Sencode owned terminal-pane fixture"
        checked(kernel.SetConsoleTitleW(title))
        workspace = args.scratch / "outside-project-中文"
        workspace.mkdir()
        database = args.scratch / "isolated.sqlite"
        environment = environment_for(args.scratch)
        common = ["--database", str(database), "--cwd", str(workspace)]
        initialized = subprocess.run([str(args.executable), *common, "doctor"], cwd=workspace,
                                     env=environment, capture_output=True, timeout=30)
        assert initialized.returncode == 0, initialized.stderr.decode(errors="replace")
        process = subprocess.Popen([str(args.executable), *common], cwd=workspace, env=environment)
        wait(console, process, lambda s: "S E N C O D E" in s["text"] and "MESSAGE" in s["text"], "actual main home without an API connection")

        def terminal_choice(shell, stale_approval=False):
            console.inject("/terminal " + shell)
            wait(console, process, lambda s: "COMMAND ARGUMENTS" in s["text"] and shell in composer(s), "terminal arguments")
            console.key(0x0D, "\r")
            completed = wait(console, process, lambda s: "Candidate completed" in s["text"] and "COMMAND ARGUMENTS" not in s["text"] and "/terminal " + shell in composer(s), "first Enter only completes terminal choice")
            assert "Interactive terminal / explicit approval" not in completed["text"]
            assert "SENCODE / USER TERMINAL" not in completed["text"]
            if stale_approval:
                # One OS write queues submit + Down + Enter before the host
                # creates its fresh approval. Trailing input must be discarded.
                events = (InputRecord * 3)()
                for event, virtual_key, unit in zip(events, (0x0D, 0x28, 0x0D), (13, 0, 13)):
                    event.EventType = 1
                    event.Event.KeyEvent = KeyEvent(True, 1, virtual_key, 0, CharUnion(unit), 0)
                written = wintypes.DWORD()
                checked(console.kernel.WriteConsoleInputW(console.input, events, 3, ctypes.byref(written)))
                assert written.value == 3
            else:
                console.key(0x0D, "\r")
            approval = wait(console, process, lambda s: "Interactive terminal / explicit approval" in s["text"] and "› Cancel" in s["text"], "second Enter opens default-cancel launch approval")
            if stale_approval:
                time.sleep(0.15)
                approval = console.read(viewport=True)
                assert "Interactive terminal / explicit approval" in approval["text"] and "› Cancel" in approval["text"]
                assert ledger(database) == []
            return approval

        first = terminal_choice("powershell", stale_approval=True)
        evidence["snapshots"]["default-cancel-approval"] = first
        assert ledger(database) == []
        console.key(0x0D, "\r")
        cancelled = wait(console, process, lambda s: "Interactive terminal / explicit approval" not in s["text"] and "MESSAGE" in s["text"], "default cancel")
        assert ledger(database) == [] and "SENCODE / USER TERMINAL" not in cancelled["text"]
        assert "/terminal" not in composer(cancelled)
        evidence["checks"].append("two-enter-completion-and-default-cancel-never-spawn")
        evidence["checks"].append("queued-down-enter-cannot-cross-fresh-launch-approval")

        terminal_choice("cmd")
        console.key(0x1B, "\x1b")
        escaped = wait(console, process, lambda s: "Interactive terminal / explicit approval" not in s["text"] and "MESSAGE" in s["text"], "Escape cancels launch")
        assert ledger(database) == [] and "SENCODE / USER TERMINAL" not in escaped["text"]
        evidence["checks"].append("escape-dismisses-launch-without-an-execution")

        terminal_choice("powershell")
        down_to(console, process, "Start user terminal")
        console.key(0x0D, "\r")
        started = wait(console, process, lambda s: "SENCODE / USER TERMINAL" in s["text"] and "Ctrl+Q closes" in s["text"], "freshly approved real PowerShell")
        assert len(ledger(database)) == 1 and ledger(database)[0]["state"] == "running"
        evidence["snapshots"]["powershell-pane"] = started
        evidence["checks"].append("fresh-down-enter-approval-starts-durable-user-terminal")

        console.command("Write-Output ('PTY_'+'中文_OK')")
        unicode = wait(console, process, lambda s: output_line(s, "PTY_中文_OK"), "real PowerShell Unicode output")
        evidence["snapshots"]["unicode-shell-output"] = unicode
        evidence["checks"].append("real-powershell-unicode-echo")

        resize_fullscreen(console, 88, 28)
        wait(console, process, lambda s: "SENCODE / USER TERMINAL" in s["text"] and len(s["rows"]) == 28, "pane resize")
        console.command("Write-Output ('SIZE_'+[Console]::WindowWidth+'_'+[Console]::WindowHeight)")
        resized = wait(console, process, lambda s: output_line(s, "SIZE_84_23"), "child ConPTY dimensions follow outer resize")
        evidence["snapshots"]["resized-pane"] = resized
        resize_fullscreen(console, 110, 35)
        wait(console, process, lambda s: "SENCODE / USER TERMINAL" in s["text"] and len(s["rows"]) == 35, "pane restored size")
        evidence["checks"].append("resize-propagates-to-child-pty-and-owned-screen")

        # Never read or write the user's clipboard. Its sequence is sufficient
        # to observe that a child OSC52 attempt caused no clipboard mutation.
        sequence = user.GetClipboardSequenceNumber()
        console.command("[Console]::Write(([char]27)+']52;c;c2VuY29kZS1maXh0dXJl'+([char]7));[Console]::Write(([char]27)+']0;CHILD_MUST_NOT_SET_OUTER'+([char]7));Write-Output ('OSC_'+'DONE')")
        escaped_output = wait(console, process, lambda s: output_line(s, "OSC_DONE"), "child OSC payload completed")
        title_buffer = ctypes.create_unicode_buffer(2048)
        kernel.GetConsoleTitleW(title_buffer, len(title_buffer))
        assert title_buffer.value == title, title_buffer.value
        assert user.GetClipboardSequenceNumber() == sequence, "Clipboard sequence changed during child OSC52 probe"
        assert "SENCODE / USER TERMINAL" in escaped_output["text"]
        evidence["checks"].append("child-osc52-and-title-escape-do-not-change-outer-state")

        console.command("Write-Output ('CTRL_'+'WAIT');Start-Sleep -Seconds 30;Write-Output ('CTRL_'+'UNEXPECTED')")
        wait(console, process, lambda s: output_line(s, "CTRL_WAIT"), "foreground shell command before Ctrl+C")
        console.key(0x43, "\x03", 8)
        wait(console, process, lambda s: powershell_prompt_after(s, "CTRL_WAIT"), "shell prompt after Ctrl+C interrupt")
        console.command("Write-Output ('AFTER_'+'CTRL_C')")
        after_interrupt = wait(console, process, lambda s: output_line(s, "AFTER_CTRL_C"), "Ctrl+C reaches the shell while the pane stays alive")
        assert not output_line(after_interrupt, "CTRL_UNEXPECTED")
        assert "SENCODE / USER TERMINAL" in after_interrupt["text"] and ledger(database)[0]["state"] == "running"
        evidence["checks"].append("ctrl-c-interrupts-shell-command-without-exiting-pane")

        # Spawn a grandchild inside this owned test Job. Retaining handles
        # distinguishes confirmed process exit from PID disappearance/reuse.
        grandchild = workspace / "grandchild.ps1"
        child = workspace / "child.ps1"
        tree = workspace / "tree.ps1"
        grandchild.write_text("$PID | Set-Content -Encoding utf8 -LiteralPath 'grandchild.pid'\nwhile ($true) { Add-Content -Encoding utf8 -LiteralPath 'grandchild.ticks' -Value 'tick'; Start-Sleep -Milliseconds 100 }\n", encoding="utf-8-sig")
        child.write_text("$PID | Set-Content -Encoding utf8 -LiteralPath 'child.pid'\nStart-Process -FilePath ($PSHOME+'\\powershell.exe') -ArgumentList @('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File','grandchild.ps1') -WindowStyle Hidden | Out-Null\nwhile ($true) { Start-Sleep -Milliseconds 100 }\n", encoding="utf-8-sig")
        tree.write_text("$PID | Set-Content -Encoding utf8 -LiteralPath 'shell.pid'\nStart-Process -FilePath ($PSHOME+'\\powershell.exe') -ArgumentList @('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File','child.ps1') -WindowStyle Hidden | Out-Null\nWrite-Output ('TREE_'+'READY')\nwhile ($true) { Start-Sleep -Milliseconds 100 }\n", encoding="utf-8-sig")
        console.command("& ([scriptblock]::Create([IO.File]::ReadAllText('tree.ps1')))")
        wait(console, process, lambda s: output_line(s, "TREE_READY"), "shell process tree started")
        pids = []
        for name in ("shell", "child", "grandchild"):
            identifier = int(wait_file(workspace / (name + ".pid"), name + " PID"))
            handle = checked(kernel.OpenProcess(0x100000 | 0x1000, False, identifier))
            handles.append(handle)
            assert kernel.WaitForSingleObject(handle, 0) == 258, name + " unexpectedly exited before close"
            pids.append(identifier)
        wait_file(workspace / "grandchild.ticks", "grandchild heartbeat")
        console.key(0x51, "\x11", 8)
        returned = wait(console, process, lambda s: "SENCODE / USER TERMINAL" not in s["text"] and "MESSAGE" in s["text"], "Ctrl+Q tree close and composer return", timeout=20)
        for handle in handles:
            assert kernel.WaitForSingleObject(handle, 5000) == 0, "A PTY descendant survived Ctrl+Q"
        rows = ledger(database)
        assert rows[0]["state"] == "complete" and rows[0]["result"]["tree_quiescent"] and not rows[0]["result"]["cleanup_unknown"], rows
        assert rows[0]["result"]["exit_code"] != -1, "Tree cleanup must record the observed process exit code"
        assert "/terminal" not in composer(returned) and "tree.ps1" not in composer(returned), composer(returned)
        evidence["tree_processes"] = pids
        evidence["snapshots"]["returned-composer"] = returned
        evidence["checks"].append("ctrl-q-certifies-root-child-grandchild-exit-and-returns-composer")
        console.inject("fresh draft 中文")
        wait(console, process, lambda s: "fresh draft 中文" in composer(s), "composer remains independently editable")
        console.key(0x55, "\x15", 8)
        evidence["checks"].append("submitted-launch-text-is-not-restored-as-a-draft")

        def slash(name, argument=False):
            console.inject(name)
            wait(console, process, lambda s: ("COMMAND ARGUMENTS" if argument else "COMMANDS") in s["text"] and name in composer(s), "slash menu " + name)
            console.key(0x0D, "\r")
            wait(console, process, lambda s: "completed" in s["text"] and "COMMAND ARGUMENTS" not in s["text"] and "COMMANDS" not in s["text"], "slash completion " + name)
            console.key(0x0D, "\r")

        slash("/plan")
        wait(console, process, lambda s: "PLAN / read only" in s["text"], "local Plan mode")
        count = len(ledger(database))
        console.inject("/terminal cmd")
        wait(console, process, lambda s: "COMMAND ARGUMENTS" in s["text"], "Plan terminal argument menu")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Candidate completed" in s["text"] and "COMMAND ARGUMENTS" not in s["text"], "Plan terminal completion")
        console.key(0x0D, "\r")
        refused = wait(console, process, lambda s: "Action stopped, code 7" in s["text"], "Plan rejects terminal launch")
        assert "Interactive terminal / explicit approval" not in refused["text"] and "SENCODE / USER TERMINAL" not in refused["text"] and len(ledger(database)) == count
        evidence["checks"].append("plan-mode-refuses-launch-before-process-or-ledger-claim")
        slash("/plan approve", argument=True)
        wait(console, process, lambda s: "PLAN / read only" not in s["text"], "leave Plan explicitly")

        terminal_choice("cmd")
        assert len(ledger(database)) == count and ledger(database)[0]["state"] == "complete"
        evidence["checks"].append("completed-terminal-approval-is-not-reused-for-a-new-shell")
        down_to(console, process, "Start user terminal")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "SENCODE / USER TERMINAL" in s["text"], "fresh CMD launch")
        console.command("echo CMD_PANE_OK")
        wait(console, process, lambda s: output_line(s, "CMD_PANE_OK"), "real CMD output")
        console.command("exit")
        wait(console, process, lambda s: "Terminal finished / Esc returns" in s["text"], "natural shell exit certification", timeout=20)
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "SENCODE / USER TERMINAL" not in s["text"] and "MESSAGE" in s["text"], "Escape returns after certified natural exit")
        evidence["checks"].append("cmd-natural-exit-certifies-before-return")
        slash("/quit")
        assert process.wait(timeout=15) == 0
        assert console.modes() == baseline, (baseline, console.modes())
        evidence["console_after"] = console.modes()
        with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as connection:
            assert connection.execute("SELECT COUNT(*) FROM shared_executions WHERE active<>0 OR cleanup_required<>0").fetchone()[0] == 0
            assert connection.execute("SELECT COUNT(*) FROM shared_tool_ledger WHERE state='running'").fetchone()[0] == 0
            assert connection.execute("SELECT COUNT(*) FROM connection_configs").fetchone()[0] == 0
        evidence["ledger"] = ledger(database)
        evidence["checks"].append("main-exit-restores-console-and-leaves-no-active-ledger-or-credentials")
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        if process is not None and process.poll() is None:
            evidence["last_screen"] = console.read(viewport=True)
        raise
    finally:
        for handle in handles:
            checked(kernel.CloseHandle(handle))
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=8)
        write_json(args.evidence, evidence)


def controller(args):
    kernel = kernel_api()
    scratch = Path(tempfile.mkdtemp(prefix="sencode-terminal-pane-")).resolve()
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
        code = process.wait(timeout=150)
        report = json.loads(args.evidence.read_text(encoding="utf-8"))
        if code or report["result"] != "passed":
            raise AssertionError(report.get("error", f"Worker failed {code}"))
        print(f"Actual main terminal pane: {len(report['checks'])} checks passed")
        print(f"Evidence: {args.evidence}")
    finally:
        checked(kernel.CloseHandle(job))
        if process is not None:
            process.wait(timeout=8)
        remove_owned_tree(scratch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[1] / "target/terminal-pane-draft/terminal-pane-console-evidence.json")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    args.executable = args.executable.resolve(strict=True)
    args.evidence = args.evidence.resolve()
    worker(args) if args.worker else controller(args)


if __name__ == "__main__":
    main()
