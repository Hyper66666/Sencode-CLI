# Ownership and recovery boundaries

The Sengoo coordinator remains the only owner of agent history, scheduling,
Goal accounting, permissions and SQLite execution fences. A native worker only
owns DNS/TLS and byte transport. One immutable connection/model snapshot is used
through every attempt. Managed-account processes retain their explicit backend
policy and are outside native retry and auto-compaction.

## Retry lifecycle

Each attempt reserves the same shared request budget, receives its own stable
request ID and records provider-reported usage or unavailable usage. It ends in
accepted, failed or canceled before the next attempt starts. At most three
attempts and thirty seconds of aggregate backoff are permitted. Backoff polls
cancel and children; it does not hold a model or write permit. HTTP 429 and
500/502/503/504 may be retried only before any SSE event. A transport error may
be retried only if the worker certifies request emission never began. Ambiguous
send failures, authentication/validation failures, cancellation and streams that
already began fail explicitly. Retry-After delta seconds and IMF-fixdate are
honored; malformed or over-bound delays stop instead of retrying early.

No failed logical turn, child or tool call is restarted automatically. Existing
durable submit and tool IDs remain the authority across reconnects and crashes.

## Context lifecycle

Configuration is bounded `.sencode/context.json` schema 1 with defaults plus
exact connection/model overrides. Local occupancy is labeled an estimate,
separate from provider-reported token usage and remaining quota. The policy
also caps serialized request bytes so a large declared model window cannot
exceed the native parser/transport limit. Compaction operates on complete
assistant/tool-result units; unresolved, unmatched or duplicate tool IDs cannot
be cut. The original public transcript is never deleted or rewritten.

A summary request uses the shared scheduler and Goal object. Recent complete
units and the current user task remain verbatim in the active context. A fenced
context checkpoint stores the summary, retained structured messages and public
history cursor atomically. It is installed only after a valid nonempty summary
and a reduced context pass bounds checks. Failure pauses execution and leaves
the previous checkpoint valid. A typed notice identifies automatic compaction.
Counts and usage are never reconstructed from shortened history.

## Responses continuation gate

Only public documented Responses schemas may justify support. Encrypted
reasoning and other continuation items are opaque provider data, never parsed
as instructions or reconstructed from text. Canonical completed output is
validated against typed host tool calls before any tool is executed. Unsupported
item kinds or missing required continuation state keep the existing explicit
refusal. Fixtures do not claim a paid live-service result.

## Security and delivery

Provider credentials stay in memory and the credential manager. Attempt records
and notices contain identities/status/usage provenance, never request headers
or raw error bodies. Configuration cannot increase tool permissions. A fixture
candidate precedes integration into the installed binary, and the managed
runtime acceptance suite must remain green.
