## Why

Goal reaches finish_goal without --check, then pauses with generic tool error 12
and a misleading cancelled footer. The user wants the model to supply suitable
acceptance conditions when none were configured. Composer hints are too dense.

## Capabilities and ownership

- Sengoo controller: accept model-proposed executable checks as a fallback,
  run them under existing permissions, preserve evidence and resume state.
- Sengoo diagnostics/UI: distinguish verification pauses from tool failure or
  cancellation; show a compact permission line with focused contextual hints.

## Non-Goals

No automatic completion from model assertions, replacement of configured checks,
permission escalation, replay of uncertain tools, or background Goal execution.
No compiler/runtime ABI changes or user-history migration.
