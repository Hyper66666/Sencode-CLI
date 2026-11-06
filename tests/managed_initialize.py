"""Initialize the pinned official public server without account/model use."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from engine_fixture import clean_generated_directory


def main():
    probe, runtime = (Path(value).resolve() for value in sys.argv[1:3])
    root = Path(tempfile.mkdtemp(prefix="sencode-public-initialize-中文😀-")).resolve()
    profile = root / "empty-profile"
    profile.mkdir()
    assert not any(profile.iterdir())
    environment = dict(os.environ, HTTP_PROXY="http://127.0.0.1:9",
                       HTTPS_PROXY="http://127.0.0.1:9", ALL_PROXY="http://127.0.0.1:9", NO_PROXY="")
    succeeded = False
    try:
        result = subprocess.run([str(probe), str(runtime), str(profile)],
                                cwd=root, env=environment, capture_output=True, text=True,
                                encoding="utf-8", timeout=30)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        report = json.loads(result.stdout)
        assert report == {"engine": "codex-app-server", "runtime_version": "0.144.4",
                          "protocol_version": "0.144.4", "profile_verified": True,
                          "initialized": True, "thread_created": False, "model_requested": False}
        report["runtime_sha256"] = hashlib.sha256(runtime.read_bytes()).hexdigest()
        report["empty_profile_at_start"] = True
        print(json.dumps(report, ensure_ascii=False))
        succeeded = True
    finally:
        if succeeded:
            clean_generated_directory(root)
        else:
            print(f"failed initialize probe retained for inspection: {root}", file=sys.stderr)


if __name__ == "__main__":
    main()
