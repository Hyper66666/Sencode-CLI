## ADDED Requirements

### Requirement: CLI protocols share SDK implementation
The CLI SHALL use the same Provider and stdio MCP protocol implementations as
independent Sengoo SDK consumers, retaining its host-owned policy and state.

#### Scenario: SDK change is consumed
- **WHEN** a provider stream or MCP operation runs in the CLI
- **THEN** the shared package performs framing and protocol parsing
- **AND** CLI controls, approvals, cancellation, result persistence and tool de-duplication remain in force

#### Scenario: Evidence is recorded
- **WHEN** a candidate is accepted
- **THEN** its source identity includes the SDK dependency graph and native runtime inputs
- **AND** each supported flow has executable checks against that candidate

### Requirement: CLI policies share embeddable Agent contracts
The CLI SHALL consume sgagent's common permission, scheduling, write admission,
question, tool-contract and retry policies without replacing its execution host.

#### Scenario: Existing host behavior is retained
- **WHEN** a CLI tool, question, write task, Goal policy or retry is evaluated
- **THEN** the shared package provides the pure policy and validation behavior
- **AND** CLI approval presentation, state transactions and execution locks retain control
