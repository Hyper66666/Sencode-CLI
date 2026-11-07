## ADDED Requirements

### Requirement: Bounded and visible network recovery
Native requests SHALL expose sanitized HTTP/transport errors and allow at
most five retries after the initial attempt when replay evidence is safe.
Owner: integration agent.

#### Scenario: Retryable rejection or pre-send TLS failure
- **WHEN** HTTP502 is received before streaming or TLS17 occurs before send
- **THEN** the host retries within wait/budget bounds and attributes each attempt
- **AND** one reconnect row appears above Working without transcript notices

#### Scenario: Unsafe replay or cancellation
- **WHEN** a stream/send is ambiguous, a certificate fails or the user cancels
- **THEN** unsafe replay stops and terminal diagnostics retain the real cause
- **AND** cancellation and completion clear transient presentation

### Requirement: Default context and complete structured continuation
Native context SHALL default to262144 tokens, output to131072 and automatic
compaction to80% of locally estimated occupancy. Owner: integration agent.

#### Scenario: Rich history below context bounds
- **WHEN** structured history exceeds4096 nodes within explicit budgets
- **THEN** load, request encoding, compaction and restart preserve complete units
- **AND** public history and cumulative request/token budgets remain unchanged

#### Scenario: Output and trigger boundaries
- **WHEN** a request is encoded or occupancy crosses80%
- **THEN** the protocol receives its output-cap field within remaining context
- **AND** compaction starts at the configured threshold or earlier safety bound

#### Scenario: Capacity or summary failure
- **WHEN** admission or trustworthy compaction cannot succeed
- **THEN** execution pauses without truncating history or replaying tools
