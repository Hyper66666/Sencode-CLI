## ADDED Requirements

### Requirement: Diagnostics SHALL expose effective settings without raw secrets
Fullscreen config and doctor commands SHALL report allowlisted metadata, policy
and target sources. They SHALL NOT emit raw config JSON, environment variables,
API key values or official account credential files. Doctor SHALL distinguish
local readiness from a real provider request.

#### Scenario: A saved connection contains an unrelated secret field
- **WHEN** config and doctor views inspect its effective target
- **THEN** the target and setting source are visible but the secret is omitted
- **AND** preferences, credentials and existing sessions remain unchanged.

### Requirement: Instruction view SHALL disclose current memory scope
The memory view SHALL display bounded applicable AGENTS.md and CLAUDE.md content
and disclose whether persistent learned memory is implemented.

#### Scenario: The user inspects project instructions
- **WHEN** the fullscreen user submits the memory command
- **THEN** instruction sources and content are displayed read-only
- **AND** the command does not grant tools additional permissions.
