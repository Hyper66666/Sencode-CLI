## Replacement

Patch the selected top-level member using SQLite JSON functions within the
fenced transaction. Load only the requested member into a Sengoo JSON document.
This removes both the replacement's unreachable old nodes and the aggregate
coupling between unrelated request/undo/context fields. Keep per-field JSON
bounds and a 16MiB combined-state byte bound; do not enlarge the JSON arena or
discard data. Keys are bounded identifiers and cannot inject JSON paths.
Permission/model loading uses the same per-field read. Branching copies state
and resets its designated fields within SQLite; portable import projects only
the already-allowed target/origin/Goal members before Sengoo validation. The
existing duplicate-origin rejection remains in place. Stored format, execution
fence and transactional snapshot/changelog flow remain compatible.
A genuine capacity failure remains a failure; never truncate unrelated modes.
Older running network-attempt evidence is classified as interrupted after a new
fenced execution has established quiescence. It is never upgraded to accepted,
and current-execution running entries remain protected by the retention bound.
Replacing an existing attempt never evicts another entry. New attempts evict
only the oldest settled/predecessor record; a journal of 256 live requests
refuses admission without changing the evidence.

## Continuation

After claiming the session, assemble complete bounded context and validate its
structure. Only a trailing unresolved assistant batch may be reconciled. Copy
exact completed ledger results that lack a public result. Calls never admitted
to the ledger receive an explicit not-executed interruption result, never a
success result or an execution. Uncertain/running/interrupted ledger entries
remain paused and block recovery. Validate every missing result before writing
any, and validate the resulting context before the next model request.

Raw history loading remains read-only and strict. An ordinary new user turn can
perform reconciliation with current execution authority. Preserve canonical
Responses items, already visible answers, tool outputs, budgets and deduplication.
The failure cleanup path also performs this reconciliation before releasing
execution authority, unless cleanup or a tool outcome remains unknown. Recovery
reserves never-admitted call IDs directly as terminal ledger records so a later
duplicate ID cannot execute them. Recovered terminal tool events use stable IDs.

## Failure boundaries

Classify failures while recording request evidence as request-state failures.
Do not call them provider rejection. A previously committed assistant response
does not authorize any tool until its normal validation/approval/claim path.
Cancellation and process cleanup retain their existing behavior.

## Verification

Reproduce the node limit with synthetic 134-attempt state. Test replacement
through the 256-entry retention boundary and stale fences. Cover unclaimed,
completed and uncertain trailing calls, user cancellation, restart, all three
wire formats and no duplicate side effects in isolated real-host fixtures.
Retain source/build hashes, installation evidence and a matching rollback package.

## Reference findings

Claude Code's `query.ts` drains remaining tool results after abort. Its
`StreamingToolExecutor` supplies explicit errors for queued/aborted tools, and
`ensureToolResultPairing` in `utils/messages.ts` guards the next API request.
Grok Build's `repair_dangling_tool_calls_with` in `conversation.rs` repairs only
unanswered calls. Its chat-state actor repairs at write boundaries and checks
integrity before building a request; `live_cancel_after_partial_tool_results_repairs_remaining`
tests retaining an already completed result. Its mid-turn injection tests warn
that repairing a still-live tool would create duplicate results and poison the
session. Consequently Sencode repairs only under the fenced owner at stopped
turn/new-turn boundaries and uses the durable ledger for actual completion.

These are architectural references. The implementation remains Sengoo and keeps
Sencode's stricter refusal to invent outcomes for uncertain native side effects.
