# Sencode CLI workbench refinements

## Capabilities

Deliver the requested monochrome dimensional SENCODE wordmark; a two-column
connection catalog showing every enabled model and a second reasoning-effort
picker; red/green code-change previews; animated thinking and compaction states;
desktop-aligned context reduction; and verified tool scheduling improvements.
Reproduce and repair the reported error 20 on a Chinese greeting without losing
the session or exiting the interactive workbench on recoverable turn failures.

## Non-Goals

No new cloud feature, account OAuth implementation or configuration companion
redesign. Existing managed-engine policy limitations remain explicit. Recovered
Claude source informs behavior only; no source is copied.

## Ownership and dependencies

Root owns frontend/TUI/rendering, diff, error recovery, controller/executor
integration, packaging and final evidence. Model owner owns the model/effort
contract and provider encoding. Compaction owner owns context reduction rules.
Scheduling owner owns cancellation leases and the batch schedule contract.
Children own their corresponding capability spec deltas and named tests.
This change depends on existing fullscreen host, shared-store, bounded transport
and project-local history contracts; it does not close their broader umbrellas.
