"""Explicit original-file references through the real three-protocol engine."""
import base64
import hashlib
import http.server
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

from media_transport_fixture import png


def main():
    executable = Path(sys.argv[1]).resolve()
    original = png()
    expected = base64.b64encode(original).decode("ascii")
    errors, captures = [], []

    class Fixture(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_):
            pass

        def do_POST(self):
            try:
                size = int(self.headers["Content-Length"])
                assert 1048576 < size < 16777216
                body = json.loads(self.rfile.read(size))
                anthropic = self.path.endswith("/messages")
                assert self.headers.get("x-api-key") == "fixture-key" if anthropic else self.headers.get("Authorization") == "Bearer fixture-key"
                rows = body["input"] if self.path.endswith("/responses") else body["messages"]
                assert len(rows) == 1
                parts = rows[0]["content"]
                assert len(parts) == 2 and parts[0]["text"] == "Inspect original 世界😀"
                if anthropic:
                    assert parts[1]["type"] == "image"
                    assert parts[1]["source"]["media_type"] == "image/png"
                    data = parts[1]["source"]["data"]
                    events = [
                        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "image accepted 世界😀"}},
                        {"type": "message_delta", "delta": {"stop_reason": "end_turn"}},
                        {"type": "message_stop"},
                    ]
                elif self.path.endswith("/responses"):
                    assert parts[1]["type"] == "input_image"
                    data = parts[1]["image_url"].split(",", 1)[1]
                    events = [
                        {"type": "response.output_text.delta", "delta": "image accepted 世界😀"},
                        {"type": "response.completed", "response": {"status": "completed"}},
                    ]
                else:
                    assert self.path.endswith("/chat/completions")
                    assert parts[1]["type"] == "image_url"
                    data = parts[1]["image_url"]["url"].split(",", 1)[1]
                    events = [{"choices": [{"delta": {"content": "image accepted 世界😀"}, "finish_reason": "stop"}]}, "[DONE]"]
                assert data == expected and base64.b64decode(data, validate=True) == original
                encoded = json.dumps(body)
                assert "image_refs" not in encoded and "sha256" not in encoded and "byte_length" not in encoded
                captures.append({"route": self.path, "request_bytes": size, "image_sha256": hashlib.sha256(original).hexdigest()})
                payload = b"".join(("data: " + (event if isinstance(event, str) else json.dumps(event, ensure_ascii=False)) + "\r\n\r\n").encode() for event in events)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Connection", "close")
                self.end_headers()
                for offset in range(0, len(payload), 7):
                    self.wfile.write(payload[offset:offset + 7])
                    self.wfile.flush()
                self.close_connection = True
            except Exception as error:
                errors.append(repr(error))
                self.send_error(400)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    directory = Path(tempfile.mkdtemp(prefix="sencode-image-reference-"))
    image = directory / "original 世界.png"
    try:
        try:
            image.write_bytes(original)
            result = subprocess.run([str(executable), str(image), f"http://127.0.0.1:{server.server_port}/v1"], timeout=75)
            assert result.returncode == 0, result.returncode
            assert image.read_bytes() == original, "source bytes changed"
            assert not errors, errors
            assert len(captures) == 3 and len({item["route"] for item in captures}) == 3, captures
            assert list(directory.iterdir()) == [image], "an image copy was written"
        finally:
            if image.is_file():
                image.unlink()
            if not any(directory.iterdir()):
                directory.rmdir()
        print(json.dumps({"result": "passed", "captures": captures, "extra_requests": 0, "source_mutations": 0}, ensure_ascii=False))
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
