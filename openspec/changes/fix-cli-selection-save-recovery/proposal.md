# Recover selection persistence after an abandoned native turn

## Capabilities

Align model and permission preference admission with the native worker's existing
no-pending-tool recovery boundary. Keep busy frontend selections pending until
the owned worker is ready and the preference write succeeds.

## Problem

The native turn can safely recover a lock-free abandoned SG execution with no
pending cleanup or tool work. Both preference writers instead call the stricter
`session_idle`, returning code 7 before the next worker can reach that recovery.
Frontend target writes also clear their pending bit before attempting the write,
and run before worker readiness. This produces repeated notices and loses the
durable selection despite the displayed choice changing.

## Non-Goals

Do not change request permission snapshots, execution fences, abandoned tool
takeover rules, imported history authority or provider behavior.

## Ownership

This child owns the shared preference admission helper and pending frontend save
state. Existing execution recovery continues to own actual claims and cleanup.
