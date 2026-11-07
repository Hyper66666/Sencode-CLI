## Why

A long session can exceed the JSON arena's node limit while replacing request
attempt evidence, although the resulting state fits. A response committed before
this bookkeeping failure leaves unexecuted tool calls at the history tail, and
subsequent user continuation fails with code 12. Cancellation exposes the issue
but is not the capacity failure's cause.

## Capabilities and ownership

- Storage owner: isolate mode reads and transactional updates within SQLite so
  unrelated fields do not share one bounded Sengoo JSON arena; preserve the
  attempt journal's retention and live-request evidence.
- Controller owner: reconcile a structurally valid trailing tool batch from
  durable ledger evidence after acquiring execution authority, without replay.
- Diagnostics owner: distinguish request-state persistence from provider failure.
- Integration owner: isolate reproduction, test continuation/restart/no replay,
  and deliver the same validated candidate through both installed aliases.

## Non-Goals

No automatic tool re-execution, guessed success, user-history deletion, weakened
cleanup/fencing, credential changes, provider fallback or JSON ABI changes.
