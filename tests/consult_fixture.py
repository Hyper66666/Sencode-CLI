"""Real loopback HTTP streams for the Sengoo consultation coordinator."""
import collections
import http.server
import json
from pathlib import Path
import subprocess
import sys
import threading
import time


class Fixture(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    lock = threading.Lock()
    active = 0
    by_connection = collections.Counter()
    maximum = 0
    maximum_connection = 0
    initial_active = 0
    initial_connections = collections.Counter()
    initial_maximum = 0
    initial_connection_maximum = 0
    errors = []
    retry_counts = collections.Counter()
    barrier = threading.Event()

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        key = self.headers.get("x-api-key", self.headers.get("Authorization", ""))
        identity = key.removeprefix("Bearer ").removeprefix("fixture-key-")
        model = body.get("model", "")
        initial = model in ("chat-one", "chat-two", "chat-three", "responses-one", "messages-one")
        if identity not in ("a", "b", "c") or body.get("tools") not in (None, []):
            self.errors.append("bad credentials or nonempty tool list")
        with self.lock:
            type(self).active += 1
            self.by_connection[identity] += 1
            type(self).maximum = max(self.maximum, self.active)
            type(self).maximum_connection = max(self.maximum_connection, self.by_connection[identity])
            if initial:
                type(self).initial_active += 1
                self.initial_connections[identity] += 1
                type(self).initial_maximum = max(self.initial_maximum, self.initial_active)
                type(self).initial_connection_maximum = max(self.initial_connection_maximum, self.initial_connections[identity])
            if self.active >= 4:
                self.barrier.set()
        try:
            if model == "retry-consult":
                with self.lock:
                    self.retry_counts[model] += 1
                    attempt = self.retry_counts[model]
                if attempt <= 2:
                    self.send_error(403)
                    return
            if model == "failure":
                self.send_error(500)
                return
            # The first batch must have four real streams open before any
            # response completes, proving that the app coordinator is parallel.
            if model in ("chat-one", "chat-two", "responses-one", "messages-one"):
                if not self.barrier.wait(5):
                    self.errors.append("initial streams did not progress concurrently")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Connection", "close")
            self.end_headers()
            if model.startswith("slow-"):
                time.sleep(1)
            if self.path.endswith("/chat/completions"):
                finish = {"delta": {}, "finish_reason": "stop"}
                if model == "tools":
                    finish = {"delta": {"tool_calls": [{"index": 0, "id": "forbidden", "function": {"name": "write_file", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}
                events = [
                    {"choices": [{"delta": {"content": "世界😀"}, "finish_reason": None}]},
                    {"choices": [finish], "usage": {"prompt_tokens": 17, "completion_tokens": 8}},
                    "[DONE]",
                ]
            elif self.path.endswith("/responses"):
                events = [
                    {"type": "response.output_text.delta", "delta": "世界😀"},
                    {"type": "response.completed", "response": {"status": "completed", "usage": {"input_tokens": 17, "output_tokens": 8}}},
                ]
            else:
                events = [
                    {"type": "message_start", "message": {"usage": {"input_tokens": 17}}},
                    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "世界😀"}},
                    {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 8}},
                    {"type": "message_stop"},
                ]
            for index, event in enumerate(events):
                data = event if isinstance(event, str) else json.dumps(event, ensure_ascii=False)
                raw = ("data: " + data + "\r\n\r\n").encode()
                # Deliberately split UTF-8, JSON escapes and SSE delimiters.
                for offset in range(0, len(raw), 3):
                    fragment = raw[offset:offset + 3]
                    self.wfile.write(f"{len(fragment):x}\r\n".encode() + fragment + b"\r\n")
                    self.wfile.flush()
                time.sleep(0.02)
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # explicit application cancellation is an expected scenario
        finally:
            self.close_connection = True
            with self.lock:
                type(self).active -= 1
                self.by_connection[identity] -= 1
                if initial:
                    type(self).initial_active -= 1
                    self.initial_connections[identity] -= 1


def main():
    executable = Path(sys.argv[1]).resolve()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run([str(executable), f"http://127.0.0.1:{server.server_port}/v1"], timeout=60)
        if result.returncode:
            print("Sengoo consultation exited", result.returncode)
            return result.returncode
        # Later canceled server handlers may briefly remain after their client
        # sockets are gone; the initial five-request batch proves the limits.
        if Fixture.errors or Fixture.initial_maximum != 4 or Fixture.initial_connection_maximum > 2:
            print("consult fixture failed", Fixture.errors, Fixture.initial_maximum, Fixture.initial_connection_maximum)
            return 1
        print("real three-protocol consultation fixture passed")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
