## ADDED Requirements

### Requirement: Preference saves share the safe native recovery boundary
Model and permission preferences SHALL persist for a lock-free abandoned SG
execution only when existing native recovery would admit that no-tool state.

#### Scenario: Resume an abandoned native turn
- **WHEN** the previous SG instance released its session lock without finalizing and has no pending tool or cleanup
- **THEN** both preferences can be saved by releasing only its stale active bit in the same transaction, preserving its ownership/fence/history; the next actual turn owns transcript recovery.

#### Scenario: Keep unresolved execution blocked
- **WHEN** the session is live, has cleanup or running tools, belongs to an active foreign engine, or has active meeting/fusion work
- **THEN** neither preference writer mutates its saved value.

### Requirement: Frontend retains busy selections until durable save
The frontend SHALL wait for worker readiness and retain a retryable pending model
or permission selection while servicing input.

#### Scenario: Retry a busy model selection
- **WHEN** the save returns busy before execution release
- **THEN** the frontend keeps the pending choice, retries after its bounded delay and preserves the current immutable request.

#### Scenario: Reject unavailable destination
- **WHEN** the session is missing or archived
- **THEN** saving fails without creating preference authority for it.
