## ADDED Requirements

### Requirement: Explicit native background ownership
The CLI SHALL run an explicitly requested native Agent in an independent bounded
Sengoo host while retaining the existing shared execution authority.

#### Scenario: Launcher exits
- **WHEN** a native job is durably admitted and its launcher exits
- **THEN** the supervisor MAY continue only under captured permissions
- **AND** the shared session lock and fence remain the only execution authority.

#### Scenario: Host crashes after admission
- **WHEN** the supervisor crashes before or after forwarding an accepted request
- **THEN** recovery SHALL NOT replay that request or any uncertain tool
- **AND** logs and public session history SHALL remain inspectable.

### Requirement: Authenticated bounded attachment
The CLI SHALL authenticate same-logon local IPC, verify PID plus process creation
identity, and allow at most one epoch-scoped control client.

#### Scenario: Observer tries to approve
- **WHEN** a read-only observer or a stale control epoch submits an approval
- **THEN** the supervisor SHALL reject it before any engine/tool side effect.

#### Scenario: Slow peer
- **WHEN** a peer stops consuming output
- **THEN** bounded peer buffers SHALL NOT stop draining worker stdout/stderr
- **AND** cursor recovery SHALL explicitly report any expired log range.

### Requirement: Foreground Goal and interaction authority
The supervisor SHALL pause Goal execution when controlling attachment is lost and
SHALL NOT retain replayable pending permission or question replies.

#### Scenario: Goal controller disconnects
- **WHEN** the controlling pipe closes during Goal execution
- **THEN** the worker and its children SHALL be cancelled
- **AND** Goal state/counters SHALL persist paused until explicit user continuation.

#### Scenario: Unattended permission request
- **WHEN** an unattended ordinary Agent requests permission or user input
- **THEN** the supervisor SHALL cancel and record interaction-required pause
- **AND** no answer or approval SHALL be fabricated.

### Requirement: Durable logs and certified stopping
The CLI SHALL expose bounded sequenced job logs and idempotent explicit stopping.

#### Scenario: Repeated stop
- **WHEN** stop is repeated for the same job
- **THEN** cancellation SHALL NOT repeat a tool or create new model requests
- **AND** completion SHALL NOT be reported before owned cleanup is certified.

#### Scenario: Operational sidecar
- **WHEN** the job registry is created or reopened
- **THEN** its schema SHALL remain separate from the shared transcript database
- **AND** registry state SHALL NOT grant session execution or bypass cleanup checks.
