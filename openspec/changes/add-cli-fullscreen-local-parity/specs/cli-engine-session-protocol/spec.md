## ADDED Requirements

### Requirement: Versioned frontend and execution events
The host SHALL accept bounded versioned commands and emit ordered events, keeping
connection snapshots, persisted execution authority and tool deduplication.

#### Scenario: Cancel running work
- **WHEN** a frontend cancels a streaming or tool-running request
- **THEN** the host processes cancellation, completes accepted tool lifecycles
  and confirms quiescence before allowing conflicting work.

#### Scenario: Frontend disconnect
- **WHEN** a foreground frontend disconnects
- **THEN** a Goal pauses and no ambiguous side-effecting operation is replayed.

### Requirement: Actual managed capabilities
Managed engines SHALL advertise actual policy and usage enforcement. Unknown or
unsupported enforcement SHALL not be presented as supported.

#### Scenario: Unsupported strict Goal
- **WHEN** an engine cannot count the requests required by the selected budget
- **THEN** strict Goal startup is rejected with a specific capability reason.
