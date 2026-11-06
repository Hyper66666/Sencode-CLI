## ADDED Requirements

### Requirement: Public recovery uses user-visible root sessions
The CLI and desktop SHALL preserve all stored conversations while excluding empty and positively identified child sessions from ordinary recovery before ordering and pagination. First-message titles SHALL share desktop Unicode rules and SHALL NOT overwrite user or branch titles.

#### Scenario: Empty and child sessions outnumber conversations
- **WHEN** a project contains more than 100 newer empty or child sessions and an older user conversation
- **THEN** ordinary recovery can still select that conversation by title or ID and the Agent view retains identified children

#### Scenario: Portable provenance and title ownership
- **WHEN** a project directory is renamed or its history is imported into a fresh catalog, or a session is branched or manually renamed
- **THEN** non-executable provenance remains valid, no child becomes a public root by copying metadata, and the chosen title survives subsequent messages

### Requirement: Failure classification preserves execution safety
The host SHALL preserve usable command output and distinguish known command failure from provider failure, cancellation, limits and unknown side effects. Existing status codes and no-replay guarantees SHALL remain valid.

#### Scenario: Correctable command failure
- **WHEN** a command exits nonzero with mixed valid and invalid UTF-8 bytes
- **THEN** its bounded result preserves valid output, reports decoding loss and permits a new model tool call without re-executing the completed identity

#### Scenario: Unknown outcome or incomplete cleanup
- **WHEN** a claimed side effect has no reliable terminal result or its owned process tree is not quiescent
- **THEN** the host pauses with a correlated reason and does not replay or hand off the execution
