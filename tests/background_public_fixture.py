"""Exercise only the installed/public main CLI Agent routes with an isolated API.

Run: python tests/background_public_fixture.py path/to/sencode-combined.exe
No probe commands, user profiles, live provider or real account are used.
"""
from contextlib import closing
import ctypes
import http.server
import json
from pathlib import Path
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


def main():
    executable = Path(sys.argv[1]).resolve()
    project = Path(tempfile.mkdtemp(prefix="sencode-public-background-中文😀-")).resolve()
    database = project / "public.sqlite"
    identifier = "custom-public-background-" + uuid.uuid4().hex
    target = "Sencode/connection/" + identifier
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    server.child_connection = identifier
    threading.Thread(target=server.serve_forever, daemon=True).start()
    key = (ctypes.c_ubyte * len(b"fixture-key")).from_buffer_copy(b"fixture-key")
    credential = Credential(Type=1, TargetName=target, CredentialBlobSize=len(key), CredentialBlob=key, Persist=1)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    assert advapi.CredWriteW(ctypes.byref(credential), 0), ctypes.WinError(ctypes.get_last_error())
    jobs = []
    succeeded = False

    def invoke(*arguments, check=True, timeout=20, format="json"):
        result = subprocess.run([str(executable), *map(str, arguments), "--database", str(database),
                                 "--cwd", str(project), "--output-format", format],
                                cwd=project, stdin=subprocess.DEVNULL, capture_output=True,
                                encoding="utf-8", timeout=timeout)
        if check:
            assert result.returncode == 0, (arguments, result.returncode, result.stdout, result.stderr)
        return result

    def command(*arguments, **options):
        result = invoke(*arguments, **options)
        return json.loads(result.stdout)

    def snapshot(job):
        values = command("agent", "list")["jobs"]
        return next(item for item in values if item["job_id"] == job["job_id"])

    def terminal(job, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            value = snapshot(job)
            if value["state"] in TERMINAL:
                return value
            time.sleep(.03)
        raise AssertionError(("public job timeout", value))

    def start(text, **options):
        arguments = ["agent", "start", "-p", text, "--connection", identifier,
                     "--model", "public-background-model"]
        for key, value in options.items():
            arguments.append("--" + key.replace("_", "-"))
            if value is not True:
                arguments.append(str(value))
        value = command(*arguments)
        jobs.append(value["job_id"])
        return value

    try:
        assert command("agent", "list")["jobs"] == []
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "public-background-fixture" if key == "instance_id" else None)
            config = {"version": 2, "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                      "protocol": "chatCompletions", "successfulProtocol": "chatCompletions",
                      "selectedModelId": "public-background-model", "credentialRef": target, "enabledModels": []}
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','Public background fixture',?,'public-background-model',1,1)",
                       (identifier, json.dumps(config)))
            db.commit()

        job = start("slow public main 中文😀")
        assert job["admitted"] and job["host_pid"] > 0 and job["host_creation_identity"] > 0
        attached = invoke("agent", "attach", job["job_id"], "--observe", format="stream-json")
        events = [json.loads(line) for line in attached.stdout.splitlines()]
        stream = [item for item in events if item.get("type") == "job_event"]
        assert any(item["event"].get("type") == "text_delta" and "中文" in item["event"].get("text", "") for item in stream), events
        sequences = [item["sequence"] for item in stream]
        assert sequences == sorted(set(sequences))
        assert terminal(job)["state"] == "completed"
        logs = command("agent", "logs", job["job_id"])
        assert logs["type"] == "logs" and logs["events"]
        cursor = logs["events"][len(logs["events"]) // 2]["sequence"]
        suffix = command("agent", "logs", job["job_id"], "--after", cursor)
        assert suffix["events"] and all(item["sequence"] > cursor for item in suffix["events"])
        followed = invoke("logs", job["job_id"], "--follow", "--after", 0, format="stream-json")
        assert any(json.loads(line).get("type") == "job_event" for line in followed.stdout.splitlines())
        assert command("stop", job["job_id"])["state"] == "completed"
        print("PASS public main start/list/attach, streaming Unicode, logs/follow/cursor and aliases", flush=True)

        denied = start("permission deny")
        done = terminal(denied)
        assert done["state"] == "paused" and done["reason"] == "interaction_required", done
        assert not (project / "denied.txt").exists()
        limited = start("slow lifetime", job_timeout_ms=1000)
        done = terminal(limited)
        assert done["state"] == "paused" and done["reason"] == "lifetime_exceeded", done
        print("PASS public detached permission refusal and bounded lifetime", flush=True)

        running = start("cancel command", allow_commands=True)
        deadline = time.monotonic() + 10
        tool = None
        while time.monotonic() < deadline:
            with closing(sqlite3.connect(database)) as db:
                tool = db.execute("SELECT state FROM shared_tool_ledger WHERE session_id=? AND name='run_command'", (running["session_id"],)).fetchone()
            if tool:
                break
            time.sleep(.03)
        assert tool
        stopped = command("agent", "stop", running["job_id"])
        assert stopped["state"] == "paused" and stopped["reason"] == "stopped", stopped
        assert command("agent", "stop", running["job_id"])["state"] == "paused"
        with closing(sqlite3.connect(database)) as db:
            assert not db.execute("SELECT 1 FROM shared_tool_ledger WHERE session_id=? AND state='running'", (running["session_id"],)).fetchone()
            assert db.execute("SELECT active FROM shared_executions WHERE session_id=?", (running["session_id"],)).fetchone()[0] == 0
        print("PASS public stop real command, cleanup authority and repeated stop", flush=True)

        rejected = invoke("agent", "start", "--goal", "must stay attached", "--connection", identifier, check=False)
        assert rejected.returncode != 0
        rejected = invoke("agent", "logs", job["job_id"], "--follow", check=False)
        assert rejected.returncode != 0
        rejected = invoke("agent", "start", "-p", "invalid lifetime", "--connection", identifier,
                          "--job-timeout-ms", 10, check=False)
        assert rejected.returncode != 0
        rejected = invoke("agent", "logs", job["job_id"], "--after=-1", check=False)
        assert rejected.returncode != 0
        print("PASS public Goal/control and parser-boundary refusals", flush=True)

        assert not Provider.errors, Provider.errors
        with closing(sqlite3.connect(database)) as db:
            assert db.execute("PRAGMA user_version").fetchone()[0] == 29
            assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='cli_jobs'").fetchone()
        # Terminal publication occurs before a short final peer drain. Verify
        # every actual detached host identity exits instead of leaving daemons.
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                           ctypes.c_void_p, ctypes.c_void_p]
        for job_id in jobs:
            value = snapshot({"job_id": job_id})
            handle = kernel.OpenProcess(0x00101000, False, value["host_pid"])
            if handle:
                try:
                    birth, ended, system, user = (ctypes.c_ulonglong() for _ in range(4))
                    assert kernel.GetProcessTimes(handle, ctypes.byref(birth), ctypes.byref(ended),
                                                   ctypes.byref(system), ctypes.byref(user))
                    if birth.value == value["host_creation_identity"]:
                        assert kernel.WaitForSingleObject(handle, 5000) == 0, value
                finally:
                    kernel.CloseHandle(handle)
            else:
                assert ctypes.get_last_error() in (87, 1168), ctypes.WinError(ctypes.get_last_error())
        succeeded = True
        print("PASS public main native background acceptance and host exit", flush=True)
    finally:
        for job_id in jobs:
            try:
                invoke("agent", "stop", job_id, timeout=20)
            except Exception:
                pass
        advapi.CredDeleteW(target, 1, 0)
        server.shutdown()
        server.server_close()
        if succeeded:
            clean_generated_directory(project)
        else:
            print("Public fixture retained for diagnosis:", project, file=sys.stderr)


if __name__ == "__main__":
    main()
