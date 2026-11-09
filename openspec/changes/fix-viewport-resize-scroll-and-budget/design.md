# Lifecycle and recovery

Viewport invalidation forces every row to be drawn, resets VT origin/margins
and erases the viewport before reconstruction. Row-reuse is valid only for the
last successfully delivered frame with matching dimensions. Terminal frame
admission checks live geometry before/after writing; races invalidate rather
than retaining an undelivered cache. Height-only changes preserve cached wrapping.
Repeat a recovery paint after the last resize settles, including transient
minimization and same-size invalidation; idle resumes zero-write behavior.

History remains represented by stable wrapped rows and message identities.
Wheel input is processed at bounded frame cadence, with overlap reuse only for
unchanged viewport content. Generic handle freelists avoid scanning retained
transcript objects during temporary allocation. Stale generation checks remain.

The composer gap contains a centered muted `▾` only when viewing older history.
Click is consumed before selection/expansion/composer hit testing; the next
frame follows the current tail and preserves draft, queue and permissions.
The header fits the workspace path with a reserved right-hand model/effort.
Plan/read/Vim indications remain separate visible state.

Budget admission and counters remain shared across parent, children, retries,
consultation and summaries. A pause includes actual requests/max and optional
token counts, explicitly retaining context and completed tools. Compaction
failure has its own stage; success never implies remaining execution budget.
Recovering an ordinary turn continues accepted context under a new turn budget;
Goal recovery preserves cumulative limits. No automatic side-effect replay.

The user subsequently removed the default request cap. Omission/zero means no
request-count limit for all entrypoints including background launch. Persisted
Goal mode adds `request_limit_explicit`; unmarked old 50 means legacy default
and is replaced by the current invocation default, without resetting counters.
Explicit new limits and non-default legacy limits remain recorded user choices.
This overrides the previous plan's implicit Goal-50 rule. Five retries per
failed request remain as separately requested by the user.
