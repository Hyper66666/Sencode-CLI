"""Actual fragmented provider streams and real file tools for child tasks."""
import collections
import http.server
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time


class Fixture(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    lock = threading.Lock()
    active = 0
    by_connection = collections.Counter()
    maximum = 0
    maximum_connection = 0
    barrier = threading.Event()
    errors = []
    retry_counts = collections.Counter()

    def log_message(self, *args):
        pass

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        model = request["model"]
        connection = self.headers["Authorization"].removeprefix("Bearer fixture-key-")
        if model == "retry-child":
            with self.lock:
                self.retry_counts[model] += 1
                attempt = self.retry_counts[model]
            if attempt <= 2:
                self.send_error(400)
                return
        initial = model.startswith("child-")
        if initial:
            with self.lock:
                type(self).active += 1
                self.by_connection[connection] += 1
                type(self).maximum = max(self.maximum, self.active)
                type(self).maximum_connection = max(self.maximum_connection, self.by_connection[connection])
                if self.active >= 4:
                    self.barrier.set()
        try:
            if initial and model != "child-three" and not self.barrier.wait(5):
                self.errors.append("four accepted children never progressed concurrently")
            if model.startswith("slow-"):
                time.sleep(1)
            tool_messages = [message for message in request["messages"] if message["role"] == "tool"]
            calls = []
            content = "子任务😀"
            if model == "read-file":
                if tool_messages:
                    if "fixture input" not in tool_messages[0]["content"]:
                        self.errors.append("child did not receive actual file output")
                    content = "observed fixture text"
                else:
                    calls = [("read_file", {"path": "fixture-input.txt"})]
            if model == "deny-write":
                if tool_messages:
                    if len(tool_messages) != 3 or any("rejected" not in message["content"] for message in tool_messages):
                        self.errors.append("readonly capability denial missing")
                    content = "denials observed"
                else:
                    calls = [("write_file", {"path": "forbidden.txt", "content": "bad"}), ("spawn_agent", {"prompt": "nested"}), ("write_plan", {"content": "bad"})]
            if model in ("write-one", "write-two") and not tool_messages:
                calls = [("write_file", {"path": model + ".txt", "content": model})]
            if model in ("read-file", "deny-write"):
                names = [tool["function"]["name"] for tool in request.get("tools", [])]
                if any(name in names for name in ("write_file", "apply_patch", "run_command", "spawn_agent", "write_plan")):
                    self.errors.append("readonly child advertised writable tools")
            delta = {"content": content}
            if calls:
                delta["tool_calls"] = [
                    {"index": index, "id": f"{model}-call-{index}", "function": {"name": name, "arguments": json.dumps(arguments)}}
                    for index, (name, arguments) in enumerate(calls)
                ]
            events = [
                {"choices": [{"delta": delta, "finish_reason": None}]},
                {"choices": [{"delta": {}, "finish_reason": "tool_calls" if calls else "stop"}], "usage": {"prompt_tokens": 17, "completion_tokens": 8}},
                "[DONE]",
            ]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Connection", "close")
            self.end_headers()
            for event in events:
                payload = event if isinstance(event, str) else json.dumps(event, ensure_ascii=False)
                raw = ("data: " + payload + "\r\n\r\n").encode()
                for offset in range(0, len(raw), 3):
                    fragment = raw[offset:offset + 3]
                    self.wfile.write(f"{len(fragment):x}\r\n".encode() + fragment + b"\r\n")
                    self.wfile.flush()
                time.sleep(0.01)
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        finally:
            self.close_connection = True
            if initial:
                with self.lock:
                    type(self).active -= 1
                    self.by_connection[connection] -= 1


def main():
    executable = Path(sys.argv[1]).resolve()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="sencode-child-fixture-") as folder:
            Path(folder, "fixture-input.txt").write_text("fixture input 世界😀", encoding="utf-8")
            result = subprocess.run([str(executable), f"http://127.0.0.1:{server.server_port}/v1"], cwd=folder, timeout=60)
            if result.returncode:
                print("Sengoo child fixture exited", result.returncode)
                return result.returncode
            if Fixture.errors or Fixture.maximum != 4 or Fixture.maximum_connection > 2:
                print("child fixture failed", Fixture.errors, Fixture.maximum, Fixture.maximum_connection)
                return 1
            print("real asynchronous child fixture passed")
            return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
