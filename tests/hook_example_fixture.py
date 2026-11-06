"""Exercise the minimal worker SDK example without granting host capabilities."""
import json
from pathlib import Path
import subprocess
import sys


for path, expected in [("notes.txt", "continue"), ("config.protected", "block")]:
    identity = {"schema": 1, "protocol": "sencode.native-worker/1", "id": "example-fixture",
                "worker_id": "protected-paths", "manifest_sha256": "a" * 64}
    initialize = dict(identity, type="initialize")
    event = dict(identity, type="hook", event="before_tool", tool="write_file", input={"path": path})
    result = subprocess.run([str(Path(sys.argv[1]).resolve())],
                            input=json.dumps(initialize) + "\n" + json.dumps(event) + "\n",
                            encoding="utf-8", capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr
    frames = list(map(json.loads, result.stdout.splitlines()))
    assert len(frames) == 2 and frames[0] == dict(identity, type="ready")
    assert frames[1]["decision"] == expected and frames[1]["event"] == "before_tool"
print("minimal Sengoo worker helper/example fixture passed")
