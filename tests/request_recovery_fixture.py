"""Native retry/automatic-compaction integration using real pipes and SQLite."""
from contextlib import closing
import ctypes
import email.utils
import http.server
import json
from pathlib import Path
import socket
import socketserver
import sqlite3
import sys
import tempfile
import threading
import time
import uuid

from cli_fixture import Credential
from engine_fixture import Host, clean_generated_directory


SUMMARY_PRIVATE_MARKER = "SYNTHETIC-CONTINUATION-STATE"
SUMMARY_DRAFT_MARKER = "PRIVATE-DRAFT-MUST-NOT-LEAK"
SUMMARY_TEXT = (
    "1. User goal and scope: preserve the synthetic coding task and its explicit workspace constraints.\n"
    "2. Decisions: keep the original system instructions and exact recent tool results.\n"
    "3. Files and interfaces: this isolated fixture exercises context.json, shared_modes and finish_goal.\n"
    "4. Evidence: prior checks returned exit zero; only provider-reported usage is counted as reported.\n"
    "5. Open issues: retain uncertain side effects and do not replay tools after reconnect.\n"
    "6. Pending work: continue the next history request using the same cumulative Goal budget.\n"
    "7. Attribution: fixture-model on this loopback connection produced this continuation state. "
    + SUMMARY_PRIVATE_MARKER
)


class RecoveryProvider(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    lock = threading.Lock()
    requests = []
    errors = []
    counts = {}
    summary_fail = False
    summary_short = False

    def log_message(self, *_):
        pass

    def do_POST(self):
        try:
            assert self.headers.get("Authorization") == "Bearer fixture-key"
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = request["messages"]
            prompt = next(value["content"] for value in reversed(messages) if value["role"] == "user")
            summary = messages[0]["content"].startswith("You summarize coding sessions")
            if summary:
                assert "PUBLIC_HISTORY_JSON:" in prompt, "summary request lost quoted public context"
                assert "Preserve still-relevant facts" in prompt, "summary request lost Sencode continuation policy"
                assert not request.get("tools"), "internal summary unexpectedly received tools"
            key = "summary" if summary else prompt[:80]
            with self.lock:
                self.requests.append(request)
                self.counts[key] = self.counts.get(key, 0) + 1
                attempt = self.counts[key]
            status, retry = 200, None
            if summary and self.summary_fail:
                status = 400
            elif prompt == "retry rate" and attempt == 1:
                status, retry = 429, "1"
            elif prompt == "retry server" and attempt <= 2:
                status = 503
            elif prompt == "retry date" and attempt == 1:
                status, retry = 429, email.utils.formatdate(time.time() + 2, usegmt=True)
            elif prompt in ("retry exhausted", "retry budget"):
                status = 502
            elif prompt == "retry too late":
                status, retry = 429, "0"
            elif prompt == "retry cancel":
                status, retry = 429, "20"
            elif prompt == "validation error":
                status = 400
            if prompt == "disconnect after send":
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            if status != 200:
                self.send_response(status)
                if retry:
                    self.send_header("Retry-After", retry)
                self.send_header("Content-Length", "0")
                self.send_header("Connection", "close")
                self.end_headers()
                return
            if summary:
                text = "too short" if self.summary_short else (
                    "<analysis>" + SUMMARY_DRAFT_MARKER + "</analysis>\n<summary>" + SUMMARY_TEXT + "</summary>"
                )
            else:
                text = "reply 中文😀 " + prompt[:30]
            events = [dict(choices=[dict(delta=dict(content=text), finish_reason=None)])]
            if prompt == "tool then retry":
                tool_results = [m for m in messages if m["role"] == "tool"]
                if not tool_results:
                    events = [dict(choices=[dict(delta=dict(tool_calls=[dict(index=0, id="retry-once-tool", function=dict(
                        name="run_command", arguments=json.dumps({"command":"printf 'once\\n' >> retry-side-effect.txt"})))]), finish_reason="tool_calls")])]
                elif attempt == 2:
                    self.send_error(400)
                    return
            if not summary and (prompt.startswith("history-") or prompt == "continue compacted context"):
                events = [dict(choices=[dict(delta=dict(tool_calls=[dict(index=0, id=f"finish-{len(self.requests)}",
                                         function=dict(name="finish_goal", arguments=json.dumps({"summary": "Run the supplied check"})))]), finish_reason="tool_calls")])]
            if prompt == "disconnect during stream" or prompt == "partial then recover" and attempt <= 2:
                frames = [("data: " + json.dumps(events[0], ensure_ascii=False) + "\n\n").encode()]
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(frames[0]) + 100))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(frames[0])
                self.wfile.flush()
                self.connection.shutdown(socket.SHUT_RDWR)
                return
            if prompt == "malformed event":
                frames = [b'data: {invalid json}\n\n']
            elif prompt == "missing terminal":
                frames = [("data: " + json.dumps(events[0]) + "\n\n").encode()]
            elif prompt == "partial SSE":
                frames = [b'data: {"choices":']
            elif prompt == "stream error":
                frames = [b'data: {"error":{"code":"rate_limit_exceeded","message":"SECRET-DO-NOT-LOG"}}\n\n']
            else:
                frames = None
            if frames is not None:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(sum(map(len, frames))))
                self.send_header("Connection", "close")
                self.end_headers()
                for frame in frames: self.wfile.write(frame)
                return
            events.append(dict(choices=[dict(delta={}, finish_reason="stop")], usage=dict(prompt_tokens=17, completion_tokens=9)))
            encoded = [("data: " + json.dumps(value, ensure_ascii=False) + "\n\n").encode() for value in events]
            encoded.append(b"data: [DONE]\n\n")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(sum(map(len, encoded))))
            self.send_header("Connection", "close")
            self.end_headers()
            for frame in encoded:
                for offset in range(0, len(frame), 7):
                    self.wfile.write(frame[offset:offset + 7])
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as error:
            self.errors.append(repr(error))
            raise
        finally:
            self.close_connection = True


