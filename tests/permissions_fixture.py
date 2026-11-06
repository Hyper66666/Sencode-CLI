"""Run the native permission contract in a synthetic owned project only."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


def clean_owned(directory):
    root = directory.resolve(strict=True)
    entries = list(root.rglob("*"))
    assert all(item.parent.resolve().is_relative_to(root) for item in entries)
    for item in sorted(entries, key=lambda value: len(value.parts), reverse=True):
        if item.is_symlink():
            item.unlink()
        elif item.is_file():
            assert item.resolve().is_relative_to(root)
            item.chmod(item.stat().st_mode | stat.S_IWUSR)
            item.unlink()
        else:
            item.rmdir()
    root.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    scratch = Path(tempfile.mkdtemp(prefix="sencode-permissions-")).resolve()
    evidence = {"schema": 1, "scope": "Native permission contract; owned files, shell and stdio MCP; no API, credential, clipboard or user state", "result": "running", "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(), "fixture_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        project = scratch / "workspace-中文"
        project.mkdir()
        (project / ".sencode").mkdir()
        (project / ".sencode" / "mcp.json").write_text(json.dumps({"servers": [{"name": "permission-fixture", "command": sys.executable, "args": [str(Path(__file__).with_name("mcp_fixture.py").resolve())]}]}), encoding="utf-8")
        environment = dict(os.environ)
        environment.update({"USERPROFILE": str(scratch / "profile"), "APPDATA": str(scratch / "roaming"), "LOCALAPPDATA": str(scratch / "local")})
        for key in ("USERPROFILE", "APPDATA", "LOCALAPPDATA"):
            Path(environment[key]).mkdir()
        result = subprocess.run([str(executable), "--cwd", str(project)], cwd=project, env=environment, capture_output=True, encoding="utf-8", errors="replace", timeout=75)
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        evidence.update({"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        assert result.returncode == 0
        assert (project / "permission-owned.txt").read_text(encoding="utf-8") == "auto edit 中文"
        assert (project / "full-command-owned.txt").read_text(encoding="utf-8") == "full shell"
        evidence["result"] = "passed"
    finally:
        clean_owned(scratch)
        evidence["owned_temporary_data_removed"] = True
        if args.evidence:
            args.evidence.parent.mkdir(parents=True, exist_ok=True)
            args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
