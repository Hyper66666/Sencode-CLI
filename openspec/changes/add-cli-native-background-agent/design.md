# Native background supervisor

One detached Sengoo supervisor owns a normal piped `--engine-stdio` child for one
native top-level turn. The child retains all Agent, child, Provider, tool, Plan,
Goal, budget, retry and context behavior. The supervisor forwards one durable
submission once and owns the worker's process tree until reaped.

`ProcessCommand.spawn_detached` returns PID plus OS creation identity, inherits
no stdio/handles, retains no launcher kill job and refuses an enclosing Windows
Job that cannot break away. All ordinary spawn/Drop behavior stays unchanged.
IPC peers are same-user/same-logon and verify server PID plus creation identity.
No PID-only stop or heartbeat takeover exists.

Job metadata/events use `<shared-db>.jobs.sqlite3` schema 1, an operational
sidecar with a separate migration lock. It cannot authorize shared execution.
The shared transcript/schema 29 and shared contract v1 remain unchanged.
Admission is committed before forwarding; that payload is never a retry queue.
After a crash the job is interrupted and public history remains inspectable.
Existing tool cleanup/fence checks determine whether explicit continuation is safe.

At most eight peers attach, with one controller identified by a fresh attach
epoch. Approval replies require that epoch, current engine nonce and stable
request ID. Observers never approve or start. Control loss while a Goal or
interaction is active cancels the engine and preserves paused state; attachment
never resumes it. Unattended ordinary turns use only captured permissions;
interaction without a controller cancels instead of manufacturing consent.

Frames and I/O queues are bounded, slow peers do not block worker output drain,
logs use monotonic sequences and explicit cursor expiration. Credentials and
authorization headers never enter the registry or logs. A failed persistence
operation cancels rather than letting side effects continue without admission.

Stop is idempotent and first requests cooperative cancellation, then shutdown,
with bounded owned-tree termination/reap. Uncertain cleanup never becomes
successful completion. Bootstrap without admission expires after ten seconds;
each submitted job also has an explicit bounded lifetime.

The root-owned CLI/TUI projects snapshots and events. No broad UI integration or
source-free installation claim follows from the synthetic provider fixture.
