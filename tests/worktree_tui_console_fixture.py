"""Real-main worktree integration in an owned hidden Windows console.

Only temporary Git repositories, profiles, databases and child processes are
used. There is no provider, real credential, clipboard or user database access.
The optional native driver uses the same owned console for fresh approvals.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
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
import traceback

from tui_console_fixture import (
    Console, JobExtendedLimits, checked, environment_for, kernel_api,
    remove_owned_tree, write_json,
)
from fullscreen_console_fixture import wait, down_to


def git(executable, environment, cwd, *arguments):
    result = subprocess.run([str(executable), "--no-pager", *arguments], cwd=cwd,
                            env=environment, capture_output=True, timeout=15)
    assert result.returncode == 0, (arguments, result.stdout, result.stderr)
    return result.stdout


def repository(path, executable, environment):
    path.mkdir()
    git(executable, environment, path, "init", "-b", "main")
    git(executable, environment, path, "config", "user.name", "Isolated TUI Fixture")
    git(executable, environment, path, "config", "user.email", "tui@example.invalid")
    (path / "file.txt").write_text("base\n", encoding="utf-8")
    git(executable, environment, path, "add", "--", "file.txt")
    git(executable, environment, path, "commit", "-m", "fixture base")


def build_slow_git(args, directory):
    """Forward to real Git except an explicitly marked synthetic slow step."""
    directory.mkdir()
    real_git = str(args.git).replace("\\", "\\\\").replace('"', '\\"')
    source = directory / "git-probe.c"
    source.write_text(r'''
#define _CRT_SECURE_NO_WARNINGS
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
int wmain(int argc, wchar_t** argv) {
 if(argc == 2 && !wcscmp(argv[1], L"--owned-child")){ Sleep(60000); return 0; }
 wchar_t image[32768]; GetModuleFileNameW(NULL,image,32768);
 wchar_t dir[32768]; wcscpy(dir,image); wchar_t* end=wcsrchr(dir,L'\\'); if(!end)return 2; end[1]=0;
 wchar_t path[32768]; swprintf(path,32768,L"%lsmode",dir);
 FILE* f=_wfopen(path,L"rb"); int mode=0; if(f){mode=fgetc(f);fclose(f);}
 int slow=0; for(int i=1;i<argc;i++) if((mode=='s' && !wcscmp(argv[i],L"status")) || (mode=='i' && !wcscmp(argv[i],L"rev-parse")))slow=1;
 if(slow){
  wchar_t command[32768]; swprintf(command,32768,L"\"%ls\" --owned-child",image);
  STARTUPINFOW start={0}; PROCESS_INFORMATION child={0}; start.cb=sizeof(start);
  if(!CreateProcessW(image,command,NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,NULL,&start,&child))return 3;
  swprintf(path,32768,L"%lschild.pid",dir); f=_wfopen(path,L"wb"); if(!f)return 4;
  fprintf(f,"%lu",child.dwProcessId); fclose(f); CloseHandle(child.hThread);CloseHandle(child.hProcess);
  Sleep(60000);return 0;
 }
 const wchar_t* rest=GetCommandLineW();
 if(*rest==L'"'){rest++;while(*rest && *rest!=L'"')rest++;if(*rest)rest++;}
 else {while(*rest && *rest!=L' ' && *rest!=L'\t')rest++;}
 wchar_t command[32768]; if(wcslen(rest)+wcslen(REAL_GIT)+4>=32768)return 5;
 swprintf(command,32768,L"\"%ls\"%ls",REAL_GIT,rest);
 STARTUPINFOW start={0};PROCESS_INFORMATION child={0};start.cb=sizeof(start);start.dwFlags=STARTF_USESTDHANDLES;
 start.hStdInput=GetStdHandle(STD_INPUT_HANDLE);start.hStdOutput=GetStdHandle(STD_OUTPUT_HANDLE);start.hStdError=GetStdHandle(STD_ERROR_HANDLE);
 if(!CreateProcessW(REAL_GIT,command,NULL,NULL,TRUE,CREATE_NO_WINDOW,NULL,NULL,&start,&child))return 6;
 CloseHandle(child.hThread);WaitForSingleObject(child.hProcess,INFINITE);DWORD code=0;GetExitCodeProcess(child.hProcess,&code);CloseHandle(child.hProcess);return (int)code;
}
'''.replace("REAL_GIT", 'L"' + real_git + '"'), encoding="utf-8")
    built = subprocess.run([str(args.clang), "-std=c11", "-O1", str(source), "-o", str(directory / "git.exe")],
                           capture_output=True, timeout=30)
    assert built.returncode == 0, built.stderr.decode(errors="replace")


def child_stopped(identifier):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    process = kernel.OpenProcess(0x100000, False, identifier)
    if process:
        try:
            assert kernel.WaitForSingleObject(process, 5000) == 0, "Owned Git descendant survived cancellation"
        finally:
            kernel.CloseHandle(process)


def worker(args):
    evidence = {"schema": 1, "scope": "native-worktree-state-hidden-console" if args.native_only else "real-main-worktree-hidden-console", "platform": "windows-x64",
                "binary_sha256": hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                "result": "running", "checks": [], "snapshots": {}}
    process = None
    try:
        deadline = time.monotonic() + 10
        while not args.ready.exists():
            if time.monotonic() > deadline:
                raise AssertionError("Owned process Job was not established")
            time.sleep(0.02)
        console = Console()
        console.resize(120, 40)
        console.clear()
        baseline = console.modes()
        environment = environment_for(args.scratch)
        environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="NUL", GIT_TERMINAL_PROMPT="0")
        environment["PATH"] = str(args.git.parent) + ";" + environment["PATH"]
        if args.native:
            native_repo = args.scratch / "native 用户 repo"
            repository(native_repo, args.git, environment)
            native = subprocess.Popen([str(args.native), "--cwd", str(native_repo), "--database", str(args.scratch / "native.sqlite")],
                                      cwd=native_repo, env=environment)
            assert native.wait(timeout=40) == 0, console.read(viewport=True)["text"]
            assert console.modes() == baseline
            evidence["native_sha256"] = hashlib.sha256(args.native.read_bytes()).hexdigest()
            evidence["checks"].append("native-state-machine-real-console-and-sticky-unknown-cleanup")
        if args.native_only:
            assert args.native, "--native-only requires --native"
            evidence["result"] = "passed"
            return

        workspace = args.scratch / "source 用户 workspace"
        repository(workspace, args.git, environment)
        original_index = (workspace / ".git/index").read_bytes()
        (workspace / "file.txt").write_text("preserved source edits 中文\n", encoding="utf-8")
        original_status = git(args.git, environment, workspace, "status", "--porcelain=v1", "-z")
        database = args.scratch / "main.sqlite"
        common = ["--database", str(database), "--cwd", str(workspace)]
        initialized = subprocess.run([str(args.executable), *common, "doctor"], cwd=workspace,
                                     env=environment, capture_output=True, timeout=20)
        assert initialized.returncode == 0, initialized.stderr.decode(errors="replace")
        shim = args.scratch / "controlled-git"
        build_slow_git(args, shim)

        def launch(slow=False):
            console.clear()
            active_environment = dict(environment)
            if slow:
                active_environment["PATH"] = str(shim) + ";" + active_environment["PATH"]
            launched = subprocess.Popen([str(args.executable), *common], cwd=workspace, env=active_environment)
            wait(console, launched, lambda s: "S E N C O D E" in s["text"] and "MESSAGE" in s["text"], "real CLI home")
            time.sleep(0.15)  # Let the independent idle execution child publish ready.
            return launched

        def slash(text, stale_approval=False):
            console.key(0x55, "\x15", 8)
            console.inject(text)
            def composer(screen):
                active = False
                lines = []
                for row in screen["rows"]:
                    value = row["text"]
                    if "╭─ MESSAGE" in value or "╭─ NEXT MESSAGE" in value:
                        active = True
                        continue
                    if active and "╰" in value:
                        break
                    if active:
                        # With no placeholder, an empty composer is just ">"
                        # after trimming. It is a prompt marker, not a draft.
                        lines.append(value.strip().removeprefix("│").removesuffix("│").strip().removeprefix(">").lstrip())
                result = "".join(lines)
                if result.startswith("Ask anything,") or result.startswith("Keep typing while Sencode"):
                    return ""
                return "".join(result.split())
            wait(console, process, lambda s: "".join(text.split()) in composer(s), text + " draft")
            current = console.read(viewport=True)
            if "COMMANDS" in current["text"] or "COMMAND ARGUMENTS" in current["text"]:
                console.key(0x0D, "\r")
                wait(console, process, lambda s: "COMMANDS" not in s["text"] and "COMMAND ARGUMENTS" not in s["text"], "completion only")
            console.key(0x0D, "\r")
            if stale_approval:
                # Queue these before allowing the slow inspect->preview state
                # machine to finish. They are deliberately not fresh consent.
                console.key(0x28)
                console.key(0x0D, "\r")
            wait(console, process, lambda s: not composer(s), text + " consumed")

        def preview(operation, target):
            slash("/worktree " + operation + " " + str(target))
            screen = wait(console, process, lambda s: "Worktree operation / explicit approval" in s["text"], "fresh exact preview")
            assert "› Cancel" in screen["text"], screen["text"]
            assert not "› Create this" in screen["text"] and not "› Remove this" in screen["text"]
            return screen

        def approve(operation):
            down_to(console, process, "Create this detached worktree" if operation == "create" else "Remove this exact clean worktree")
            console.key(0x0D, "\r")
            wait(console, process, lambda s: "Worktree operation / explicit approval" not in s["text"], "fresh approval consumed")

        def finished(status="complete"):
            return wait(console, process, lambda s: "GIT WORKTREES / " + status in s["text"] and "Worktree finished" in s["text"], "worktree " + status, timeout=20)

        def stop():
            nonlocal process
            slash("/quit")
            assert process.wait(timeout=15) == 0
            assert console.modes() == baseline, (baseline, console.modes())
            process = None

        process = launch()
        console.inject("/worktr")
        wait(console, process, lambda s: "COMMANDS" in s["text"] and "/worktree" in s["text"], "worktree command registry")
        console.key(0x0D, "\r")
        completed = wait(console, process, lambda s: "Command completed" in s["text"] and "COMMANDS" not in s["text"], "worktree first Enter")
        assert "GIT WORKTREES" not in completed["text"]
        console.key(0x0D, "\r")
        evidence["snapshots"]["list"] = finished()
        evidence["checks"].append("registry-menu-first-enter-completes-second-enter-lists")

        target = args.scratch / "created 子 detached"
        evidence["snapshots"]["default-cancel"] = preview("create", target)
        assert not target.exists()
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "Worktree operation cancelled" in s["text"], "default denial")
        assert not target.exists()
        evidence["checks"].append("immutable-preview-default-cancel-no-mutation")

        slash("/worktree create " + str(target), stale_approval=True)
        fresh = wait(console, process, lambda s: "Worktree operation / explicit approval" in s["text"], "stale queued input discarded")
        assert "› Cancel" in fresh["text"] and not target.exists(), fresh["text"]
        evidence["checks"].append("keys-queued-before-preview-cannot-approve")
        approve("create")
        evidence["snapshots"]["created"] = finished()
        assert target.is_dir()
        assert git(args.git, environment, target, "rev-parse", "--abbrev-ref", "HEAD").strip() == b"HEAD"
        assert (target / "file.txt").read_text(encoding="utf-8") == "base\n"
        assert (workspace / "file.txt").read_text(encoding="utf-8") == "preserved source edits 中文\n"
        assert original_status == git(args.git, environment, workspace, "status", "--porcelain=v1", "-z")
        assert original_index == (workspace / ".git/index").read_bytes()
        evidence["checks"].append("fresh-create-detached-and-preserve-source-edits-index")

        changed_target = args.scratch / "externally occupied"
        preview("create", changed_target)
        changed_target.mkdir()
        (changed_target / "external.txt").write_text("external content", encoding="utf-8")
        approve("create")
        wait(console, process, lambda s: "The approved worktree target changed" in s["text"] and "Worktree stopped" in s["text"], "changed target refused before start")
        assert (changed_target / "external.txt").read_text(encoding="utf-8") == "external content"
        evidence["checks"].append("target-created-after-preview-refuses-without-overwriting")

        changed_head = args.scratch / "stale HEAD"
        preview("create", changed_head)
        git(args.git, environment, workspace, "commit", "--allow-empty", "-m", "advance HEAD after preview")
        approve("create")
        finished("refused")
        assert not changed_head.exists()
        evidence["checks"].append("head-changed-after-preview-refuses-one-use-approval")

        slash("/plan")
        wait(console, process, lambda s: "Plan mode enabled" in s["text"], "Plan enabled")
        slash("/worktree create " + str(changed_head))
        wait(console, process, lambda s: "Plan mode refuses worktree creation" in s["text"], "Plan creation denied")
        slash("/worktree remove " + str(target))
        wait(console, process, lambda s: "Plan mode refuses worktree creation" in s["text"], "Plan removal denied")
        assert target.exists() and not changed_head.exists()
        slash("/worktree list")
        finished()
        evidence["checks"].append("plan-create-remove-denied-list-permitted")
        slash("/plan approve")
        wait(console, process, lambda s: "Plan approved" in s["text"], "Plan explicitly approved")

        (target / "untracked.txt").write_text("must survive", encoding="utf-8")
        preview("remove", target)
        approve("remove")
        evidence["snapshots"]["dirty-refused"] = finished("refused")
        assert (target / "untracked.txt").read_text(encoding="utf-8") == "must survive"
        (target / "untracked.txt").unlink()
        evidence["checks"].append("approved-dirty-removal-refused-without-force")
        stop()

        # This marker delays the real removal status probe after its SQLite
        # writer reservation; it also spawns a descendant to verify cleanup.
        (shim / "mode").write_text("status", encoding="ascii")
        process = launch(slow=True)
        preview("remove", target)
        approve("remove")
        wait(console, process, lambda s: (shim / "child.pid").exists(), "reserved slow removal")
        child = int((shim / "child.pid").read_text(encoding="ascii"))
        console.command("queued while Git owns the interface")
        wait(console, process, lambda s: "1 queued" in s["text"], "queue held during Git reservation")
        with sqlite3.connect(database, timeout=0.05) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as error:
                assert "locked" in str(error).lower(), str(error)
            else:
                db.rollback()
                raise AssertionError("Removal did not retain its SQLite writer reservation")
        slash("/connections unavailable-fixture-id")
        wait(console, process, lambda s: "A worktree job owns this interface" in s["text"], "state mutation refused during reservation")
        console.key(0x43, "\x03", 8)
        evidence["snapshots"]["cancelled"] = finished("cancelled")
        child_stopped(child)
        assert target.exists()
        with sqlite3.connect(database, timeout=1) as db:
            db.execute("BEGIN IMMEDIATE")
            db.rollback()
            assert db.execute("SELECT COUNT(*) FROM shared_tool_ledger WHERE name='user_terminal'").fetchone()[0] == 0
        assert "queue paused" in console.read(viewport=True)["text"]
        evidence["checks"].append("cancel-reserved-removal-reaps-descendant-releases-writer-holds-queue")
        (shim / "mode").unlink()
        slash("/queue clear")
        wait(console, process, lambda s: "Cancel queued tasks?" in s["text"], "queue clear approval")
        down_to(console, process, "Cancel every queued task")
        console.key(0x0D, "\r")
        wait(console, process, lambda s: "QUEUED TASKS" in s["text"] and "Cancel queued tasks?" not in s["text"], "queued cancellation consumed")
        console.key(0x1B, "\x1b")
        wait(console, process, lambda s: "QUEUED TASKS" not in s["text"], "empty paused queue closed")
        preview("remove", target)
        approve("remove")
        finished()
        assert not target.exists()
        evidence["checks"].append("clean-removal-fresh-approval-no-terminal-launch")
        stop()
        evidence["checks"].append("real-main-exits-restore-console-modes")

        (shim / "child.pid").unlink()
        (shim / "mode").write_text("inspect", encoding="ascii")
        process = launch(slow=True)
        slash("/worktree list")
        wait(console, process, lambda s: (shim / "child.pid").exists(), "slow inspection descendant")
        child = int((shim / "child.pid").read_text(encoding="ascii"))
        slash("/quit")
        assert process.wait(timeout=15) == 0
        child_stopped(child)
        assert console.modes() == baseline
        process = None
        evidence["checks"].append("exit-during-worktree-waits-for-tree-quiescence-and-restores-console")
        evidence["result"] = "passed"
    except BaseException:
        evidence["result"] = "failed"
        evidence["error"] = traceback.format_exc()
        try:
            evidence["last_screen"] = console.read(viewport=True)
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
    scratch = Path(tempfile.mkdtemp(prefix="sencode-worktree-tui-"))
    job = checked(kernel.CreateJobObjectW(None, None))
    process = None
    try:
        limits = JobExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000
        checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        child_args = [sys.executable, str(Path(__file__).resolve()), str(args.executable), "--worker",
                      "--scratch", str(scratch), "--ready", str(scratch / "ready"),
                      "--evidence", str(args.evidence), "--git", str(args.git), "--clang", str(args.clang)]
        if args.native:
            child_args += ["--native", str(args.native)]
        if args.native_only:
            child_args.append("--native-only")
        process = subprocess.Popen(child_args, startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE)
        checked(kernel.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)))
        (scratch / "ready").write_text("assigned", encoding="ascii")
        code = process.wait(timeout=180)
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        if code or evidence["result"] != "passed":
            raise AssertionError(evidence.get("error", f"Worker failed {code}"))
        print(f"{'Native worktree state' if args.native_only else 'Real-main worktree TUI'}: {len(evidence['checks'])} checks passed")
        print(f"Evidence: {args.evidence}")
    finally:
        checked(kernel.CloseHandle(job))
        if process is not None:
            process.wait(timeout=5)
        # Git's object files are read only, so inventory each literal file and
        # make it removable before using the shared empty-directory cleanup.
        for path in scratch.rglob("*"):
            if path.is_file():
                path.chmod(0o600)
        remove_owned_tree(scratch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--native-only", action="store_true", help="Run only the real-console native state driver; no production-main claim")
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[1] / "target/worktree-tui/console-evidence.json")
    parser.add_argument("--git", type=Path, default=Path(shutil.which("git") or "missing-git.exe"))
    parser.add_argument("--clang", type=Path, default=Path(os.environ["LOCALAPPDATA"]) / "SengooToolchain/clang+llvm-19.1.7-x86_64-pc-windows-msvc/bin/clang.exe")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--ready", type=Path)
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("This gate requires a real Windows console")
    for name in ("executable", "native", "git", "clang"):
        value = getattr(args, name)
        if value:
            setattr(args, name, value.resolve(strict=True))
    args.evidence = args.evidence.resolve()
    if args.worker:
        worker(args)
    else:
        controller(args)


if __name__ == "__main__":
    main()
