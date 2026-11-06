## ADDED Requirements

### Requirement: Level-one children SHALL progress asynchronously in Sengoo

Starting a child SHALL capture its session, canonical cwd, connection, model,
credentials and independent context, then return a stable id without waiting
for a provider. List, poll, bounded wait and cancel SHALL operate on these ids.
The shared scheduler SHALL enforce global and per-connection limits; waiting
parents SHALL release model and write permits. Every actual request and usage
report SHALL consume the same root Goal budget exactly once.

#### Scenario: Five children share three connections

- **WHEN** five children include three on one connection and the default limits
  are four global and two per connection
- **THEN** four real provider streams progress concurrently and the fifth queues
- **AND** reports retain their captured session, connection and model
- **AND** credentials do not appear in reports or events

### Requirement: Child tools SHALL remain controlled by inherited host authority

Explore, Plan and children of Plan SHALL advertise only read-only tools. Every
received tool request SHALL be checked again, including unadvertised requests.
Children SHALL not spawn descendants, write the parent plan, invoke MCP, ask
the user or finish the parent Goal. Writable tools SHALL require a canonical
cwd FIFO permit before host execution. Completion SHALL match the claimed call
id exactly once; the controller SHALL retain permission and durable-ledger gates.

#### Scenario: A read-only child requests unauthorized operations

- **WHEN** a provider requests write_file, spawn_agent or write_plan
- **THEN** the child receives a denial as tool context without executing it
- **AND** the child can continue its independent request and report the denial

#### Scenario: Two approved children write in one workspace

- **WHEN** both children request a writable file tool
- **THEN** the second accepted tool waits for the first cwd permit to release
- **AND** a mismatched or repeated completion cannot advance the task

### Requirement: Cancellation SHALL drain real child resources

Canceling a child or parent, or exhausting the shared budget, SHALL close active
streams and account observed usage. Canceled parents SHALL continue to permit
cleanup polling. Events SHALL expose request starts, text deltas, accepted turns,
usage and terminal status for host persistence. Pending tool work SHALL return
to the controller; bounded wait SHALL not execute it implicitly.

#### Scenario: Root budget is exhausted with children active

- **WHEN** the next child would exceed the root request budget
- **THEN** queued requests never start and active requests are canceled
- **AND** local native stream handles and workers return to zero
