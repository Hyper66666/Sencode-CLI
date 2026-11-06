"""Windows synthetic-provider acceptance for the real Sengoo background host.

Uses a temporary shared database, operational sidecar, unique credential target
and actual named-pipe/process/engine paths. No user profile or live API is read.
"""
from contextlib import closing
import ctypes
import http.server
import io
import json
import os
from pathlib import Path
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from cli_fixture import Credential
from engine_fixture import Provider, clean_generated_directory


TERMINAL = {"completed", "paused", "failed", "interrupted", "cleanup_unknown"}


class BackgroundProvider(Provider):
    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        request = json.loads(raw)
        prompt = next(value["content"] for value in reversed(request["messages"]) if value["role"] == "user")
        if prompt != "flood slow observer":
            self.rfile = io.BytesIO(raw)
            return super().do_POST()
        assert self.headers.get("Authorization") == "Bearer fixture-key"
        with self.lock:
            self.requests.append(request)
        frames = [("data: " + json.dumps({"choices": [{"delta": {"content": "x" * 2048}, "finish_reason": None}]}) + "\n\n").encode()
                  for _ in range(256)]
        frames += [("data: " + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}],
                                           "usage": {"prompt_tokens": 11, "completion_tokens": 7}}) + "\n\n").encode(),
                   b"data: [DONE]\n\n"]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(sum(map(len, frames))))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            for frame in frames:
                self.wfile.write(frame)
                self.wfile.flush()
                time.sleep(.002)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        finally:
            self.close_connection = True


