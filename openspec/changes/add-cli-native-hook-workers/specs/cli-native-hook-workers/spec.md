## ADDED Requirements

### Requirement: Explicit fingerprint-bound local workers
The native CLI SHALL inspect and register bounded local worker manifests without
executing them and SHALL enable only explicitly reviewed manifest/executable
fingerprints through an independent registry.

#### Scenario: Project content discovers an executable
- **WHEN** repository instructions, a skill or provider output names a worker
- **THEN** the host SHALL NOT register, enable or launch it automatically.

#### Scenario: Reviewed bytes change
- **WHEN** a reviewed manifest or executable differs before invocation
- **THEN** the host SHALL deny launch until explicit review of the new bytes.

### Requirement: Host policy and fresh approval remain authoritative
Every worker launch SHALL require a current request-bound user approval and the
existing effectful-tool scheduling, execution fencing and process ownership.

#### Scenario: Plan or inherited read-only task
- **WHEN** an enabled hook matches a tool in Plan or an inherited read-only task
- **THEN** no worker SHALL start
- **AND** a mandatory before hook SHALL not be silently bypassed.

#### Scenario: Worker requests greater permission
- **WHEN** a worker returns continue or requests a host operation
- **THEN** continue SHALL not grant parent tool permission
- **AND** unsupported host calls SHALL produce no tool/model side effects.

#### Scenario: Stale or absent controller
- **WHEN** no fresh matching interaction reply is available
- **THEN** auto-edit, command grants and prior trust SHALL not authorize launch.

### Requirement: One bounded versioned invocation
The host SHALL exchange bounded UTF-8 JSONL with a fresh owned worker, validate
identity/version/phase and require exactly one terminal result plus clean exit.

#### Scenario: Invalid output or nonzero exit
- **WHEN** output is malformed, oversized, duplicated, stale or followed by failure
- **THEN** the invocation SHALL fail closed and the owned tree SHALL be cleaned.

#### Scenario: Input is too large
- **WHEN** a hook input exceeds its bound
- **THEN** the host SHALL reject before spawn instead of truncating the decision input.

### Requirement: Durable no-replay and certified cleanup
Invocation admission SHALL precede process creation and SHALL reuse shared
session/fence authority without migrating the shared schema.

#### Scenario: Duplicate or interrupted admission
- **WHEN** an admitted invocation is encountered after duplicate delivery or crash
- **THEN** no worker SHALL run automatically for that invocation again.

#### Scenario: Cancellation or descendant remains
- **WHEN** cancellation occurs or a worker leaves a descendant
- **THEN** the host SHALL terminate and reap its owned tree
- **AND** SHALL NOT report successful completion before quiescence is certified.

### Requirement: Hook ordering preserves tool truth
Before workers SHALL release their single cwd FIFO permit before the parent
tool obtains its own permit; after workers SHALL require a persisted known
parent result and confirmed cleanup.

#### Scenario: Before hook blocks
- **WHEN** a before worker returns block
- **THEN** the original tool SHALL not execute and its result SHALL name the veto source.

#### Scenario: Parent outcome is unknown
- **WHEN** parent execution or cleanup is uncertain
- **THEN** no after worker SHALL start and no parent operation SHALL be replayed.

#### Scenario: Hook fails during Goal
- **WHEN** a worker fails or needs unavailable approval
- **THEN** Goal SHALL pause with its existing counters intact and SHALL not be completed.
