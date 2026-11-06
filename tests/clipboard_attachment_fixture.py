"""Original-path parsing only; never accesses the interactive clipboard."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import zlib


def png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\x33\x66\x99\xff")) + chunk(b"IEND", b""))


def main():
    args = argparse.ArgumentParser()
    args.add_argument("probe", type=Path)
    args.add_argument("--evidence", type=Path, required=True)
    options = args.parse_args()
    scratch = Path(tempfile.mkdtemp(prefix="sencode-image-path-中文-"))
    first = scratch / "original screenshot 中文.png"
    second = scratch / "second image.png"
    bad = scratch / "not an image.png"
    checks = []
    try:
        first.write_bytes(png())
        second.write_bytes(png())
        bad.write_text("not a PNG", encoding="utf-8")
        original = hashlib.sha256(first.read_bytes()).hexdigest()

        def parse(value):
            run = subprocess.run([str(options.probe.resolve()), "--cwd", str(scratch), "--prompt", value],
                                 capture_output=True, timeout=20)
            assert run.returncode == 0, run.stdout + run.stderr
            return json.loads(run.stdout.decode("utf-8-sig"))

        for value in [f'"{first}"', str(first), f'"{first.name}"']:
            result = parse(value)
            assert result["matched"] and len(result["paths"]) == 1, result
            assert os.path.samefile(result["paths"][0], first), result
            assert result["text"] == "", result
            assert result["temporary_path"] == "", result
        checks.append("quoted-unquoted-relative-and-Unicode-original-paths")
        for value in [f'"{first}" "{second}"', f"{first}\n{second}", f"'{first}'\r\n'{second}'"]:
            result = parse(value)
            assert result["matched"] and len(result["paths"]) == 2, result
            assert os.path.samefile(result["paths"][0], first), result
            assert os.path.samefile(result["paths"][1], second), result
        checks.append("multiple-quoted-and-newline-paths")
        for value in [f"please inspect {first}", f'"{first}" trailing prose', f'"{first}',
                      str(bad), str(scratch / "missing.png"), " ".join([f'"{first}"'] * 9)]:
            result = parse(value)
            assert not result["matched"] and not result["paths"] and result["text"] == value, result
        checks.append("invalid-missing-prose-and-over-limit-keep-original-text")
        assert hashlib.sha256(first.read_bytes()).hexdigest() == original
        assert not (scratch / ".sencode").exists()
        assert set(scratch.iterdir()) == {first, second, bad}
        checks.append("source-images-unchanged-and-no-project-copy")
        evidence = {"schema": 1, "result": "passed", "checks": checks,
                    "clipboard_access": "none; path parser only",
                    "probe_sha256": hashlib.sha256(options.probe.read_bytes()).hexdigest()}
        options.evidence.parent.mkdir(parents=True, exist_ok=True)
        options.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(evidence, ensure_ascii=False))
    finally:
        for item in [first, second, bad]:
            if item.exists():
                item.unlink()
        scratch.rmdir()


if __name__ == "__main__":
    main()
