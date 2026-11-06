"""Native state/context regression using only disposable SQLite stores."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading


class SummaryFixture(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *_):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        assert 0 < length <= 786432
        request = json.loads(self.rfile.read(length))
        assert self.path == "/v1/chat/completions"
        assert request["model"] == "history-fixture"
        assert request["stream"] is True
        assert len(request["messages"]) == 2
        assert "PUBLIC_HISTORY_JSON:" in request["messages"][1]["content"]
        self.requests.append(request)
        summary = ("Continuation evidence: preserve the user goal and exact cumulative budgets. "
                   "The public SQLite transcript remains complete. No workspace files were changed. "
                   "The next step is to continue from the retained recent messages and verify the task. " * 4)
        chunks = [
            {"choices": [{"index": 0, "delta": {"content": summary}, "finish_reason": None}]},
            {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
             "usage": {"prompt_tokens": 70, "completion_tokens": 31}},
        ]
        body = "".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks) + "data: [DONE]\n\n"
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def clean(directory):
    root = directory.resolve(strict=True)
    entries = list(directory.rglob("*"))
    assert all(entry.parent.resolve().is_relative_to(root) for entry in entries)
    assert all(entry.is_symlink() or entry.resolve().is_relative_to(root) for entry in entries)
    for entry in sorted(entries, key=lambda item: len(item.parts), reverse=True):
        if entry.is_symlink():
            entry.unlink()
        elif entry.is_file():
            entry.chmod(entry.stat().st_mode | stat.S_IWUSR)
            entry.unlink()
        else:
            entry.rmdir()
    directory.rmdir()


def main():
    baseline = "--baseline" in sys.argv[1:]
    executables = [Path(item).resolve(strict=True) for item in sys.argv[1:] if item != "--baseline"]
    results = []
    for executable in executables:
        directory = Path(tempfile.mkdtemp(prefix="sencode-long-history-"))
        server = ThreadingHTTPServer(("127.0.0.1", 0), SummaryFixture)
        SummaryFixture.requests = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = subprocess.run(
                [str(executable), "--database", str(directory / "history.sqlite3"),
                 "--base-url", f"http://127.0.0.1:{server.server_port}/v1"],
                cwd=directory, capture_output=True, encoding="utf-8", timeout=180,
            )
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            if baseline:
                assert result.returncode == 1, result.returncode
                assert "REPRODUCED:" in result.stderr
            else:
                assert result.returncode == 0, result.returncode
                assert len(SummaryFixture.requests) == (1 if "context" in executable.name else 0)
            results.append({
                "binary": executable.name, "exit_code": result.returncode,
                "sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                "loopback_summary_requests": len(SummaryFixture.requests),
            })
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            clean(directory)
    print(json.dumps({"result": "reproduced" if baseline else "passed", "cases": results,
                      "provider_calls": 0, "real_credentials": 0}))


if __name__ == "__main__":
    main()
