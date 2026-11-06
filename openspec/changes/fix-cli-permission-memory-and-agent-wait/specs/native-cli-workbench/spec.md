## ADDED Requirements

### Requirement: Session permissions survive re-entry
The CLI SHALL restore a local session's last selected manual, automatic-edit or
full permission mode and explicit command authorization without changing Plan.

#### Scenario: Exit after changing permission without sending
- **WHEN** a user changes permissions and returns through resume or the picker
- **THEN** the footer and next request use the saved session selection
- **AND** switching sessions loads each destination's selection independently

#### Scenario: Selection races host startup
- **WHEN** permissions are changed immediately after opening a restored session
- **THEN** temporary startup contention retains the pending preference until it can be saved
- **AND** exiting or branching flushes it after owned process cleanup

#### Scenario: Submit contends with another executor
- **WHEN** a second execution host cannot save its submit policy because the session is owned
- **THEN** that submit receives a structured failure without stopping the host or starting tools
- **AND** its unaccepted request ID can execute after the session becomes idle

#### Scenario: Permission change during execution
- **WHEN** permissions are changed while a turn is active
- **THEN** the running request and current approvals keep their captured policy
- **AND** the new selection is saved after execution and cleanup release ownership

#### Scenario: Overrides and untrusted history
- **WHEN** explicit permission flags are supplied or independent history is imported
- **THEN** explicit flags override stored selections and untrusted history cannot grant execution permissions
- **AND** missing metadata uses manual approval without changing saved model targets or budgets

### Requirement: Child waits and capacity are not budget failures
A bounded child wait SHALL return its caller to runnable state. Temporary model
capacity exhaustion SHALL wait while processing children and control input.

#### Scenario: Slow children outlive wait timeout
- **WHEN** one or two healthy children run past a wait_agents timeout
- **THEN** the parent continues when a model slot is available and children finish normally
- **AND** no code 12 or budget diagnostic is generated for scheduler backpressure

#### Scenario: Cancellation and actual budget exhaustion
- **WHEN** the user cancels during capacity waiting or the shared request budget is exhausted
- **THEN** cancellation remains responsive, child resources are cleaned up and a genuine budget failure remains distinguishable
- **AND** waiting alone consumes no request and completed tools are not replayed

### Requirement: One assistant heading per user turn
The transcript SHALL show one SENCODE speaker heading for the assistant's response
to each user message, regardless of tool and streamed segment boundaries.

#### Scenario: Multi-step response and restored history
- **WHEN** an answer contains text, tools, children, notices and more text
- **THEN** chronological content remains intact with only its initial assistant heading
- **AND** history restore, reflow and scrolling retain that grouping
- **AND** the next user message permits a new assistant heading
