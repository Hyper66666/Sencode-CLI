"""Real local Git / SQLite probes for the explicit Sengoo worktree owner.

All paths, databases, hooks and marker payloads are created beneath one fresh
temporary directory. Cleanup removes inventoried files and then empty folders;
it never recursively deletes or uses force worktree removal.
"""
from __future__ import annotations

import json
import ctypes
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time


EXE = Path(sys.argv[1]).resolve()
GIT = shutil.which("git")
assert GIT, "real Git is required for this fixture"
ROOT = Path(tempfile.mkdtemp(prefix="sencode-worktree-用户 空格-"))
REPO = ROOT / "主工作区 中文"
DB = ROOT / "test-shared.sqlite3"
COUNT = 0


@contextmanager
def database(timeout: float = 5):
    connection = sqlite3.connect(DB, timeout=timeout)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def git(*args: str, cwd: Path = REPO, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    for key in tuple(env):
        if key.startswith("GIT_"):
            del env[key]
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="NUL", GIT_TERMINAL_PROMPT="0")
    result = subprocess.run([GIT, "--no-pager", *args], cwd=cwd, env=env, capture_output=True, timeout=20)
    if check:
        assert result.returncode == 0, (args, result.returncode, result.stdout, result.stderr)
    return result


def run(mode: str, target: Path | str = "", extra: str = "", cwd: Path = REPO, env: dict[str, str] | None = None) -> dict:
    global COUNT
    COUNT += 1
    result = subprocess.run([str(EXE), str(DB), str(cwd), mode, str(target), extra], cwd=ROOT,
                            env=env, capture_output=True, text=True, encoding="utf-8", timeout=40)
    assert result.returncode == 0, (mode, result.returncode, result.stdout, result.stderr)
    lines = result.stdout.splitlines()
    assert lines, (mode, result.stderr)
    return json.loads(lines[-1])


def refused(mode: str, target: Path | str, extra: str = "", cwd: Path = REPO) -> dict:
    report = run(mode, target, extra, cwd)
    assert report["status"] == "refused", (mode, report)
    return report


def remove_known_file(path: Path) -> None:
    if path.is_file() or path.is_symlink():
        path.chmod(0o600)
        path.unlink()


def cleanup() -> None:
    # Inventory once; remove only known literal entries and empty directories.
    for directory, _, files in os.walk(ROOT, topdown=False, followlinks=False):
        for name in files:
            remove_known_file(Path(directory) / name)
        for child in Path(directory).iterdir():
            if child.is_symlink():
                child.unlink()
        Path(directory).rmdir()


