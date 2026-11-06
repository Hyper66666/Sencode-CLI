## ADDED Requirements

### Requirement: Terminal job creation SHALL require explicit user approval
A host-owned terminal job SHALL require approval of its exact launch snapshot,
refuse Plan/child-policy creation, and remain absent from model tool dispatch.
The cwd SHALL resolve within the supplied workspace and reject reparse
components. Child environment SHALL include only an OS allowlist and explicit
user overrides, with no arbitrary parent/provider-secret inheritance.

#### Scenario: Plan or stale approval attempts to launch a shell
- **WHEN** Plan is active, approval is absent, or the approved snapshot changes
- **THEN** creation fails before a process starts or a workspace lock is taken

### Requirement: Terminal jobs SHALL retain shared write ownership through cleanup
Each job SHALL hold the shared workspace OS write lock from launch until the
entire owned job is quiescent and its direct child reaped. Direct-child exit
alone SHALL not release that lock. Cancel/Drop SHALL clean the job; unknown
cleanup SHALL retain the native lock until the owning CLI process exits.

#### Scenario: The parent shell exits while a descendant is still active
- **WHEN** the parent exits and its child continues holding the workspace
- **THEN** another model/tool/frontend writer cannot acquire the shared lock
- **AND** cancellation releases it only after the descendant exits

### Requirement: Terminal display transport SHALL remain bounded and explicit
Terminal read/write/resize/poll SHALL use the owning std::pty API. Display
storage SHALL retain at most 256KiB raw VT with dropped-byte accounting. The
module SHALL not print raw bytes, execute model tool requests or replay jobs.

#### Scenario: An interactive shell floods display output
- **WHEN** terminal output exceeds the retained display bound
- **THEN** storage remains bounded and callers can observe the dropped offset
- **AND** cancellation remains available and restores write ownership
