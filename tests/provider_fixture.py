"""Three-protocol byte-fragmentation fixture and native transport test runner."""
import http.server
import json
from pathlib import Path
import subprocess
import sys
import threading
import time


class ProviderFixture(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    errors = []
    active = 0
    maximum_active = 0
    lock = threading.Lock()

    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 1048576:
            self.send_error(413)
            return
        body = json.loads(self.rfile.read(length))
        anthropic = self.path.endswith("/messages")
        expected = self.headers.get("x-api-key") if anthropic else self.headers.get("Authorization")
        if expected != ("fixture-key" if anthropic else "Bearer fixture-key"):
            self.errors.append("authorization header missing")
            self.send_error(401)
            return
        if self.headers.get("Content-Type") != "application/json" or not body.get("stream"):
            self.errors.append("not streaming JSON")
            self.send_error(400)
            return
        with self.lock:
            type(self).active += 1
            type(self).maximum_active = max(self.maximum_active, self.active)
        try:
            events = []
            if self.path.endswith("/chat/completions"):
                events = [
                    {"choices": [{"delta": {"content": "世界😀"}, "finish_reason": None}]},
                    {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "c1", "function": {"name": "read_file", "arguments": "{\"path\":"}}]}, "finish_reason": None}]},
                    {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": "\"test.sg\"}"}}]}, "finish_reason": "tool_calls"}], "usage": {"prompt_tokens": 17, "completion_tokens": 8}},
                    "[DONE]",
                ]
            elif self.path.endswith("/responses"):
                events = [
                    {"type": "response.output_text.delta", "delta": "世界😀"},
                    {"type": "response.output_item.added", "output_index": 1, "item": {"type": "function_call", "call_id": "r1", "name": "read_file", "arguments": ""}},
                    {"type": "response.function_call_arguments.delta", "output_index": 1, "delta": "{\"path\":\"test.sg\"}"},
                    {"type": "response.completed", "response": {"status": "completed", "usage": {"input_tokens": 17, "output_tokens": 8}}},
                ]
            elif anthropic:
                events = [
                    {"type": "message_start", "message": {"usage": {"input_tokens": 17}}},
                    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "世界😀"}},
                    {"type": "content_block_start", "index": 1, "content_block": {"type": "tool_use", "id": "a1", "name": "read_file", "input": {}}},
                    {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": "{\"path\":\"test.sg\"}"}},
                    {"type": "message_delta", "delta": {"stop_reason": "tool_use"}, "usage": {"output_tokens": 8}},
                    {"type": "message_stop"},
                ]
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Connection", "close")
            self.end_headers()
            for index, event in enumerate(events):
                # Mix raw UTF-8 and escaped Unicode, including surrogate pairs.
                data = event if isinstance(event, str) else json.dumps(event, ensure_ascii=index % 2 == 0)
                payload = ("data: " + data + "\r\n\r\n").encode()
                for byte in payload:
                    self.wfile.write(b"1\r\n" + bytes([byte]) + b"\r\n")
                    self.wfile.flush()
                time.sleep(0.025)
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
            self.close_connection = True
        finally:
            with self.lock:
                type(self).active -= 1


def main():
    executable = Path(sys.argv[1]).resolve()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ProviderFixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run([str(executable), f"http://127.0.0.1:{server.server_port}/v1"], timeout=60)
        if result.returncode:
            return result.returncode
        if ProviderFixture.errors or ProviderFixture.maximum_active < 3:
            print("transport fixture failed", ProviderFixture.errors, ProviderFixture.maximum_active)
            return 1
        print("four-way three-protocol HTTP/SSE fixture passed")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
