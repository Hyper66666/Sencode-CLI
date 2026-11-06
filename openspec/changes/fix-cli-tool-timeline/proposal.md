# Native tool timeline and activity

## Capabilities

Keep assistant text and tools in event order, update each tool call in one card,
restore those cards from public history, and animate only visible running tool
headers. Keep image references blue and atomic. All projection, animation and
history logic is Sengoo. The native terminal remains a generic I/O boundary.

## Non-Goals

No provider request, tool replay, permission grant or database migration is
introduced by rendering. Plain and JSON output contracts remain unchanged.

## Ownership and dependencies

The integration owner owns this timeline and its native projection tests.
`fix-cli-recoverable-tool-results` owns the separate tool error policy.
Sengoo's bounded terminal polling repair owns OS event consumption. Independent
loopback and hidden-console fixtures qualify the combined candidate.
