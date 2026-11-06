## ADDED Requirements

### Requirement: Ordinary read errors are model-visible tool results

The native controller SHALL persist and return ordinary no-side-effect
built-in read failures as `is_error` tool results without pausing the agent.
It SHALL retain the error code, call identity and a useful correction hint.

#### Scenario: A directory path is rejected

- **WHEN** a built-in directory read rejects an absolute or out-of-workspace path
- **THEN** its error result SHALL be returned to the model under the original call ID
- **AND** a corrected new call SHALL be allowed within the unchanged policy
- **AND** reusing the completed call ID SHALL reuse its recorded result without execution

#### Scenario: Parallel safe reads include an error

- **WHEN** one hardened Git read settles with an ordinary error
- **THEN** unrelated safe reads SHALL still settle and publish in declaration order
- **AND** the process lease SHALL remain owned until its tree is quiescent

### Requirement: Uncertainty and control failures remain explicit pauses

The controller SHALL distinguish proof of no operation from an unknown
side-effect outcome. Cancellation, invalid ownership, exhausted resources and
unknown side effects SHALL NOT become ordinary recoverable read results.

#### Scenario: Editor preflight fails before mutation admission

- **WHEN** path or preview validation fails before entering checkpoint mutation
- **THEN** a no-operation error result MAY continue the model loop
- **AND** file contents and checkpoint mutation state SHALL remain unchanged

#### Scenario: A write or process result is unknown

- **WHEN** an admitted effectful tool returns an error without proof of no operation
- **THEN** its durable result SHALL identify the unknown outcome and pause execution
- **AND** the same call ID SHALL never execute automatically after resume
- **AND** a repeated call ID SHALL preserve the pause instead of implying successful recovery

#### Scenario: The user cancels a read

- **WHEN** cancellation is received while a read is executing
- **THEN** the controller SHALL clean up owned work and stop the batch
- **AND** it SHALL NOT send another model request as ordinary error recovery
