## Why

Plan currently latches across replies and is restored from session metadata.
The user wants planning read-only to constrain one conversation turn, then exit
after completion, cancellation or abnormal interruption.

## Capabilities

- Scope Plan to one submitted turn, preserving captured child policies.
- Clear the frontend and execution host flags on every terminal outcome.
- Resume sessions without reviving historical or crashed Plan selections.

## Non-Goals and ownership

No change to saved manual/auto/full permissions, tool approvals, Goal semantics,
plan files, execution fencing or cleanup guarantees. Sengoo policy/controller
owns runtime enforcement; engine/frontend/main own turn and session boundaries.
