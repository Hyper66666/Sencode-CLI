## ADDED Requirements

### Requirement: Explicit bounded provider event structure
The native provider parser SHALL admit valid completion events exceeding 4096
nodes within an explicit 1 MiB and 65536-node budget, without retaining optional
usage metadata in conversation history or changing legacy JSON defaults.

#### Scenario: Rich Responses usage attribution
- **WHEN** an otherwise valid completion includes more than 4096 nodes of optional usage metadata
- **THEN** the answer, reported usage totals and tool continuation validate normally
- **AND** no retry occurs solely because the legacy JSON budget was exceeded

#### Scenario: Invalid or excessive event
- **WHEN** event JSON is malformed or exceeds an explicit byte or node limit
- **THEN** a closed diagnostic distinguishes invalid syntax from local resource limits
- **AND** no tool is authorized by that event and retry and cancellation policy remains unchanged

#### Scenario: Repeated parsing cleanup
- **WHEN** rich event documents are parsed repeatedly or fail admission
- **THEN** their transient JSON documents and reservations are released
- **AND** optional attribution is absent from retained history and diagnostics