class Bridge:
    def __init__(self, executable, database, identifier, role="control"):
        self.process = subprocess.Popen(
            [str(executable), "bridge", str(database), identifier, role],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1)
        self.incoming = queue.Queue()
        self.events = []

        def reader():
            for line in self.process.stdout:
                try:
                    self.incoming.put(json.loads(line))
                except Exception as exc:
                    self.incoming.put({"type": "invalid", "error": str(exc), "line": line})
            self.incoming.put({"type": "eof"})

        threading.Thread(target=reader, daemon=True).start()
        self.ready = self.wait(lambda event: event.get("type") == "ready")

    def wait(self, predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                value = self.incoming.get(timeout=max(.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if value.get("type") == "logs":
                self.events.extend(value["events"])
                for wrapper in value["events"]:
                    if predicate(wrapper["event"]):
                        return wrapper["event"]
            if predicate(value):
                return value
            if value.get("type") in {"invalid", "eof"}:
                raise AssertionError((value, self.process.stderr.read()))
        raise AssertionError(("bridge timeout", self.ready if hasattr(self, "ready") else None, self.events[-8:]))

    def send(self, kind, **values):
        message = dict(schema=1, type=kind, job_id=self.ready["job_id"],
                       generation=self.ready["generation"], **values)
        if kind not in {"stop", "logs"}:
            message.setdefault("control_epoch", self.ready["control_epoch"])
        self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def close(self):
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        for stream in (self.process.stdout, self.process.stderr):
            if stream:
                stream.close()


def main():
    executable = Path(sys.argv[1]).resolve()
    project = Path(tempfile.mkdtemp(prefix="sencode-background-中文😀-")).resolve()
    database = project / "shared.sqlite"
    sidecar = Path(str(database) + ".jobs.sqlite3")
    identifier = "custom-background-fixture-" + uuid.uuid4().hex
    target = "Sencode/connection/" + identifier
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), BackgroundProvider)
    server.child_connection = identifier
    threading.Thread(target=server.serve_forever, daemon=True).start()
    key = (ctypes.c_ubyte * len(b"fixture-key")).from_buffer_copy(b"fixture-key")
    credential = Credential(Type=1, TargetName=target, CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    assert advapi.CredWriteW(ctypes.byref(credential), 0), ctypes.WinError(ctypes.get_last_error())
    bridges = []
    jobs = []
    succeeded = False

    def run(*arguments, check=True, timeout=20):
        result = subprocess.run([str(executable), *map(str, arguments)], cwd=project,
                                capture_output=True, encoding="utf-8", timeout=timeout)
        if check:
            assert result.returncode == 0, (arguments, result.returncode, result.stdout, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() and result.returncode == 0 else result

    def start(text, prepare=False, **options):
        submit = dict(type="submit", id="submit-" + uuid.uuid4().hex, text=text,
                      connection=identifier, model="background-fixture-model", plan=False,
                      auto_edit=False, allow_commands=False, maximum_requests=50,
                      token_budget=0, operation="turn", goal="", checks=[], permission_profile="strict")
        submit.update(options)
        path = project / (submit["id"] + ".json")
        path.write_text(json.dumps(submit, ensure_ascii=False), encoding="utf-8")
        job = run("prepare" if prepare else "start", database, project, path)
        jobs.append(job["job_id"])
        return job, submit

    def terminal(job, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            snapshot = run("snapshot", database, job["job_id"])
            if snapshot["state"] in TERMINAL:
                return snapshot
            time.sleep(.03)
        raise AssertionError(("job failed to terminate", snapshot))

    try:
        run("init", database)
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "test-fixture" if key == "instance_id" else None)
            configuration = json.dumps({"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                                        "protocol": "chatCompletions", "successfulProtocol": "chatCompletions",
                                        "selectedModelId": "background-fixture-model", "credentialRef": target, "enabledModels": []})
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Background fixture',?,'background-fixture-model',1,1)",
                       (identifier, configuration))
            db.commit()

        job, submit = start("slow detached 中文😀")
        assert job["admitted"] and job["host_pid"] > 0 and job["host_creation_identity"] > 0
        observe = Bridge(executable, database, job["job_id"], "observe")
        bridges.append(observe)
        first = observe.wait(lambda e: e.get("type") == "text_delta")
        assert first["text"]
        finished = terminal(job)
        assert finished["state"] == "completed", finished
        logs = run("logs", database, job["job_id"], 0)
        assert any("中文" in e["event"].get("text", "") for e in logs["events"])
        sequences = [e["sequence"] for e in logs["events"]]
        assert sequences == sorted(set(sequences))
        cursor = sequences[len(sequences) // 2]
        suffix = run("logs", database, job["job_id"], cursor)
        assert all(e["sequence"] > cursor for e in suffix["events"])
        assert run("stop", database, job["job_id"])["state"] == "completed"
        observe.close()
        print("PASS detached launcher exit, streaming Unicode, cursor logs, terminal stop", flush=True)

        job, submit = start("permission allow", prepare=True)
        controller = Bridge(executable, database, job["job_id"])
        bridges.append(controller)
        controller.send("start")
        approval = controller.wait(lambda e: e.get("type") == "approval")
        controller.send("start")
        assert controller.wait(lambda e: e.get("type") == "error")["code"] == 12
        controller.send("logs", after=0, unknown=True)
        assert controller.wait(lambda e: e.get("type") == "error")["code"] == 2
        rejected = subprocess.run([str(executable), "bridge", str(database), job["job_id"], "control"],
                                  capture_output=True, encoding="utf-8", timeout=8)
        assert rejected.returncode != 0, rejected.stdout
        observer = Bridge(executable, database, job["job_id"], "observe")
        bridges.append(observer)
        observer.send("approval", id=approval["id"], request_id=submit["id"], approved=True)
        assert observer.wait(lambda e: e.get("type") == "error")["code"] == 7
        controller.send("approval", control_epoch="stale-epoch", id=approval["id"], request_id=submit["id"], approved=True)
        assert controller.wait(lambda e: e.get("type") == "error")["code"] == 7
        assert not (project / "approved.txt").exists()
        controller.send("approval", id=approval["id"], request_id=submit["id"], approved=True)
        assert terminal(job)["state"] == "completed"
        assert (project / "approved.txt").read_text(encoding="utf-8") == "approved 中文😀"
        controller.close()
        observer.close()
        print("PASS attached approvals, observer refusal, stale control epoch", flush=True)

        job, submit = start("permission deny", prepare=True)
        controller = Bridge(executable, database, job["job_id"])
        bridges.append(controller)
        controller.send("start")
        controller.wait(lambda e: e.get("type") == "approval")
        controller.close()
        done = terminal(job)
        assert done["state"] == "paused" and done["reason"] == "interaction_controller_disconnected", done
        assert not (project / "denied.txt").exists()
        print("PASS approval disconnect cancels without side effect", flush=True)

        job, submit = start("permission deny")
        done = terminal(job)
        assert done["state"] == "paused" and done["reason"] == "interaction_required", done
        assert not (project / "denied.txt").exists()
        print("PASS detached approval fails closed", flush=True)

        job, submit = start("slow goal disconnect", prepare=True, goal="slow goal disconnect", maximum_requests=9)
        controller = Bridge(executable, database, job["job_id"])
        bridges.append(controller)
        controller.send("start")
        controller.wait(lambda e: e.get("type") == "text_delta")
        controller.close()
        done = terminal(job)
        assert done["state"] == "paused" and done["reason"] == "goal_controller_disconnected", done
        with closing(sqlite3.connect(database)) as db:
            mode = json.loads(db.execute("SELECT mode_json FROM shared_modes WHERE session_id=?", (job["session_id"],)).fetchone()[0])["goal"]
            assert mode["status"] == 2 and mode["requests"] >= 1 and mode["max_requests"] == 9, mode
        before = len(Provider.requests)
        run("logs", database, job["job_id"], 0)
        run("list", database)
        time.sleep(.2)
        assert len(Provider.requests) == before
        print("PASS Goal control loss pauses persistently and observation never resumes", flush=True)

        job, submit = start("cancel command", allow_commands=True)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            with closing(sqlite3.connect(database)) as db:
                tool = db.execute("SELECT state FROM shared_tool_ledger WHERE session_id=? AND name='run_command'", (job["session_id"],)).fetchone()
            if tool:
                break
            time.sleep(.03)
        assert tool, "real command never started"
        done = run("stop", database, job["job_id"])
        assert done["state"] == "paused" and done["reason"] == "stopped", done
        assert run("stop", database, job["job_id"])["state"] == "paused"
        with closing(sqlite3.connect(database)) as db:
            assert not db.execute("SELECT 1 FROM shared_tool_ledger WHERE session_id=? AND state='running'", (job["session_id"],)).fetchone()
        print("PASS real command cancellation, cleanup ledger and idempotent stop", flush=True)

        # This is a test-owned process from this isolated registry. No PID from
        # user state or another application is opened or terminated.
        job, submit = start("slow crash no replay")
        observer = Bridge(executable, database, job["job_id"], "observe")
        bridges.append(observer)
        observer.wait(lambda e: e.get("type") == "text_delta")
        before = len(Provider.requests)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x00100001, False, job["host_pid"])
        assert handle, ctypes.WinError(ctypes.get_last_error())
        try:
            assert kernel.TerminateProcess(handle, 99)
            assert kernel.WaitForSingleObject(handle, 5000) == 0
        finally:
            kernel.CloseHandle(handle)
        done = terminal(job)
        assert done["state"] == "interrupted" and done["reason"] == "host_exited_no_replay", done
        assert run("stop", database, job["job_id"])["state"] == "interrupted"
        run("logs", database, job["job_id"], 0)
        replay = subprocess.run([str(executable), "--background-host", job["job_id"], "--database", str(database)],
                                capture_output=True, encoding="utf-8", timeout=8)
        assert replay.returncode != 0
        time.sleep(.2)
        assert len(Provider.requests) == before
        observer.close()
        print("PASS supervisor crash, receipt recovery and accepted-submit no replay", flush=True)

        job, submit = start("bootstrap must not run", prepare=True)
        original = job["host_creation_identity"]
        with closing(sqlite3.connect(sidecar)) as db:
            db.execute("UPDATE cli_jobs SET host_creation_identity=? WHERE id=?", (original + 1, job["job_id"]))
            db.commit()
        mismatch = subprocess.run([str(executable), "bridge", str(database), job["job_id"], "observe"],
                                  capture_output=True, encoding="utf-8", timeout=8)
        assert mismatch.returncode != 0
        with closing(sqlite3.connect(sidecar)) as db:
            db.execute("UPDATE cli_jobs SET host_creation_identity=? WHERE id=?", (original, job["job_id"]))
            db.commit()
        before = len(Provider.requests)
        done = terminal(job, timeout=15)
        assert done["state"] == "interrupted" and done["reason"] == "bootstrap_expired", done
        assert len(Provider.requests) == before
        print("PASS process birth mismatch and unattended bootstrap expiration", flush=True)

        wrapper = run("agent", "start", "--database", database, "--cwd", project,
                      "--connection", identifier, "--model", "background-fixture-model",
                      "-p", "slow public wrapper", "--output-format", "json")
        jobs.append(wrapper["job_id"])
        public = subprocess.run([str(executable), "agent", "attach", wrapper["job_id"],
                                 "--database", str(database), "--cwd", str(project),
                                 "--output-format", "stream-json"], stdin=subprocess.DEVNULL,
                                capture_output=True, encoding="utf-8", timeout=15)
        assert public.returncode == 0, (public.stdout, public.stderr)
        public_events = [json.loads(line) for line in public.stdout.splitlines()]
        assert any(value.get("type") == "job_event" and value["event"].get("type") == "text_delta"
                   for value in public_events), public_events
        exported = run("agent", "logs", wrapper["job_id"], "--database", database,
                       "--cwd", project, "--output-format", "json")
        assert exported["type"] == "logs" and exported["events"]
        listed = run("agent", "list", "--database", database, "--cwd", project, "--output-format", "json")
        assert any(item["job_id"] == wrapper["job_id"] and item["state"] == "completed" for item in listed["jobs"])
        refusal = run("agent", "start", "--database", database, "--cwd", project,
                      "--connection", identifier, "--goal", "must stay attached", "--output-format", "json", check=False)
        assert isinstance(refusal, subprocess.CompletedProcess) and refusal.returncode != 0
        print("PASS public command wrapper start/list/attach/logs and unattended Goal refusal", flush=True)

        # Open a real authenticated same-logon native observer and deliberately
        # stop reading it. The host must keep draining its worker and honor stop.
        job, submit = start("flood slow observer", prepare=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong,
                                      ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.WriteFile.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong,
                                    ctypes.POINTER(ctypes.c_ulong), ctypes.c_void_p]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        pipe = None
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            names = [name for name in os.listdir("\\\\.\\pipe\\") if name.endswith("." + job["endpoint"])]
            if names:
                assert len(names) == 1
                pipe = kernel.CreateFileW("\\\\.\\pipe\\" + names[0], 0xC0000000, 0, None, 3, 0, None)
                if pipe not in (None, ctypes.c_void_p(-1).value):
                    break
            time.sleep(.01)
        assert pipe not in (None, ctypes.c_void_p(-1).value)
        try:
            greeting = (json.dumps(dict(schema=1, type="hello", job_id=job["job_id"], generation=job["generation"], role="observe", after=0)) + "\n").encode()
            payload = ctypes.create_string_buffer(greeting)
            written = ctypes.c_ulong()
            assert kernel.WriteFile(pipe, payload, len(greeting), ctypes.byref(written), None)
            assert written.value == len(greeting)
            controller = Bridge(executable, database, job["job_id"])
            bridges.append(controller)
            controller.send("start")
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                with closing(sqlite3.connect(database)) as db:
                    emitted = db.execute("SELECT MAX(length(text)) FROM messages WHERE session_id=? AND role='assistant'", (job["session_id"],)).fetchone()[0]
                if (emitted or 0) >= 131072:
                    break
                time.sleep(.01)
            assert (emitted or 0) >= 131072
            then = time.monotonic()
            done = run("stop", database, job["job_id"])
            assert done["state"] in {"completed", "paused"}, done
            assert time.monotonic() - then < 10
            controller.close()
        finally:
            kernel.CloseHandle(pipe)
        print("PASS unread native observer backpressure, large stream and responsive stop", flush=True)

        assert not Provider.errors, Provider.errors
        with closing(sqlite3.connect(database)) as db:
            assert db.execute("PRAGMA user_version").fetchone()[0] == 29
            assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='cli_jobs'").fetchone()
        with closing(sqlite3.connect(sidecar)) as db:
            assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        succeeded = True
        print("PASS background native end-to-end acceptance; shared schema unchanged", flush=True)
    finally:
        for bridge in bridges:
            bridge.close()
        for identifier in jobs:
            try:
                run("stop", database, identifier, timeout=20)
            except Exception:
                pass
        advapi.CredDeleteW(target, 1, 0)
        server.shutdown()
        server.server_close()
        if succeeded:
            clean_generated_directory(project)
        else:
            print("Fixture retained for diagnosis:", project, file=sys.stderr)


if __name__ == "__main__":
    main()