class TlsAbort(socketserver.BaseRequestHandler):
    hellos = []
    def handle(self):
        self.request.settimeout(3)
        hello = self.request.recv(4096)
        type(self).hellos.append(hello)
        # Abort TLS before an application HTTP request can be emitted.
        assert hello and hello[0] == 22, hello[:20]


def modes(database, session):
    with closing(sqlite3.connect(database)) as db:
        row = db.execute("SELECT mode_json FROM shared_modes WHERE session_id=?", (session,)).fetchone()
        return json.loads(row[0]) if row else {}


def main():
    executable = Path(sys.argv[1]).resolve()
    project = Path(tempfile.mkdtemp(prefix="sencode-recovery-中文😀-")).resolve()
    database = project / "fixture.sqlite"
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RecoveryProvider)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    identifier = "custom-recovery-" + uuid.uuid4().hex
    target = "Sencode/connection/" + identifier
    key = (ctypes.c_ubyte * len(b"fixture-key")).from_buffer_copy(b"fixture-key")
    credential = Credential(Type=1, TargetName=target, CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    assert advapi.CredWriteW(ctypes.byref(credential), 0), ctypes.WinError(ctypes.get_last_error())
    hosts = []
    succeeded = False
    try:
        bootstrap = Host(executable, project, database, "")
        hosts.append(bootstrap)
        bootstrap.stop()
        config = dict(version=2, baseUrl=f"http://127.0.0.1:{server.server_port}/v1", protocol="chatCompletions",
                      credentialRef=target, selectedModelId="fixture-model", enabledModels=[])
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "test-fixture" if key == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','fixture',?,'fixture-model',1,1)",
                       (identifier, json.dumps(config)))
            db.commit()
        host = Host(executable, project, database, identifier)
        hosts.append(host)
        started = time.monotonic()
        start = host.submit("rate", "retry rate")
        host.result("rate", start)
        assert time.monotonic() - started >= 1, "Retry-After was ignored"
        assert RecoveryProvider.counts["retry rate"] == 2
        records = modes(database, host.session)["request_attempts"]["attempts"]
        assert len(records) == 2 and len({value["id"] for value in records}) == 2
        assert records[0]["status"] == "failed" and records[0]["usage_source"] == "unavailable"
        assert records[1]["status"] == "accepted" and records[1]["usage_source"] == "provider-reported"
        start = host.submit("server", "retry server")
        host.result("server", start)
        assert RecoveryProvider.counts["retry server"] == 3
        began = time.monotonic()
        start = host.submit("date", "retry date")
        host.result("date", start)
        assert time.monotonic() - began >= .75 and RecoveryProvider.counts["retry date"] == 2
        start = host.submit("exhausted", "retry exhausted")
        failure = host.result("exhausted", start, 502)
        diagnostic = failure["diagnostic"]
        assert diagnostic["http_status"] == 502 and diagnostic["retries"] == 5
        assert "HTTP 502 Bad Gateway" in failure["content"]
        assert len([e for e in host.events[start:] if e.get("type") == "retry"]) == 5
        assert not any(e.get("type") == "notice" and "request retry" in e.get("text", "") for e in host.events[start:])
        assert RecoveryProvider.counts["retry exhausted"] == 6
        for identifier_, text, code in (("late", "retry too late", 429), ("invalid", "validation error", 400),
                                        ("ambiguous", "disconnect after send", 10), ("partial", "disconnect during stream", 10)):
            start = host.submit(identifier_, text)
            failed = host.result(identifier_, start, code)
            assert RecoveryProvider.counts[text] == 6 and failed["diagnostic"]["retries"] == 5, "model request did not receive five retries"
            if text == "disconnect during stream":
                assert "HTTP response body ended before completion" in failed["content"], failed
                assert failed["diagnostic"]["response_stage"] == "http_finish"
                assert failed["content"].startswith("Invalid or incomplete provider response (HTTP 200 received)"), failed
        for prompt, code, label, stage in (("malformed event", 10, "Invalid provider event", "provider_event"),
                         ("missing terminal", 10, "without a provider completion event", "provider_terminal"),
                         ("partial SSE", 10, "SSE event ended before completion", "sse_finish"),
                         ("stream error", 9, "Provider rate limit reported inside the stream", "provider_event")):
            start = host.submit(prompt, prompt)
            failed = host.result(prompt, start, code)
            assert RecoveryProvider.counts[prompt] == 6 and failed["diagnostic"]["retries"] == 5
            assert label in failed["content"] and failed["diagnostic"]["response_stage"] == stage, failed
            assert "SECRET-DO-NOT-LOG" not in json.dumps(failed), failed
        start = host.submit("recover-partial", "partial then recover")
        host.result("recover-partial", start)
        assert RecoveryProvider.counts["partial then recover"] == 3
        retry_events = [e for e in host.events[start:] if e.get("type") == "retry"]
        assert len(retry_events) == 2 and all(json.loads(e["text"])["replace_partial"] for e in retry_events)
        with closing(sqlite3.connect(database)) as db:
            rows = list(db.execute("SELECT text,cancelled FROM messages WHERE session_id=? AND role='assistant' AND text LIKE '%reply 中文😀 partial then recover%'", (host.session,)))
            assert len(rows) == 1 and rows[0][1] == 0, rows
        start = host.submit("tool-once", "tool then retry", allow_commands=True)
        host.result("tool-once", start)
        assert (project / "retry-side-effect.txt").read_text() == "once\n", "retry reran a completed tool"
        assert RecoveryProvider.counts["tool then retry"] == 3
        records = modes(database, host.session)["request_attempts"]["attempts"]
        assert any(value.get("http_status") == 200 and value.get("response_stage") == "http_finish" for value in records)
        start = host.submit("cancel", "retry cancel")
        host.wait("retry", "cancel", start)
        began = time.monotonic()
        host.send({"type": "cancel", "id": "cancel"})
        host.result("cancel", start, 19)
        assert time.monotonic() - began < 2 and RecoveryProvider.counts["retry cancel"] == 1
        start = host.submit("budget", "retry budget", goal="retry budget", maximum_requests=2)
        host.result("budget", start, 13)
        assert RecoveryProvider.counts["retry budget"] == 2
        saved_goal = modes(database, host.session)["goal"]
        assert saved_goal["requests"] == 2 and saved_goal["status"] == 3
        host.stop()

        unbound = socket.socket()
        unbound.bind(("127.0.0.1", 0))
        refused_port = unbound.getsockname()[1]
        config["baseUrl"] = f"http://127.0.0.1:{refused_port}/v1"
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "test-fixture" if key == "instance_id" else None)
            db.execute("UPDATE connection_configs SET config_json=? WHERE id=?", (json.dumps(config), identifier))
            db.commit()
        refused = Host(executable, project, database, identifier)
        hosts.append(refused)
        start = refused.submit("connect-refused", "connection refused", goal="connection failure", maximum_requests=8)
        refused_result = refused.wait("result", "connect-refused", start, timeout=230)
        assert refused_result["code"] in (9, 11), refused_result
        connection_modes = modes(database, refused.session)
        assert connection_modes["goal"]["requests"] == 6
        assert len(connection_modes["request_attempts"]["attempts"]) == 6
        assert all(value["usage_source"] == "unavailable" for value in connection_modes["request_attempts"]["attempts"])
        refused.stop()
        unbound.close()
        with socketserver.ThreadingTCPServer(("127.0.0.1", 0), TlsAbort) as tls_server:
            threading.Thread(target=tls_server.serve_forever, daemon=True).start()
            config["baseUrl"] = f"https://127.0.0.1:{tls_server.server_address[1]}/v1"
            with closing(sqlite3.connect(database)) as db:
                db.create_function("sengoo_context", 1, lambda key: "test-fixture" if key == "instance_id" else None)
                db.execute("UPDATE connection_configs SET config_json=? WHERE id=?", (json.dumps(config), identifier))
                db.commit()
            tls_host = Host(executable, project, database, identifier)
            hosts.append(tls_host)
            start = tls_host.submit("tls-abort", "TLS pre-send failure")
            failed = tls_host.wait("result", "tls-abort", start, timeout=230)
            assert failed["code"] == 17 and failed["diagnostic"]["retries"] == 5, failed
            assert "TLS handshake failed" in failed["content"]
            assert len(TlsAbort.hellos) == 6 and all(value[0] == 22 for value in TlsAbort.hellos)
            tls_host.stop()
            tls_server.shutdown()
        config["baseUrl"] = f"http://127.0.0.1:{server.server_port}/v1"
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "test-fixture" if key == "instance_id" else None)
            db.execute("UPDATE connection_configs SET config_json=? WHERE id=?", (json.dumps(config), identifier))
            db.commit()

        # A separate session avoids inheriting the intentionally partial stream.
        compact = Host(executable, project, database, identifier)
        hosts.append(compact)
        compact_request_start = len(RecoveryProvider.requests)
        settings = project / ".sencode" / "context.json"
        settings.parent.mkdir(exist_ok=True)
        settings.write_text(json.dumps({"schema": 1, "models": [{"connection": identifier, "model": "fixture-model",
                            "context_window_tokens": 9000, "threshold_percent": 80, "max_input_bytes": 24000}]}), encoding="utf-8")
        for index in range(16):
            text = f"history-{index} " + ("verified 中文😀 evidence; " * 100)
            start = compact.submit(f"history-{index}", text, goal="context work", maximum_requests=0, allow_commands=True, checks=["exit 0"])
            compact.result(f"history-{index}", start)
        assert RecoveryProvider.counts.get("summary", 0) >= 2, "repeated automatic compaction was not exercised"
        checkpoint = modes(database, compact.session)["context"]
        assert checkpoint["schema"] == 2 and checkpoint["messages"]
        assert SUMMARY_PRIVATE_MARKER in checkpoint["summary"]
        assert SUMMARY_DRAFT_MARKER not in json.dumps(checkpoint), "drafting escaped summary cleaning"
        assert "<summary>" not in checkpoint["summary"]
        assert any(value.get("context_summary") for value in checkpoint["messages"]), "summary carrier lost its identity"
        cumulative = modes(database, compact.session)["goal"]["requests"]
        assert modes(database, compact.session)["goal"]["max_requests"] == 0, "compaction does not introduce a request cap"
        assert cumulative == len(RecoveryProvider.requests) - compact_request_start, "summary requests did not share the cumulative Goal budget"
        assert any(event.get("type") == "context_compacted" and event.get("text") == "上下文已压缩" for event in compact.events)
        assert not any(event.get("type") == "notice" and "compacted;" in event.get("text", "") for event in compact.events)
        assert any(event.get("type") == "phase" and event.get("text") == "compacting" for event in compact.events)
        reducing = False
        for event in compact.events:
            if event.get("type") == "phase" and event.get("text") == "compacting":
                reducing = True
            elif event.get("type") == "context_compacted":
                assert reducing and event.get("text") == "上下文已压缩"
                reducing = False
            elif event.get("type") == "phase" and reducing:
                assert event.get("text") == "compacting", "summary activity was overwritten by Working/Thinking"
        assert not reducing, "successful compaction never reported its checkpoint"
        assert not any(SUMMARY_PRIVATE_MARKER in event.get("text", "") or SUMMARY_DRAFT_MARKER in event.get("text", "")
                       for event in compact.events if event.get("type") == "text_delta"), "internal summary appeared as public streamed output"
        with closing(sqlite3.connect(database)) as db:
            texts = "\n".join(value[0] for value in db.execute("SELECT text FROM messages WHERE session_id=?", (compact.session,)))
            assert all(f"history-{index}" in texts for index in range(16)), "original public history was deleted"
            assert SUMMARY_PRIVATE_MARKER not in texts and SUMMARY_DRAFT_MARKER not in texts, "internal summary entered the public assistant transcript"
        session = compact.session
        compact.stop()
        resumed = Host(executable, project, database, identifier, session)
        hosts.append(resumed)
        start = resumed.submit("after-compact-restart", "continue compacted context", goal="context work", maximum_requests=0, allow_commands=True, checks=["exit 0"])
        resumed.result("after-compact-restart", start)
        assert modes(database, session)["goal"]["requests"] > cumulative
        assert any("Continuation summary" in value.get("content", "") for value in RecoveryProvider.requests[-1]["messages"])
        assert any(value.get("role") == "tool" and value.get("tool_call_id", "").startswith("finish-") for value in RecoveryProvider.requests[-1]["messages"]), "recent tool results disappeared from the active context"
        # A failed summary never replaces the last complete checkpoint.
        RecoveryProvider.summary_fail = True
        failed = False
        for index in range(16, 24):
            before = modes(database, session).get("context")
            text = f"history-{index} " + ("verified 中文😀 evidence; " * 100)
            start = resumed.submit(f"failure-{index}", text, goal="context work", maximum_requests=0, allow_commands=True, checks=["exit 0"])
            result = resumed.wait("result", f"failure-{index}", start)
            if result["code"] == 400:
                after = modes(database, session)
                assert after["context"] == before
                assert after["goal"]["status"] == 2
                assert "Context reduction" in after["goal"]["last_failure"]
                failed = True
                break
            assert result["success"], result
        assert failed, "summary failure path was not exercised"
        # An HTTP-successful but inadequate summary is also rejected, once;
        # no implicit quality retry consumes more budget or replaces state.
        RecoveryProvider.summary_fail = False
        RecoveryProvider.summary_short = True
        before = modes(database, session)["context"]
        before_requests = modes(database, session)["goal"]["requests"]
        summary_count = RecoveryProvider.counts["summary"]
        start = resumed.submit("short-summary", "compact", operation="compact", goal="context work", maximum_requests=0,
                               allow_commands=True, checks=["exit 0"])
        resumed.result("short-summary", start, 10)
        after = modes(database, session)
        assert after["context"] == before
        assert after["goal"]["status"] == 2
        assert after["goal"]["requests"] == before_requests + 1
        assert RecoveryProvider.counts["summary"] == summary_count + 1, "quality failure was silently retried"
        assert not RecoveryProvider.errors, RecoveryProvider.errors
        resumed.stop()
        succeeded = True
        print("native request recovery acceptance passed: Retry-After, 429/5xx limits, all-error five retries, provisional stream replacement, exact-once tool execution, cancel, per-attempt budget/usage, repeated model-scoped automatic compaction, cleaned private summaries, quality refusal, public history and cumulative budgets across restart")
    finally:
        for host in hosts:
            host.abort()
        advapi.CredDeleteW(target, 1, 0)
        server.shutdown()
        server.server_close()
        if succeeded:
            clean_generated_directory(project)
        else:
            print(f"failed fixture retained for inspection: {project}", file=sys.stderr)


if __name__ == "__main__":
    main()
