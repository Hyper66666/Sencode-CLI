# Long-history query and recovery design

## Data ownership and lifecycle

Public transcript rows remain immutable evidence except through existing
fenced transcript operations. Query failure does not remove rows, rewrite
checkpoints or spend request budgets. `messages_seen` is an absolute public
message count, independent of revision gaps and the displayed recent window.

Additive APIs retain `Result<_,i64>`:

- `cli_state_history_count(state,id)` returns the SQL count.
- `cli_state_history_range(state,id,start,count)` returns an exact ascending
  absolute range; invalid bounds fail 2.
- `cli_state_history_tail(state,id,messages_seen)` returns every newer row;
  invalid consumed counts fail 10.
- `cli_state_history(state,id)` returns all rows or an explicit error.
- `cli_state_recent_history(state,id,limit)` returns the newest ascending
  window, retrying a smaller newest window only on resource status 13.

Every successful history document has `messages`, `total_messages` and
`offset`. The recent API is presentation-only. Strict APIs never halve a
window, discard an old unit, start from a guessed tool result or return a
successful prefix. Invalid JSON remains an error, not a reason to hide rows.

## Bounds and backpressure

SQL byte lengths are inspected before allocating row Strings or parsing JSON.
Each query is bounded to 16 MiB encoded output and the existing 4096 JSON
node/link admission. More than 4090 requested rows is rejected before scanning;
rich rows may exhaust nodes earlier. JSON reservations use a window-specific
upper bound instead of reserving 16 MiB for every tiny snapshot. Resource
exhaustion fails 13. The legacy runtime's exact `json node limit exceeded`
diagnostic is normalized from 10 to 13 at the state boundary; malformed input
still fails 10. A newest single row exceeding admission remains an error.

Model context has separate 1000-message/786432-encoded-byte hard bounds,
including the current system message and retained checkpoint. Restore loads
the checkpoint first, validates `messages_seen` against the SQL count, checks
retained/tail counts, reads only the complete newer tail and validates complete
assistant/tool-result units. No UI recent window is used. Unknown pending tool
outputs pause through status 12 rather than being fabricated or replayed.

## Recovery and budgets

At 850 model messages, controller compaction triggers even below byte/token
thresholds. This leaves room for the existing maximum 128-result batch before
the structural ceiling. The existing complete-unit summary procedure and
provider request path are reused. Successful checkpoints record SQL public
count, even when full public history cannot fit one JSON document. Their
canonical retained messages and every newer row rebuild the next context.

Summary requests use the same GoalState, scheduler reservation, reported usage,
retry limits and persistence. Queries and restore do not reset counters. A
failed limit/summary leaves the public transcript intact; an old oversized
uncheckpointed history fails 13 with an explicit new-session diagnostic.

## Security and compatibility

No credentials, provider configuration or user directories are read by tests.
The integration fixture uses loopback HTTP and a unique generated temporary
Credential Manager entry, removed on both ordinary success and failure. Tool
payloads remain untrusted history. Existing schema 1 summaries and schema 2
checkpoints retain their representations. No runtime symbol, manifest, lockfile
or storage schema changes are required.
