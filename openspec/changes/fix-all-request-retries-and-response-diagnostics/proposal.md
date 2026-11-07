# All model request retries and response diagnostics

## Why

HTTP 200 currently masks a later protocol/transport failure. Saved screenshot
evidence proves error 10 but lacks the phase needed to distinguish truncation
from an invalid provider event. The user explicitly requests five retries for
every model request error, including partial streams.

## Capabilities

- Retry every native model request failure, initial attempt plus five retries,
  across the controller, children and consultation; cancellation and execution
  budgets remain authoritative.
- Replace provisional response text between attempts and retain completed
  tools without replaying them.
- Report and persist sanitized HTTP, SSE and provider failure phases.
- Normalize built-in batch writes to UTF-8 without BOM and CRLF, with the same
  content shown for permission review.

## Non-Goals

Changing credentials, repairing an external service, automatically rerunning
failed shell commands or changing user's Git identity. No managed-runtime
internal retry policy or schema migration.

## Ownership

One integration owner modifies the native Sengoo CLI. This change supersedes
the conservative partial-response retry policy in the completed
fix-cli-network-retry-and-context-capacity change under explicit user direction.
