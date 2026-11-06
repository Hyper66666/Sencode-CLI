# Session reliability and readable native CLI output

## Why
CLI sessions retain placeholder titles, public recovery lists mix empty and child sessions, command decoding discards usable output, and generic failures obscure the execution boundary. Reading cards and coarse diff rendering make ordinary coding work difficult to follow.

## Capabilities
- Reliable first-message titles and public-session recovery, with portable non-executable child provenance.
- Classified execution diagnostics, loss-tolerant command output and preserved no-replay boundaries.
- Consecutive exploration groups, provider-backed activity, persisted elapsed time and semantic span rendering.
- Bounded multi-hunk diffs matching the approved single-column reference.

## Non-Goals
No schema migration, history deletion, provider fallback, new permission mode, renderer dependency, public release, or fresh-VM qualification. Existing raw and JSON output contracts retain their fields and numeric status codes.

## Dependencies and ownership
Integration owns event contracts, Provider/controller activity, recovery entrypoints and candidate acceptance. Session owner owns CLI storage and desktop persistence compatibility. Execution owner owns command diagnostics and the sibling Sengoo lossy-decoding/monotonic-clock capability. Presentation owner owns native TUI and diff projection. Existing project-history, request-recovery and mode-controls invariants remain required.
