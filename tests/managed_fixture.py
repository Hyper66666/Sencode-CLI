"""Real process/pipe tests for the two public managed runtime adapters.

The packaged runtimes in this isolated installation are Sengoo fixtures. This
test never launches an installed account runtime, reads an account credential,
logs in, or contacts a model service.
"""
from contextlib import closing
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time

from engine_fixture import Host, clean_generated_directory


def process_exists(pid):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    code = ctypes.c_ulong()
    kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    try:
        assert kernel.GetExitCodeProcess(handle, ctypes.byref(code))
        return code.value == 259
    finally:
        kernel.CloseHandle(handle)


def quiescent(database):
    with closing(sqlite3.connect(database)) as db:
        assert not db.execute("SELECT 1 FROM shared_executions WHERE active=1 OR cleanup_required=1").fetchone()
        assert not db.execute("SELECT 1 FROM shared_tool_ledger WHERE state='running'").fetchone()


def main():
    executable = Path(sys.argv[1]).resolve()
    runtime = Path(sys.argv[2]).resolve()
    root = Path(tempfile.mkdtemp(prefix="sencode-managed-中文😀-")).resolve()
    installation = root / "bin"
    installation.mkdir()
    project = root / "project"
    project.mkdir()
    entry = installation / "sencode-sg.exe"
    shutil.copyfile(executable, entry)
    digest = hashlib.sha256(runtime.read_bytes()).hexdigest()
    entries = []
    for engine, version, protocol, basename in (
        ("codex-app-server", "0.144.4", "0.144.4", "codex-app-server.exe"),
        ("sencode-acp", "0.2.102", "1", "sencode-agent.exe"),
    ):
        shutil.copyfile(runtime, installation / basename)
        entries.append(dict(engine=engine, runtime_version=version,
                            protocol_version=protocol, executable=basename, sha256=digest))
    manifest = {"schema": 1, "product": "sencode-cli", "target": "windows-x64", "managedRuntimes": entries}
    manifest_path = installation / "package-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    database = root / "fixture.sqlite"
    hosts = []
    succeeded = False
    try:
        bootstrap = Host(entry, project, database, "")
        hosts.append(bootstrap)
        bootstrap.stop()
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "test-fixture" if key == "instance_id" else None)
            for identifier, kind in (("codex-fixture", "codex"), ("sencode-fixture", "sencode")):
                db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,?,'managed',?,'{}','fixture-model',1,1)",
                           (identifier, kind, identifier))
            db.commit()
        (root / "profiles" / "codex" / "codex-fixture").mkdir(parents=True)
        (root / "profiles" / "sencode-managed" / "sencode-managed").mkdir(parents=True)
        # A fake provider secret reaches the host, but must not be inherited by
        # a managed account process. Its value is never written to test output.
        previous_secret = os.environ.get("SENCODE_FIXTURE_PROVIDER_SECRET")
        os.environ["SENCODE_FIXTURE_PROVIDER_SECRET"] = "fixture-only-do-not-forward"
        try:
            host = Host(entry, project, database, "codex-fixture")
        finally:
            if previous_secret is None:
                del os.environ["SENCODE_FIXTURE_PROVIDER_SECRET"]
            else:
                os.environ["SENCODE_FIXTURE_PROVIDER_SECRET"] = previous_secret
        hosts.append(host)
        for engine, connection in (("codex-app-server", "codex-fixture"), ("sencode-acp", "sencode-fixture")):
            denied = host.submit(engine + "-strict", "must not start", connection=connection)
            host.result(engine + "-strict", denied, 7)
            assert not (project / "managed.pid").exists(), "strict refusal started an account process"
            for name, options, code in (("plan", {"plan": True}, 7),
                                        ("goal", {"goal": "must pause", "plan": False}, 7),
                                        ("tokens", {"token_budget": 1, "plan": False}, 7),
                                        ("compact", {"operation": "compact", "plan": False}, 8),
                                        ("consult", {"operation": "consult", "plan": False}, 8)):
                identifier = engine + "-" + name
                start = host.submit(identifier, "must not start", connection=connection,
                                    permission_profile="backend", **options)
                host.result(identifier, start, code)
            for field in ("fixture-bad-version", "fixture-wrong-home") if engine == "codex-app-server" else ("fixture-bad-version",):
                marker = project / field
                marker.write_text("fixture", encoding="ascii")
                identifier = engine + "-" + field
                start = host.submit(identifier, "must reject handshake", connection=connection,
                                    permission_profile="backend", plan=False)
                host.result(identifier, start, 8)
                marker.unlink()
                quiescent(database)
                assert not process_exists(int((project / "managed.pid").read_text()))

            identifier = engine + "-stream"
            start = host.submit(identifier, "stream managed", connection=connection,
                                permission_profile="backend", plan=False)
            first = host.wait("text_delta", identifier, start)
            assert first["text"] == "managed ", first
            policy = host.wait("session", identifier, start)
            assert policy["engine"] == engine and policy["permission_scope"] == "managed-backend"
            assert not policy["enforced"] and not policy["request_accounting"] and not policy["token_accounting"]
            result = host.result(identifier, start)
            assert result["content"] == "managed 中文😀", result
            assert (project / "managed-env.txt").read_text() == "OS environment allowlist; provider secrets absent"
            assert "Current user task:\nstream managed" in (project / "managed-context.txt").read_text(encoding="utf-8")
            if engine == "sencode-acp":
                context = (project / "managed-context.txt").read_text(encoding="utf-8")
                assert "managed 中文😀" in context, "cross-engine context omitted shared public history"
            quiescent(database)
            assert not process_exists(int((project / "managed.pid").read_text()))

            for marker_name in ("fixture-wrong-session", "fixture-malformed"):
                marker = project / marker_name
                marker.write_text("fixture", encoding="ascii")
                identifier = engine + "-" + marker_name
                start = host.submit(identifier, "malformed managed", connection=connection, permission_profile="backend")
                host.result(identifier, start, 10)
                marker.unlink()
                assert not any(event.get("text") == "must not appear" for event in host.events[start:])
                quiescent(database)
                assert not process_exists(int((project / "managed.pid").read_text()))

            for allow in (False, True):
                approval_path = project / "managed-approved.txt"
                if approval_path.exists():
                    approval_path.unlink()
                identifier = engine + ("-allow" if allow else "-deny")
                start = host.submit(identifier, "approve managed" if allow else "deny managed", connection=connection,
                                    permission_profile="backend")
                approval = host.wait("approval", identifier, start)
                assert not approval_path.exists()
                host.send({"type": "approval", "id": approval["id"], "request_id": identifier, "approved": allow})
                host.result(identifier, start, 0 if allow else 12)
                assert approval_path.exists() == allow
                if allow:
                    assert approval_path.read_text(encoding="utf-8") == "managed approved 中文😀"
                quiescent(database)
                assert not process_exists(int((project / "managed.pid").read_text()))

            identifier = engine + "-slow"
            start = host.submit(identifier, "slow managed", connection=connection, permission_profile="backend")
            host.wait("text_delta", identifier, start)
            owned_pid = (project / "managed.pid").read_text()
            contender = Host(entry, project, database, connection)
            hosts.append(contender)
            conflict = contender.submit(engine + "-workspace-conflict", "must not start managed", permission_profile="backend")
            refused = contender.wait("result", engine + "-workspace-conflict", conflict)
            assert not refused["success"] and refused["code"] != 0, "another session entered an owned workspace"
            assert (project / "managed.pid").read_text() == owned_pid, "conflicting runtime was started"
            contender.stop()
            cancelled_at = time.monotonic()
            host.send({"type": "cancel", "id": identifier})
            host.result(identifier, start, 19)
            assert time.monotonic() - cancelled_at < 5
            quiescent(database)
            assert not process_exists(int((project / "managed.pid").read_text()))

            marker = project / "fixture-crash"
            marker.write_text("fixture", encoding="ascii")
            identifier = engine + "-crash"
            start = host.submit(identifier, "crash managed", connection=connection, permission_profile="backend")
            host.result(identifier, start, 9)
            marker.unlink()
            quiescent(database)
            (project / "managed.pid").unlink()

        # Admission lives in the shared DB, independently of the process host.
        session = host.session
        host.stop()
        restarted = Host(entry, project, database, "codex-fixture", session)
        hosts.append(restarted)
        stamp = (project / "managed-context.txt").stat().st_mtime_ns
        start = restarted.submit("codex-app-server-allow", "approve managed", permission_profile="backend")
        restarted.result("codex-app-server-allow", start, 12)
        assert (project / "managed-context.txt").stat().st_mtime_ns == stamp

        entries[0]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        start = restarted.submit("tampered", "must not run", permission_profile="backend")
        restarted.result("tampered", start, 8)
        assert not (project / "managed.pid").exists()
        quiescent(database)
        restarted.stop()
        succeeded = True
        print("managed public protocol acceptance passed: pinned package/hash, explicit backend consent, strict policy refusal, two engines, UTF-8 stream, shared context, opaque approvals, cancellation, process cleanup, handshake rejection, crash and durable replay refusal")
    finally:
        for host in hosts:
            host.abort()
        if succeeded:
            clean_generated_directory(root)
        else:
            print(f"failed fixture retained for inspection: {root}", file=sys.stderr)


if __name__ == "__main__":
    main()
