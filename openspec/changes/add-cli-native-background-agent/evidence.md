# Native background Agent evidence

Recorded 2026-11-04T21:01:42+08:00 on Windows x64 host `DESKTOP-FUAQMFB`.

Sencode repository baseline:
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a`.
Sengoo repository baseline:
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`.
Both retain pre-existing and current uncommitted source work; these are baseline
identities, not a release candidate commit claim.

## Artifact SHA256

| Artifact | SHA256 |
| --- | --- |
| `target/background/job_probe.exe` | `dd451459e83fba089984da3d66a8b88bbb27abb7c4848c2715a47ccf8b52f6ab` |
| `target/background/tests_jobs.exe` | `0bf968b402b15c66612242b1970a71ca90ff389d4a3a78aedd78d32f2c8c8c8e` |
| `target/terminal-pane-draft/sencode-combined.exe` | `ca0ba6e9cea2044885508bb5204e985c20a74d70ff0de6e6e2194a038ecc8840` |
| `D:/Sengoo/target/debug/sgc.exe` | `b79895635aabd0acfef17a81f9f7f0060fcc473bc56b41da47ebb7ff6912169c` |

Detailed source/fixture/imported-module/runtime hashes and exact command results
are in `D:/sencode/windows/sencode-cli/target/background/evidence.json`.
Artifacts are source-development outputs and are not release eligible.

## Checks actually run

From `D:/sencode/windows/sencode-cli`, with `sgsqlite` mapped to the local official
package and the declared source-development runtime:

```text
sgc --runtime-mode source-development build src/job_probe.sg --force-rebuild -O 0 -o target/background/job_probe.exe
sgc --runtime-mode source-development build src/tests_jobs.sg --force-rebuild -O 0 -o target/background/tests_jobs.exe
target/background/tests_jobs.exe --database <isolated-temporary-path>
python tests/background_fixture.py target/background/job_probe.exe
python tests/background_public_fixture.py target/terminal-pane-draft/sencode-combined.exe
```

The two builds and all three executable checks passed. Python was
`C:/Users/admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.

`tests_jobs` checked partial/Unicode/malformed/unknown/oversized frames, durable
duplicate admission refusal, a 512-event retention boundary, independent 16-MiB
retention using twenty approximately 960-KiB events, a near-limit event cursor
read, registry reopening and absence of shared execution authority. Final run
took approximately 1.99 seconds.

`background_fixture.py` checked real detached launcher survival, named-pipe
attach and Unicode streaming, monotonic cursor logs, controller contention,
observer/stale epoch/duplicate start/unknown-field refusal, approved writes,
approval disconnect and unattended interaction pause without a write, Goal
disconnect pause with durable budgets, real PowerShell command cancellation and
idempotent stop, supervisor crash with no accepted-submit replay, mismatched
process birth identity, ten-second bootstrap expiry, public wrapper routes and
an unread native observer during a large stream with responsive stopping.

`background_public_fixture.py` used only the combined main executable's public
commands. It checked `agent start/list/attach/logs/stop`, top-level aliases,
redirected `stream-json` attach, Unicode, cursor/follow behavior, permission and
unattended Goal refusal, a one-second lifetime pause, real command/ledger/shared
execution cleanup, parser boundaries and receipt-matched detached host exit.
Final run took approximately 6.75 seconds.

Each Python fixture created a temporary workspace/database/sidecar and a unique
Credential Manager fixture target, used a loopback synthetic API, stopped its
owned jobs and removed its own credentials and generated files after success.
No user profile, live API, OAuth account or existing session was consumed.

From `D:/sencode/windows`:

```text
openspec validate add-cli-native-background-agent --strict
```

Validation passed. Both Python files also passed `py_compile`.

## Limits on this evidence

This is Windows source-development and synthetic-provider verification. It does
not close the integration owner's source-free installed candidate acceptance,
live provider checks, other platforms or managed background execution. Generic
IPC cross-user/logon and detached process tests belong to their independently
recorded Sengoo foundation evidence. No automatic replay/restart or background
Goal is advertised.
