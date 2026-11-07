## Resolution

No target, or the same provider alone, inherits the running request's complete
owned snapshot, including effort, protocol, URL and image capability. Changing
saved defaults mid-request cannot affect it. A different explicit provider alone
selects that provider's configured default. Model-only requests search all
enabled providers. Explicit provider IDs or unique provider labels restrict it.

Exact model ID wins over exact label, then ASCII-case-insensitive exact ID and
label, then case-insensitive substring in ID or label. `terra` matches
`gpt-6.1-terra`. For the same model ID on several providers prefer the current
provider; otherwise return candidates. Distinct fuzzy matches require a choice.
Discovered-only models are excluded. Unavailable or managed-account targets
return a reason, with no native fallback.

## Lifecycle and permissions

Resolve before reading a credential, creating a child session, or reserving a
model slot. Unresolved targets are durable recoverable tool results, not host
failures; retry/deduplication, cancellation and shared budgets are unchanged.
Only the top-level agent receives list_models. It is a read-only Plan-safe tool.
Its allowlist excludes config JSON, database paths, URLs and secrets. Pages have
at most 64 entries; resolution returns at most 64 candidates and a total count.
Input is bounded to 512 providers, 256 enabled entries/provider and 256-byte
queries. The directory follows the existing per-provider snapshot bound;
over-limit provider counts and query/page arguments fail explicitly. Automatic
protocol selection uses the saved successful protocol at connection admission.
Invalid native protocols are diagnosed separately from managed accounts.
Configuration and credential errors before child admission remain recoverable.

## Identity and recovery

Append JSON-escaped host connection/model/effort/engine metadata to the first
system message in an ephemeral outbound history copy for native main, child,
compaction and consult requests. Keep original system text first. Managed
adapters receive configured-target metadata in their existing context envelope.
These facts describe the selected configuration, not upstream model weights.
Public history and compaction checkpoints do not persist this metadata; retries
and resume regenerate it from the selected snapshot without accumulation.
