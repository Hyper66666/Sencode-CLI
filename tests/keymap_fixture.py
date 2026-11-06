"""Read-only Sengoo keymap loader gate with a fully isolated user profile."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def run(executable: Path, evidence: Path):
    scratch = Path(tempfile.mkdtemp(prefix="sencode-keymap-")).resolve()
    profile = scratch / "profile"
    directory = profile / "Sencode"
    directory.mkdir(parents=True)
    default = directory / "cli-keybindings.json"
    explicit = scratch / "explicit.json"
    files = [default, explicit]
    checks = []
    result = {"schema": 1, "scope": "read-only-user-keymap", "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(), "checks": checks, "result": "running"}
    environment = {name: os.environ[name] for name in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "PROCESSOR_ARCHITECTURE") if name in os.environ}
    environment["APPDATA"] = str(profile)
    environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")

    def load(path=None):
        child_env = dict(environment)
        if path is not None:
            child_env["SENCODE_KEYMAP"] = str(path)
        process = subprocess.run([str(executable)], cwd=scratch, env=child_env, capture_output=True, text=True, encoding="utf-8", timeout=15)
        assert process.returncode == 0, (process.returncode, process.stdout, process.stderr)
        return json.loads(process.stdout.strip())

    def rejected(name, payload):
        explicit.write_bytes(payload)
        before = explicit.read_bytes()
        actual = load(explicit)
        assert actual == {"mode": "default", "source": "built-in defaults", "warning": True, "bindings": 0}, actual
        assert explicit.read_bytes() == before, "Loader modified the user keymap"
        checks.append(name)

    try:
        assert load() == {"mode": "default", "source": "built-in defaults", "warning": False, "bindings": 0}
        checks.append("missing-default-keeps-default-editing")
        default.write_text(json.dumps({"version": 1, "mode": "default", "bindings": [{"key": "alt+b", "action": "word_left"}]}), encoding="utf-8")
        actual = load()
        assert actual["mode"] == "default" and actual["bindings"] == 1 and not actual["warning"] and Path(actual["source"]) == default, actual
        checks.append("documented-user-default-is-read-only")
        explicit.write_text('{"version":1,"mode":"vim","bindings":[]}', encoding="utf-8")
        actual = load(explicit)
        assert actual["mode"] == "vim" and actual["bindings"] == 0 and not actual["warning"] and Path(actual["source"]) == explicit, actual
        checks.append("explicit-selection-precedes-user-default")
        rejected("invalid-utf8-is-rejected", b'{"version":1,"mode":"\xff"}')
        rejected("nul-input-is-rejected", b'{"version":1}\x00')
        rejected("escaped-nul-fields-are-rejected", b'{"version":1,"mode":"vim\\u0000default"}')
        rejected("over-64k-file-is-rejected", b" " * 65537)
        rejected("reserved-chord-rejects-complete-map", b'{"version":1,"bindings":[{"key":"alt+b","action":"word_left"},{"key":"ctrl+c","action":"left"}]}')
        rejected("execution-actions-are-rejected", b'{"version":1,"bindings":[{"key":"alt+b","action":"submit"}]}')
        rejected("duplicate-chords-are-rejected", b'{"version":1,"bindings":[{"key":"alt+b","action":"left"},{"key":"ALT+B","action":"right"}]}')
        rejected("unknown-field-delimiters-are-rejected", b'{"version":1,"version||mode":0}')
        rejected("duplicate-root-members-are-rejected", b'{"version":1,"mode":"default","mode":"vim"}')
        rejected("escaped-duplicate-members-are-rejected", b'{"version":1,"mode":"default","m\\u006fde":"vim"}')
        rejected("duplicate-binding-members-are-rejected", b'{"version":1,"bindings":[{"key":"alt+b","key":"alt+x","action":"left"}]}')
        actual = load(scratch / "missing.json")
        assert actual["warning"] and actual["bindings"] == 0 and actual["mode"] == "default", actual
        checks.append("missing-explicit-path-warns-without-fallback")
        actual = load("")
        assert actual["warning"] and actual["bindings"] == 0 and actual["mode"] == "default", actual
        checks.append("empty-explicit-selection-never-loads-another-map")
        result["result"] = "passed"
        print(f"Read-only keymap files: {len(checks)} checks passed")
    except BaseException as error:
        result["result"] = "failed"
        result["error"] = repr(error)
        raise
    finally:
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        for path in files:
            resolved = path.resolve()
            assert resolved.is_relative_to(scratch), resolved
            if path.exists():
                path.unlink()
        directory.rmdir()
        profile.rmdir()
        scratch.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[1] / "target/keymap-file-evidence.json")
    args = parser.parse_args()
    run(args.executable.resolve(strict=True), args.evidence.resolve())


if __name__ == "__main__":
    main()