try:
    REPO.mkdir()
    git("init", "-b", "main")
    git("config", "user.name", "Isolated Worktree Fixture")
    git("config", "user.email", "worktree-fixture@example.invalid")
    (REPO / "file.txt").write_text("base\n", encoding="utf-8")
    (REPO / "staged.txt").write_text("base staged\n", encoding="utf-8")
    (REPO / "filtered.txt").write_text("filtered original\n", encoding="utf-8")
    (REPO / ".gitattributes").write_text("filtered.txt filter=evil\n", encoding="utf-8")
    (REPO / ".gitignore").write_text("ignored.bin\n", encoding="utf-8")
    git("add", "--", ".")
    git("commit", "-m", "isolated fixture base")
    base_head = git("rev-parse", "HEAD").stdout.strip().decode()
    (REPO / "file.txt").write_text("source unstaged 用户\n", encoding="utf-8")
    (REPO / "staged.txt").write_text("source staged\n", encoding="utf-8")
    git("add", "--", "staged.txt")
    (REPO / "untracked.txt").write_text("preserve untracked\n", encoding="utf-8")
    status_before = git("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    index_before = (REPO / ".git" / "index").read_bytes()

    assert run("parse")["status"] == "complete"
    inspection = run("inspect")
    assert inspection["capability"] == "ready" and inspection["head"] == base_head, inspection
    assert len(inspection["worktrees"]) == 1
    nonrepo = ROOT / "非 Git 空间"
    nonrepo.mkdir()
    assert run("inspect", cwd=nonrepo)["capability"] == "not_repository"
    no_path_env = os.environ.copy()
    no_path_env["PATH"] = str(ROOT / "missing-path")
    assert run("inspect", env=no_path_env)["capability"] == "missing_git"
    bare = ROOT / "裸 仓库"
    git("init", "--bare", str(bare))
    assert run("inspect", cwd=bare)["capability"] == "bare_repository"

    created = ROOT / "Detached 子工作区 😀"
    for mode in ("unapproved", "plan", "child", "stale", "plan-late", "lock-source", "lock-repo"):
        refused(mode, created)
        assert not created.exists()
    assert run("cancel")["status"] == "cancelled"
    assert run("timeout")["status"] == "timed_out"
    # Synthetic executables exercise process bounds after real Git proved the
    # integration path. Their source/binaries remain in this temporary root.
    fake_bin = ROOT / "synthetic external git"
    fake_bin.mkdir()
    fake_source = fake_bin / "probe.c"
    fake_source.write_text(r'''
#define _CRT_SECURE_NO_WARNINGS
#include <windows.h>
#include <stdio.h>
#include <string.h>
int wmain(void) {
 wchar_t own[32768]; GetModuleFileNameW(NULL,own,32768);
 wchar_t* slash=wcsrchr(own,L'\\'); if(!slash)return 2; slash[1]=0;
 wchar_t mode_path[32768]; swprintf(mode_path,32768,L"%lsmode",own);
 FILE* file=_wfopen(mode_path,L"rb"); if(!file)return 3;
 int flood=fgetc(file)=='f'; fclose(file);
 if(flood){char bytes[4096];memset(bytes,'x',sizeof(bytes));DWORD count;
   for(int i=0;i<512;i++){WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),bytes,sizeof(bytes),&count,NULL);WriteFile(GetStdHandle(STD_ERROR_HANDLE),bytes,sizeof(bytes),&count,NULL);}
 } else {
   wchar_t system[32768];GetSystemDirectoryW(system,32768);wcscat(system,L"\\cmd.exe");
   wchar_t command[]=L"cmd.exe /d /c ping -n 60 127.0.0.1 >NUL";
   STARTUPINFOW start={0};PROCESS_INFORMATION child={0};start.cb=sizeof(start);
   if(!CreateProcessW(system,command,NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,NULL,&start,&child))return 4;
   wchar_t pid_path[32768];swprintf(pid_path,32768,L"%lschild.pid",own);
   file=_wfopen(pid_path,L"wb");if(!file)return 5;fprintf(file,"%lu",child.dwProcessId);fclose(file);
   CloseHandle(child.hThread);CloseHandle(child.hProcess);
 }
 Sleep(30000);return 0;
}
''', encoding="utf-8")
    clang = Path(os.environ["LOCALAPPDATA"]) / "SengooToolchain/clang+llvm-19.1.7-x86_64-pc-windows-msvc/bin/clang.exe"
    built = subprocess.run([str(clang), "-std=c11", "-O1", str(fake_source), "-o", str(fake_bin / "git.exe")], capture_output=True, timeout=20)
    assert built.returncode == 0, built.stderr
    fake_env = os.environ.copy()
    fake_env["PATH"] = str(fake_bin) + ";" + fake_env.get("PATH", "")
    (fake_bin / "mode").write_text("flood", encoding="ascii")
    bounded = run("inspect", env=fake_env)
    assert bounded["status"] == "failed" and bounded["code"] == 13 and "1 MiB" in bounded["message"], bounded
    assert len(json.dumps(bounded, ensure_ascii=False).encode("utf-8")) < 2200000
    (fake_bin / "mode").write_text("slow", encoding="ascii")
    interrupted = run("cancel-delayed", env=fake_env)
    assert interrupted["status"] == "cancelled", interrupted
    descendant = int((fake_bin / "child.pid").read_text(encoding="ascii"))
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.restype = ctypes.c_void_p
    process = kernel.OpenProcess(0x100000, False, descendant)
    if process:
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        assert kernel.WaitForSingleObject(process, 5000) == 0, "cancelled Git descendant survived"
        kernel.CloseHandle(process)
    junction = ROOT / "junction 指向主目录"
    result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(REPO)],
                            capture_output=True, timeout=10)
    assert result.returncode == 0, (result.stdout, result.stderr)
    refused("create", junction / "不应创建")
    refused("remove", junction)
    junction.rmdir()

    # Executable repo config must never run through status, checkout or hooks.
    hook_dir = ROOT / "malicious hooks"
    hook_dir.mkdir()
    hook_marker = ROOT / "HOOK_RAN"
    hook = hook_dir / "post-checkout"
    hook.write_text("#!/bin/sh\nprintf ran > '" + hook_marker.as_posix() + "'\n", encoding="utf-8")
    hook.chmod(0o700)
    git("config", "core.hooksPath", str(hook_dir))
    markers = {name: ROOT / (name.upper() + "_RAN") for name in ("clean", "smudge", "process", "fsmonitor")}
    for suffix in ("clean", "smudge", "process"):
        payload = ROOT / (suffix + "-payload.cmd")
        payload.write_text("@echo off\r\necho ran>\"" + str(markers[suffix]) + "\"\r\nexit /b 17\r\n", encoding="utf-8")
        git("config", "filter.evil." + suffix, "\"" + str(payload) + "\"")
    git("config", "filter.evil.required", "true")
    fsmonitor = ROOT / "fsmonitor-payload.cmd"
    fsmonitor.write_text("@echo off\r\necho ran>\"" + str(markers["fsmonitor"]) + "\"\r\nexit /b 17\r\n", encoding="utf-8")
    git("config", "core.fsmonitor", "\"" + str(fsmonitor) + "\"")
    made = run("create", created)
    assert made["status"] == "complete" and created.is_dir(), made
    assert (created / "filtered.txt").read_text(encoding="utf-8") == "filtered original\n"
    assert git("symbolic-ref", "-q", "HEAD", cwd=created, check=False).returncode == 1
    assert git("rev-parse", "HEAD", cwd=created).stdout.strip().decode() == base_head
    assert not hook_marker.exists() and all(not marker.exists() for marker in markers.values())
    # --hooksPath=NUL must remain a true Git override, not an empty-string claim.
    assert git("-c", "core.hooksPath=NUL", "config", "--get", "core.hooksPath").stdout.strip() == b"NUL"

    branch_target = ROOT / "分支 工作区"
    branch_name = "codex/用户-exact-branch"
    branch_created = run("create", branch_target, branch_name)
    assert branch_created["status"] == "complete", branch_created
    assert git("symbolic-ref", "--short", "HEAD", cwd=branch_target).stdout.strip().decode() == branch_name
    invalid = run("create", ROOT / "invalid target", "bad..branch")
    assert invalid["status"] == "failed" and not (ROOT / "invalid target").exists(), invalid
    existing = run("create", ROOT / "existing branch target", branch_name)
    assert existing["status"] == "failed" and not (ROOT / "existing branch target").exists(), existing

    # Tracked, staged, untracked and ignored content all block removal.
    refused("remove", REPO)
    refused("remove", created, cwd=created)
    (created / "file.txt").write_text("changed\n", encoding="utf-8")
    refused("remove", created)
    (created / "file.txt").write_text("base\n", encoding="utf-8")
    (created / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    refused("remove", created)
    remove_known_file(created / "untracked.txt")
    (created / "ignored.bin").write_bytes(b"keep ignored bytes")
    refused("remove", created)
    remove_known_file(created / "ignored.bin")
    git("worktree", "lock", "--reason", "isolated fixture", str(created))
    refused("remove", created)
    git("worktree", "unlock", str(created))
    refused("lock-target", created)
    nested = created / "空 子目录"
    nested.mkdir()
    run("session", cwd=nested)
    refused("lock-nested", created, str(nested))

    # Shared session leases, active state and uncertain cleanup block deletion.
    session = run("session", cwd=created)["session"]
    refused("lock-session", created, session)
    with database() as connection:
        connection.execute("INSERT INTO shared_executions(session_id,owner_instance_id,execution_id,engine,fence,active,started_at,updated_at) VALUES(?, 'fixture','fixture-exec','sengoo',1,1,0,0)", (session,))
    refused("remove", created)
    with database() as connection:
        connection.execute("UPDATE shared_executions SET active=0,cleanup_required=1 WHERE session_id=?", (session,))
    refused("remove", created)
    with database() as connection:
        connection.execute("UPDATE shared_executions SET cleanup_required=0 WHERE session_id=?", (session,))

    # The guard transaction blocks late shared-state writers until removal ends.
    owner = subprocess.Popen([str(EXE), str(DB), str(REPO), "reserve", str(created), ""], cwd=ROOT,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    assert owner.stdout is not None
    assert owner.stdout.readline().strip() == "RESERVED"
    with database(timeout=0) as connection:
        try:
            connection.execute("UPDATE shared_executions SET active=1 WHERE session_id=?", (session,))
        except sqlite3.OperationalError as error:
            assert "locked" in str(error).lower(), error
        else:
            raise AssertionError("late execution writer was not blocked")
    tail, errors = owner.communicate(timeout=15)
    assert owner.returncode == 0, (owner.returncode, tail, errors)
    report = json.loads(tail.splitlines()[-1])
    assert report["status"] == "complete" and not created.exists(), report
    assert run("remove", branch_target)["status"] == "complete" and not branch_target.exists()

    # Inspecting malformed/ambiguous filter names refuses checkout, no execution.
    git("config", "filter.evil=name.smudge", "exit 23")
    weird = ROOT / "ambiguous filter checkout"
    refused("create", weird)
    assert not weird.exists()
    git("config", "--unset-all", "filter.evil=name.smudge")
    for suffix in ("clean", "smudge", "process", "required"):
        git("config", "--unset-all", "filter.evil." + suffix)
    git("config", "--unset-all", "core.hooksPath")
    git("config", "--unset-all", "core.fsmonitor")
    assert not hook_marker.exists() and all(not marker.exists() for marker in markers.values())
    assert git("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout == status_before
    assert (REPO / ".git" / "index").read_bytes() == index_before
    assert (REPO / "file.txt").read_text(encoding="utf-8") == "source unstaged 用户\n"
    assert (REPO / "staged.txt").read_text(encoding="utf-8") == "source staged\n"
    assert (REPO / "untracked.txt").read_text(encoding="utf-8") == "preserve untracked\n"
    print(f"worktrees: {COUNT} real isolated operations passed, UTF-8/spaces, literal exact branch, hook/filter suppression, Plan/approval, locks/session fencing, clean removal and source edit preservation")
finally:
    if os.environ.get("SENCODE_KEEP_WORKTREE_FIXTURE") == "1":
        print("Fixture retained:", ROOT, file=sys.stderr)
    else:
        cleanup()
