"""Owned PNG -> native request -> loopback capture. No provider or user files."""
import base64
import hashlib
import http.server
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import threading
import zlib


def chunk(kind, data):
    return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))


def png():
    width, height = 768, 384
    rng = random.Random(98217)
    raw = b''.join(b'\0' + rng.randbytes(width * 4) for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def main():
    executable = Path(sys.argv[1]).resolve()
    image = png()
    encoded = base64.b64encode(image).decode('ascii')
    errors, captured = [], []

    class Fixture(http.server.BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *_):
            pass

        def do_POST(self):
            try:
                size = int(self.headers['Content-Length'])
                assert 1048576 < size < 16777216
                body = json.loads(self.rfile.read(size))
                anthropic = self.path.endswith('/messages')
                assert self.headers.get('x-api-key') == 'fixture-key' if anthropic else self.headers.get('Authorization') == 'Bearer fixture-key'
                assert body['stream'] and body['model'] == 'fixture'
                rows = body['input'] if self.path.endswith('/responses') else body['messages']
                parts = rows[0]['content']
                assert len(parts) == 3 and parts[0]['text'] == 'before 世界' and parts[2]['text'] == 'after 😀'
                if anthropic:
                    assert parts[1]['type'] == 'image'
                    source = parts[1]['source']
                    assert source['type'] == 'base64' and source['media_type'] == 'image/png'
                    data = source['data']
                    events = [
                        {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': '已接收😀'}},
                        {'type': 'message_delta', 'delta': {'stop_reason': 'end_turn'}},
                        {'type': 'message_stop'},
                    ]
                elif self.path.endswith('/responses'):
                    assert parts[0]['type'] == 'input_text' and parts[1]['type'] == 'input_image'
                    assert parts[1]['image_url'].startswith('data:image/png;base64,')
                    data = parts[1]['image_url'].split(',', 1)[1]
                    events = [
                        {'type': 'response.output_text.delta', 'delta': '已接收😀'},
                        {'type': 'response.completed', 'response': {'status': 'completed'}},
                    ]
                else:
                    assert self.path.endswith('/chat/completions')
                    assert parts[0]['type'] == 'text' and parts[1]['type'] == 'image_url'
                    assert parts[1]['image_url']['url'].startswith('data:image/png;base64,')
                    data = parts[1]['image_url']['url'].split(',', 1)[1]
                    events = [{'choices': [{'delta': {'content': '已接收😀'}, 'finish_reason': 'stop'}]}, '[DONE]']
                assert data == encoded and base64.b64decode(data, validate=True) == image
                assert 'content_parts' not in json.dumps(body) and 'byte_length' not in json.dumps(body)
                captured.append({'route': self.path, 'bytes': size, 'image_sha256': hashlib.sha256(image).hexdigest()})
                payload = b''.join(('data: ' + (e if isinstance(e, str) else json.dumps(e, ensure_ascii=False)) + '\r\n\r\n').encode() for e in events)
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Content-Length', str(len(payload)))
                self.send_header('Connection', 'close')
                self.end_headers()
                # Deliberately split UTF-8 and SSE delimiters.
                for offset in range(0, len(payload), 7):
                    self.wfile.write(payload[offset:offset + 7])
                    self.wfile.flush()
                self.close_connection = True
            except Exception as error:
                errors.append(repr(error))
                self.send_error(400)

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    directory = Path(tempfile.mkdtemp(prefix='sencode-media-wire-'))
    path = directory / 'history 世界.json'
    try:
        path.write_text(json.dumps({'messages': [{'role': 'user', 'content': '', 'content_parts': [
            {'type': 'text', 'text': 'before 世界'},
            {'type': 'image', 'mime': 'image/png', 'data': encoded, 'byte_length': len(image)},
            {'type': 'text', 'text': 'after 😀'},
        ]}]}), encoding='utf-8')
        result = subprocess.run([str(executable), f'http://127.0.0.1:{server.server_port}/v1', str(path)], timeout=75)
        assert result.returncode == 0, result.returncode
        assert not errors, errors
        assert len(captured) == 3 and len({row['route'] for row in captured}) == 3, captured
        print(json.dumps({'result': 'passed', 'captures': captured, 'preflight_refusals': 9, 'extra_requests': 0}, ensure_ascii=False))
        return 0
    finally:
        server.shutdown()
        server.server_close()
        path.unlink(missing_ok=True)
        directory.rmdir()


if __name__ == '__main__':
    raise SystemExit(main())
