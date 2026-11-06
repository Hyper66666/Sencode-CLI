"""Isolated Windows user-terminal jobs; never reads the normal Sencode store."""
from pathlib import Path
import base64
import os
import subprocess
import sys
import tempfile
import time


def run(binary: Path) -> None:
    if os.name != "nt":
        raise SystemExit("Windows ConPTY execution is required; no platform skip is a pass")
    # Keep artifacts on failure. Clean only each known fixture file and empty
    # directories, never recursively remove a path or junction target.
    root = Path(tempfile.mkdtemp(prefix="sencode-pty-jobs-"))
    workspace = root / "workspace-中文😀"
    outside = root / "outside"
    workspace.mkdir()
    outside.mkdir()
    junction = workspace / "escape-junction"
    link_script = "New-Item -ItemType Junction -Path '" + str(junction).replace("'", "''") + "' -Target '" + str(outside).replace("'", "''") + "' -ErrorAction Stop | Out-Null"
    encoded_link = base64.b64encode(link_script.encode("utf-16le")).decode("ascii")
    created = subprocess.run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded_link],
        capture_output=True,
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if created.returncode:
        raise AssertionError(f"junction creation failed: {created.stdout!r} {created.stderr!r}")
    database = root / "isolated.sqlite"
    arguments = [str(binary), str(database), str(workspace), str(junction), str(outside)]
    env = os.environ.copy()
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CODEX_API_KEY", "SENCODE_FIXTURE_PROVIDER_SECRET"]:
        env[key] = "isolated-fixture-sentinel-not-a-real-key"
    before = time.monotonic()
    result = subprocess.run(arguments, env=env, capture_output=True, timeout=60)
    if result.returncode:
        raise AssertionError(f"terminal jobs ({result.returncode}), artifacts {root}:\n{result.stdout!r}\n{result.stderr!r}")
    if result.stderr:
        raise AssertionError(f"terminal output escaped into caller stderr: {result.stderr!r}")
    if not result.stdout.startswith(b"terminal jobs:") or result.stdout.count(b"\n") != 1:
        raise AssertionError(f"unexpected caller stdout: {result.stdout!r}")

    # A deliberately unprovable owner must fail closed across processes and
    # release only when its containing CLI process exits.
    owner = subprocess.Popen(arguments + ["unknown"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        marker = workspace / "unknown-ready"
        deadline = time.monotonic() + 20
        while not marker.exists():
            if owner.poll() is not None:
                out, err = owner.communicate()
                raise AssertionError(f"unknown-cleanup owner exited early {owner.returncode}: {out!r} {err!r}")
            if time.monotonic() >= deadline:
                raise AssertionError("unknown cleanup fixture did not become ready")
            time.sleep(0.025)
        blocked = subprocess.run(arguments + ["probe-lock"], env=env, capture_output=True, timeout=10)
        if blocked.returncode != 23:
            raise AssertionError(f"unproven cleanup released lock: {blocked.returncode} {blocked.stdout!r} {blocked.stderr!r}")
    finally:
        owner.kill()
        owner.communicate(timeout=10)
    released = subprocess.run(arguments + ["probe-lock"], env=env, capture_output=True, timeout=10)
    if released.returncode:
        raise AssertionError(f"OS exit did not release retained lock: {released.stdout!r} {released.stderr!r}")
    print(f"Windows terminal-job fixture passed ({time.monotonic() - before:.2f}s); isolated artifacts: {root}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: pty_session_fixture.py /absolute/path/to/tests_pty_session.exe")
    run(Path(sys.argv[1]).resolve(strict=True))
