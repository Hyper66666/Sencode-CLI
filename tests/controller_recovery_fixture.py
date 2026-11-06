"""Dedicated real-controller probe; isolated DB/files and no API credentials."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


def clean(directory):
    root = directory.resolve(strict=True)
    entries = list(directory.rglob("*"))
    assert all(entry.parent.resolve().is_relative_to(root) for entry in entries)
    assert all(entry.is_symlink() or entry.resolve().is_relative_to(root) for entry in entries)
    for entry in sorted(entries, key=lambda value: len(value.parts), reverse=True):
        if entry.is_symlink():
            entry.unlink()
        elif entry.is_file():
            entry.chmod(entry.stat().st_mode | stat.S_IWUSR)
            entry.unlink()
        else:
            entry.rmdir()
    directory.rmdir()


def main():
    executable = Path(sys.argv[1]).resolve(strict=True)
    cases = []
    for case in ("ordinary-git", "missing-git"):
        directory = Path(tempfile.mkdtemp(prefix="sencode-recoverable-tools-"))
        try:
            (directory / "invalid.bin").write_bytes(b"\xff\xfeinvalid text")
            environment = dict(os.environ)
            if case == "missing-git":
                # The Git resolver admits only absolute PATH entries; removing
                # all of them exercises real job-start rejection without a process.
                environment["PATH"] = ""
            result = subprocess.run(
                [str(executable), "--database", str(directory / "state.sqlite3")],
                cwd=directory, env=environment, capture_output=True,
                encoding="utf-8", timeout=60,
            )
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            assert result.returncode == 0, (case, result.returncode)
            assert not (directory / "must-not-replay.txt").exists()
            assert (directory / "unchanged.txt").read_text(encoding="utf-8") == "original 世界"
            cases.append({"case": case, "exit_code": result.returncode})
        finally:
            clean(directory)
    print(json.dumps({
        "result": "passed", "cases": cases,
        "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "provider_calls": 0, "real_credentials": 0,
    }))


if __name__ == "__main__":
    main()
