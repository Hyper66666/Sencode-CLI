## ADDED Requirements

### Requirement: No implicit request-count limit
All native CLI entrypoints SHALL have no request-count limit by default while
retaining shared usage accounting and optional explicit user budgets.

#### Scenario: Successful work exceeds fifty requests
- **WHEN** ordinary or Goal work and child/summary requests exceed fifty successful calls without an explicit cap
- **THEN** execution continues through compaction until completion, cancellation or another actual failure
- **AND** cumulative usage remains recorded without an automatic reset

#### Scenario: Legacy default Goal recovery
- **WHEN** a resumed Goal contains the unmarked old default limit 50
- **THEN** the new unlimited default applies and accumulated usage and acceptance evidence remain intact
- **AND** new explicitly configured limits remain distinguishable through export/import

### Requirement: Distinguish compaction success from budget pause
The host SHALL preserve shared budgets and show actual consumed/maximum request
counts and configured token counts when a budget pauses execution.

#### Scenario: Last budgeted request compacts context
- **WHEN** compaction succeeds but the shared request limit prevents the next model request
- **THEN** the checkpoint remains valid and the result states the exhausted budget with counts
- **AND** the UI shows a paused outcome and a continuation route, without calling it compaction failure

#### Scenario: Available budget after compaction
- **WHEN** a valid summary is installed and shared budget remains available
- **THEN** the next model request continues with that context without replaying completed tools

#### Scenario: Invalid summary or oversized retained unit
- **WHEN** compaction cannot produce valid bounded continuation state
- **THEN** the diagnostic identifies context reduction as the failing stage
- **AND** the previous checkpoint and public history are retained
