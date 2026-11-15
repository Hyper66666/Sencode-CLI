"""Real local video sampling and helper timeout checks; no interactive state."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import time
import zlib


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("probe", type=Path)
    parser.add_argument("video", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    executable = args.probe.resolve()
    source = args.video.resolve()
    original = digest(source)
    checks = []

    def run(arguments, expected=0, timeout=120):
        result = subprocess.run([str(executable), *map(str, arguments)], capture_output=True, timeout=timeout)
        assert result.returncode == expected, (result.returncode, result.stdout, result.stderr)
        return result

    prepared = json.loads(run([source]).stdout)
    assert len(prepared["paths"]) == 3
    assert "frame 1 at 0 ms" in prepared["text"]
    assert "Only these still frames" in prepared["text"] and "no audio" in prepared["text"]
    assert not Path(prepared["temporary_directory"]).exists()
    assert all(not Path(path).exists() for path in prepared["paths"])
    checks.append("three-real-sampled-frames-with-actual-timestamps-and-cleanup")

    with tempfile.TemporaryDirectory(prefix="sencode-video-helper-") as scratch:
        destination = Path(scratch) / "sample 世界.png"
        document = json.loads(run(["--video-frame", source, "0", destination]).stdout)
        assert document["ok"] and document["value"] == 0
        png = destination.read_bytes()
        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        offset = 8
        kinds = []
        while offset < len(png):
            length = struct.unpack_from(">I", png, offset)[0]
            kind = png[offset + 4:offset + 8]
            chunk = png[offset + 8:offset + 8 + length]
            checksum = struct.unpack_from(">I", png, offset + length + 8)[0]
            assert zlib.crc32(kind + chunk) & 0xffffffff == checksum
            kinds.append(kind)
            offset += length + 12
        assert kinds[0] == b"IHDR" and kinds[-1] == b"IEND" and b"IDAT" in kinds
        existing = digest(destination)
        rejected = json.loads(run(["--video-frame", source, "0", destination], expected=1).stdout)
        assert not rejected["ok"] and digest(destination) == existing
        invalid = Path(scratch) / "invalid.mp4"
        invalid.write_bytes(b"invalid video fixture")
        rejected = json.loads(run(["--video-duration", invalid], expected=1).stdout)
        assert not rejected["ok"]
    checks.append("real-PNG-chunks-and-existing-output-preserved")
    checks.append("malformed-video-rejected")

    started = time.monotonic()
    run(["--test-video-timeout"], timeout=40)
    elapsed = time.monotonic() - started
    assert 30 <= elapsed < 37
    checks.append("thirty-second-helper-timeout-tree-reap-and-process-resource-recovery")
    assert digest(source) == original
    checks.append("original-video-unchanged")
    report = {"schema": 1, "result": "passed", "checks": checks,
              "probe_sha256": digest(executable), "video_sha256": original,
              "helper_timeout_elapsed_seconds": elapsed,
              "scope": "synthetic local video; no audio, live provider or full-motion inference"}
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
