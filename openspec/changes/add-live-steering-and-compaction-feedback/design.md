# Design

The frontend keeps ordinary queued tasks until a second unmodified Enter with
an empty composer explicitly sends a scoped `steer` control. FIFO order is
preserved. Menus, approval dialogs, multiline Enter and queue editing retain
priority. A transferred message has a stable ID and remains visible, muted,
until a durable `steering_applied` acknowledgment. Other pending tasks and the
draft are untouched. Managed backends retain the queue and report unsupported.

The single owner validates request identity, field shapes and existing image
bounds. Steering cannot change model, policy, Plan, Goal or budget. Its control
queue is bounded to eight pending 64-KiB messages. Duplicate IDs cannot append
twice within an execution. The controller commits user history before emitting
an applied acknowledgment and taking another model request. Complete tool pairs
precede insertion; already started requests and tool batches run to their safe
boundary. Cancellation wins. Unapplied messages are explicitly rejected at turn
end and returned to the paused frontend queue. A host crash with an unconfirmed
receipt retains the text for manual recovery and never automatically resends it.

Internal summary requests emit Compacting, including reasoning and retries.
Only successful checkpoint installation emits `context_compacted` with
上下文已压缩, followed by Working. This information uses a muted standalone
row, without NOTICE. Compaction failure remains a red notice and pauses safely.
All NOTICE rows use red foreground; NO_COLOR retains plain text.

Existing schema-v1 event envelopes accept additive event types. The selected
native session advertises live steering; other operations/backends reject it.
Tests distinguish native state machines, local HTTP fixtures, real Windows
console checks and installation evidence; no fixture implies live API coverage.
