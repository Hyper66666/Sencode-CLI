# Design

The initial request may be followed by at most five retries, each charged to
the existing budget. Retry429/500/502/503/504 before a stream, or transport
9/11/17 only when emission provably never began. Certificate errors remain
permanent. Preserve connection snapshots, tool ledgers and unknown-outcome
pauses. Backoff250/500/1000/2000/4000ms is cancelable and honors Retry-After
within a30-second aggregate wait ceiling. Budgets/cancellation can stop sooner.
Diagnostic metadata contains status, classified label, attempts and stop
reason, never credentials, URLs, headers or raw response bodies.

An additive `retry` event drives one transient row immediately above the
conversation activity. It does not append notices. Completion, cancellation
and a fresh turn clear the row; reader anchors survive its insertion/removal.

Sengoo's explicit budgets are used end to end in canonical context, checkpoint,
compaction, model identity and outbound encoding. Public/UI history keeps its
existing strict bounds. Canonical limits remain1000 messages/786432 encoded
bytes, with32768 nodes and automatic pressure relief before the row ceiling.
Context defaults to262144 tokens;80% uses the existing clearly labelled local
token estimate. A655360-byte safety trigger may compact earlier.

Maximum output defaults131072 tokens, configurable as `max_output_tokens`
in the existing schema1 context configuration, including model overrides.
Requests use max_completion_tokens (Chat), max_output_tokens (Responses),
max_tokens (Messages). Actual allowance is capped to estimated remaining
context with32 tokens of framing margin; it is an upper bound, not a promise
that a provider/model supports that capacity. No unsupported-provider fallback.
Absolute checkpoint cursors, complete tool units and cumulative budgets remain.
