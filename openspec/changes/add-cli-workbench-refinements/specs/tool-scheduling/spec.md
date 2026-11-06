## ADDED Requirements

### Requirement: Validated bounded tool dispatch

The native CLI SHALL schedule complete validated inputs, retain durable fenced
ledger and permission checks, and bound dispatch. Repeated stable call IDs SHALL
not launch duplicate work.

#### Scenario: A model repeats a stable ID with different arguments
- **WHEN** two calls in one batch have the same ID
- **THEN** batch admission fails without executing either call
- **AND** batches are bounded to 128 entries and one to eight parallel safe reads
- **AND** a durable completed call from an earlier batch can only reuse its saved result

#### Scenario: Preview arguments are incomplete
- **WHEN** streamed JSON is incomplete or required fields fail ToolSpec validation
- **THEN** it is not eligible for parallel execution
- **AND** normal tool validation produces a diagnostic without performing the operation

### Requirement: Read blocks and ordered exclusive barriers

Validated automatically permitted reads MAY overlap within a read block. Other
tools SHALL form ordered exclusive barriers. Executable hooks SHALL retain
serial admission; classification errors SHALL be conservative.

#### Scenario: Read read write read
- **WHEN** a batch declares two reads, a write and another read
- **THEN** the first two reads may be in flight together
- **AND** Git status/diff use polled process jobs while synchronous file reads yield between calls
- **AND** the write starts after both settle, and the last read starts after the write settles

#### Scenario: Executable hooks are configured
- **WHEN** the hook configuration sidecar is present or its status is uncertain
- **THEN** tools run through the existing serial hook/approval/ledger path
- **AND** a read tool does not gain a hook permission bypass

#### Scenario: An explicit predecessor fails
- **WHEN** an entry's earlier predecessor settles unsuccessfully
- **THEN** that dependent entry is skipped without execution
- **AND** unrelated reads may still finish

### Requirement: Progress and result order

In-flight jobs SHALL be polled fairly with bounded per-poll pipe reads. Progress
MAY be shown immediately. Final model tool results SHALL be persisted and
appended once in original call order, independent of completion order.

#### Scenario: Later read finishes first
- **WHEN** the second read completes before the first
- **THEN** the UI may show its completion
- **AND** model history receives the first result followed by the second

### Requirement: Cancellation preserves ownership until quiescence

Cancellation SHALL stop queued admission immediately and retain acquired write
permits until tool/provider cleanup and explicit quiescence confirmation. Live
canceled descendants SHALL remain pending and unreapable. Stable tool lease
tokens SHALL reject stale completions.

#### Scenario: A command has a living grandchild
- **WHEN** the command is canceled while a successor writer is queued
- **THEN** the successor stays blocked until direct-child and process-tree quiescence are confirmed
- **AND** a timeout, heartbeat expiry or unknown outcome does not release the write permit

#### Scenario: A parent waits while a child is draining
- **WHEN** a canceled child still holds a tool lease or unreported provider request
- **THEN** the parent cannot resume or finish by ignoring that child
- **AND** a quiescent parent releases its model/write permits before waiting

### Requirement: Shared FIFO and execution cleanup

Writers SHALL queue by request arrival within their canonical workspace. Removing
a canceled queued writer SHALL not block its successors. A provider request
SHALL retain its capacity until completion/cancellation usage is reported.
The public synchronous process API SHALL not return a tool outcome while its
owned process tree can still mutate the workspace; I/O failures SHALL terminate
and poll owned cleanup before returning the original error.

#### Scenario: Direct child exits before its descendants
- **WHEN** the root process exits and a descendant keeps running
- **THEN** the job stays live until the entire owned process tree settles
- **AND** no final result or write-permit release is inferred from root exit alone

#### Scenario: Pipe output exceeds its bound
- **WHEN** stdout or stderr exceeds the configured capture limit
- **THEN** additional output is drained without unbounded allocation
- **AND** the final result identifies truncation after tree cleanup
