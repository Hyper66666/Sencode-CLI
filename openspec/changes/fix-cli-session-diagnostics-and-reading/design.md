# Design

The Sengoo execution host remains the single state owner. I/O workers do not receive JSON, SQLite or agent state. The desktop only changes the shared session projection; no runtime or WebView execution is duplicated.

## Storage and recovery
Schema 29 and project archive v2 keep their table shapes. Session creation atomically writes bounded `shared_modes.session_origin` metadata. Branches reset their origin and imported history preserves only the validated, non-executable origin fields alongside the existing paused-Goal allowlist. Legacy child classification requires exact same-project ledger or subagent-run evidence. Public resume filtering precedes pagination; internal host membership still accepts its newly created empty session. Title updates and message insertion share a transaction and preserve user ownership.

Elapsed time is measured with a monotonic clock. Terminal metadata is attached to the current execution's existing shared-history row under the execution fence. It does not change model content or resume work. Replayed history renders a static duration, never a live spinner. Session locks, fencing, tool ledger deduplication and cleanup-before-handoff remain authoritative.

## Events and diagnostics
Provider activity is a bounded enum; hidden reasoning text is neither displayed nor added to diagnostics. Explicit protocol reasoning activity produces `thinking`; text/tool work produces `working`. Existing `phase` events carry this state. Child envelopes carry `kind=phase` with `value.phase`. Terminal results add `elapsed_ms` and a structured diagnostic while retaining their existing fields and codes. Frontends ignore unknown optional fields. A private host diagnostic record tracks stage and correlation IDs without storing commands, keys or raw provider bodies.

Ordinary command exits return results to the model. Unknown tool outcomes, ownership loss and incomplete cleanup still pause without replay. Error code 20 alone does not identify its cause. Lossy command decoding replaces malformed UTF-8 subsequences and reports loss instead of discarding valid prefixes. Explicit PowerShell execution sets only that child's encoding.

## Presentation
One projection classifies consecutive read/list/search tools, supplies counts and stable fold identities, and drives both rendering and hit testing. Non-reading actions break groups; failures remain visible. The input owns its keys unless a modal or explicit fold shortcut consumes them. A physical spacer row separates history from the composer.

Renderer-owned spans carry semantic styles through Unicode wrapping; provider ANSI is never executed. Frame comparisons include spans. Stable unchanged rows and cursor state produce no terminal writes. Activity ticks affect visible activity rows only. The default palette adds semantic color while keeping image chips blue and honoring NO_COLOR/dumb output.

Diff construction is bounded and cached outside repaint. Line edits generate multiple hunks with three context lines; unified text remains the compatibility surface. The UI projects a file header, gray single-column line numbers, red deletions and green additions without row backgrounds. Exhausted work limits are explicit rather than claiming a precise minimal change.
