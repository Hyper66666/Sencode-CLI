# Stable viewport resizing, long-history scrolling and compaction diagnostics

## Capabilities
Reconstruct the entire fullscreen viewport on invalidation and after geometry
races, retain message reading anchors, show a centered muted jump-to-latest
button in the composer gap and show the workspace path beside SENCODE.
Measure long-history wheel latency and improve generic Sengoo allocation where
retained history makes temporary handle allocation proportional to history.
Expose actual shared request/token limits at budget pause, distinguishing a
successful compaction from subsequent request-budget exhaustion.
Following the user's subsequent correction, remove the implicit 50-request
default everywhere and from unmarked old Goal checkpoints. Usage remains
accounted; only an explicitly supplied request/token budget can stop on counts.
Review the corresponding CC/Grok limits and document optimization priorities.

## Non-Goals
No automatic budget extension/reset, tool replay, history migration, engine
permission change or modifications to user configuration/history. Synthetic
fixtures, native console tests and live-history read-only evidence are distinct.

## Ownership
Integration owns CLI rendering, controls, diagnostics, fixtures and delivery.
Sengoo owns generic terminal frame admission and constant-time handle reuse.
