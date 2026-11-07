Current defaults and diagnostics: [Network and context recovery](network-context-recovery.md).

# Native request recovery and context limits

The API coordinator retries HTTP 429/500/502/503/504 before stream output, or a
terminal connect/timeout/TLS-handshake failure only when the transport proves it never
attempted an application write. The initial attempt plus at most five retries and 30 seconds aggregate
backoff apply. Valid bounded Retry-After seconds and HTTP dates are honored;
over-bound or malformed delays stop. Cancellation stays available in backoff.
Every attempt has its own ID and consumes the same request budget. Provider
usage is distinguished from unavailable usage. There is no silent provider switch.

Already emitted streams, ambiguous send failures and side-effecting tool calls
are not replayed. Parallel child/consult sampling still reports its first error;
it does not inherit coordinator retries. Managed engines own backend recovery.

Automatic compaction uses a local byte-based occupancy estimate, not provider
quota. Optional `.sencode/context.json` is strict schema 1:

```json
{
  "schema": 1,
  "models": [{
    "connection": "custom-id",
    "model": "model-id",
    "context_window_tokens": 32768,
    "threshold_percent": 85,
    "max_input_bytes": 131072,
    "target_percent": 50,
    "min_summary_chars": 500,
    "min_reduction_percent": 20
  }]
}
```

The same numeric fields at the top level provide workspace defaults. Default
window is 262144, threshold80%, target occupancy 50%, and serialized input
ceiling655360 bytes. Exact connection/model overrides take precedence.
Existing schema 1 documents remain readable; an explicit older 80% threshold is
honored, while omitted fields use the current defaults. If an older trigger is
50% or lower and no target was declared, the target adapts to half the trigger,
clamped to 1%. The legacy 1% trigger uses an implicit 1% target; explicit targets
must always be below the trigger. Unknown fields,
duplicate selected targets and invalid limits are rejected. A declared window
is a user input; the CLI does not assert the model actually supports it.

Compaction selects the recent tail by serialized size, keeping complete
assistant/tool groups and the current true user task. Unresolved, duplicate or
orphaned tool calls cannot be cut. Exact source hashes reject stale summary
results, including same-count edits. Original system/project instructions remain
unchanged. A summary is explicitly marked as historical context, so it cannot
become the newest user task during a later compaction cycle.

The summarizer carries forward prior continuation facts, changed paths,
decisions, verification evidence, unresolved work and uncertain side effects.
Leading drafting and wrapper tags are removed; quoted control tags are
neutralized without discarding real sections. By default a summary must contain
at least 500 Unicode scalars, fit its planned byte cap, and reduce serialized
history by at least 20%. A result still over the active trigger is rejected.
Insufficient quality pauses the Goal; there is no automatic quality retry.
An explicit retry is a new budgeted request. Manual `/compact` can reduce a
history below the automatic trigger but still requires a reducible old prefix.

Public history remains intact. A fenced context checkpoint stores a summary
plus structured tail and cursor before the active owning JSON document is
replaced. Each successful replacement uses a fresh document arena. Internal
summary requests consume the same Goal request budget and provider usage
accounting but do not appear as public assistant messages or text deltas.
`compacting` and `thinking` phase events drive separate frontend progress.
A failed summary preserves the previous checkpoint. Reopen does not reset
accumulated requests. See [compaction design and evidence](context-compaction.md).

These rules apply to the native API engine. Managed engines own their context
and advertise their own compaction capabilities. The local estimate is not an
exact model tokenizer; 50% is a selection target, not a guaranteed exact output
token count. There is no imported Sencode memory-engine recovery state or
automatic synthesis of missing tool results.

The current Responses adapter rejects reasoning/tool continuation it cannot
preserve. It does not invent opaque reasoning items. Exact token-budget mode is
also refused until full accounting is available; request budgets are supported.
