# Explicit Agent jobs on Windows

Start an ordinary native API task that may continue after its launching terminal
closes:

```powershell
sen agent start -p "Inspect this project and report its architecture"
sen agent list
sen agent attach JOB_ID
sen agent logs JOB_ID
sen agent logs JOB_ID --follow
sen agent stop JOB_ID
sen resume SESSION_ID
```

Use `--cwd PATH` and `--database PATH` to select an isolated workspace/profile.
`--connection ID` and `--model ID` select the native API target. Managed account
backends are unavailable for background jobs. Ordinary foreground `sen` keeps
its existing behavior.

The start command prints the job ID, public session ID and selected target.
Each job runs one top-level Agent turn, including its existing child tasks. It
has a default one-hour lifetime; `--job-timeout-ms` accepts 1000 through 86400000.
`--max-requests` and an explicitly provided `--token-budget` retain their engine
meaning. Switching the application's default connection does not retarget an
already admitted job.

Default file/command/MCP permissions still apply. Starting in the background
does not grant tool permissions. An unattended job that requests approval or a
user answer pauses without executing that operation. An attached text terminal
can review the live request and answer it. `--auto-edit` or `--allow-commands`
must be explicitly supplied to authorize those existing capabilities.

`--observe` attaches without control. Only one client may hold control. Losing a
controller while a permission request is pending cancels that interaction;
approvals from the old attachment are never replayed. Ctrl+C while controlling
an attached job requests stop; an observer can leave without stopping ordinary
work. `stop` is idempotent and waits for owned worker cleanup.

Goal stays attached:

```powershell
sen agent start --goal "Implement the change and pass the checks" --check "your test command"
```

Goal requires an interactive text terminal. Disconnecting its controller pauses
the Goal and preserves its request/token accounting. Attaching to logs, reopening
a terminal or sending an ordinary follow-up does not resume it. Explicitly resume
the saved public session and use `/goal resume` after reviewing its state.

For automation:

```powershell
sen agent start -p "Inspect this project" --output-format json
sen agent logs JOB_ID --after 12 --output-format json
sen agent logs JOB_ID --follow --output-format stream-json
sen agent attach JOB_ID --observe --output-format stream-json
```

`json` writes one snapshot or one bounded log page. Live attach and `--follow`
require `text` or `stream-json`; structured/redirected clients never approve tools
automatically. Stream events use schema 1 `job_event` envelopes with `job_id`,
`generation`, monotonic `sequence` and the existing engine `event`. Reconnect
using `--after SEQUENCE` and deduplicate by job/generation/sequence.

Logs retain at most 512 events and 16 MiB per job. Expired cursors return an
explicit `cursor_expired` response with a snapshot and the first retained
sequence. Public session history is preserved separately and remains the source
for future conversation context. The event log is an operational view and can
have a final gap if the host crashes after a public-history commit.

Operational metadata lives in `<shared-database>.jobs.sqlite3`. Include it with
the shared database if job logs are needed in a backup. It holds the admitted
prompt and bounded local event history, but receives no provider credential or
authorization header. Its schema is independent of shared contract v1/schema29
and it grants no session execution authority. Existing shared locks, execution
IDs, fences and tool-cleanup checks remain authoritative.

The supervisor authenticates same-user/same-logon Windows IPC and verifies both
PID and process creation identity. No heartbeat or PID-only termination grants
takeover. If a supervisor crashes, logs remain inspectable and the job becomes
interrupted; requests, uncertain tools and approvals are never automatically
replayed or restarted. A pending cleanup marker still requires explicit review.

This feature is Windows native API support. Synthetic provider acceptance is
recorded separately from installed-candidate and live-service verification.
