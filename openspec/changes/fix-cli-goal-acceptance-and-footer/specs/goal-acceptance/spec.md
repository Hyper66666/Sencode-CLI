## ADDED Requirements

### Requirement: Executable model-proposed acceptance
When no configured acceptance exists, the host SHALL accept bounded executable
checks proposed by the model and SHALL require actual successful execution.

#### Scenario: No --check configured
- **WHEN** finish_goal supplies valid checks for an active Goal
- **THEN** the host persists their model origin and executes them under the current command policy
- **AND** completion requires all checks to exit successfully

#### Scenario: Configured checks
- **WHEN** the user or a resumed Goal already has checks
- **THEN** a model proposal cannot replace or weaken them

#### Scenario: Missing or invalid proposal
- **WHEN** the model omits checks or supplies invalid commands
- **THEN** the tool gives a recoverable correction request without claiming completion

### Requirement: Truthful paused state
The host SHALL preserve failed verification evidence and SHALL distinguish a
verification pause from cancellation and uncertain tool outcomes.

#### Scenario: Repeated failed acceptance or denied permission
- **WHEN** unchanged checks fail twice or command approval is denied
- **THEN** Goal pauses with its specific reason and remains explicitly resumable
- **AND** budgets and saved checks do not reset

### Requirement: Compact focused composer footer
The footer SHALL retain current permissions and show only relevant action hints.

#### Scenario: Idle composer
- **WHEN** no overlay or actionable notice is active
- **THEN** the footer omits full shortcut lists and duplicate readiness labels

#### Scenario: Approval or selection
- **WHEN** an overlay owns keyboard focus
- **THEN** its concise hints take priority without hiding the permission selection
