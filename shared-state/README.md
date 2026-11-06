# Shared store v1

Schema 29 extends the desktop schema 28. Both applications register the SQL
function `sengoo_context(key)`; `instance_id` identifies the owning connection.
Missing functions fail closed on protected writes. Secrets never enter this DB.

The database file is canonicalized. Lock paths are `<db>.locks/<sha256>.lock`,
where the hash input is `scope + ':' + identity` encoded as UTF-8. Scopes:
`migration`, `session`, `workspace`, `connection`. Session identity is its exact
ID. Workspace identity is its canonical native path. Locks are nonblocking,
exclusive and non-inheritable; files are never deleted to release ownership.

A process holds its session lock from claim through child-process cleanup.
Claims increment `fence` in a transaction. Every CLI event checks owner,
execution ID, fence and active state. A heartbeat alone is never an ownership
proof. Recovery requires acquiring the released OS lock first. When the old
desktop execution or a CLI tool ledger is incomplete, `cleanup_required` remains
set: startup may classify the task as interrupted, but dispatch refuses to take
it over. The current anonymous Job Objects cannot supply a cross-process cleanup
certificate. This conservative recovery gate remains an explicit delivery item;
do not clear its database flag or infer cleanup from a dead PID. A CLI model-only
turn with no pending tool can be recovered under the released lock. Side effects
with an incomplete ledger are never automatically replayed.

`shared_history` preserves portable structured messages beside desktop-visible
`messages`. Legacy desktop messages are reconstructed from public text and tool
records. `shared_engine_bindings` namespaces opaque native state. The original
`runtime_bindings` remains the desktop runtime's compatibility surface and its
insert/update/delete triggers mirror the desktop namespace transactionally.
Each inserted message captures the current turn fence. CLI commits validate the
owner, execution ID and fence; desktop callbacks retain their message's fence,
including when a later turn runs in the same desktop process.
Desktop dispatch and terminal insertion also require the original accepted user
message, even when an assistant placeholder does not exist yet. Edit/resend and
shared/managed ACP fallback sends claim the same session lease. Unfenced legacy
state setters cannot change a session with shared execution history.

Changelog triggers commit alongside shared records; consumers poll by sequence.
Initial migration uses the OS migration lock, a SQLite backup and a schema version
increase. Close older desktop clients before upgrading both applications; the
automatic exclusion of an already-running old desktop is not yet qualified.
Unsupported writers refuse the upgraded schema. The CLI refuses an uncoordinated
schema 28 upgrade. Never exercise migration on the user's real DB in tests.
