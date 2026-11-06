## ADDED Requirements

### Requirement: Inspect Git worktrees through bounded owned jobs
The CLI SHALL expose explicit-user worktree inspection through cancellable piped Git jobs with bounded output, NUL-safe framing, stable capability failures and no model-tool registration.

#### Scenario: Missing Git or repository
- **WHEN** Git is unavailable or the selected directory is not a nonbare checkout
- **THEN** inspection returns an explicit unsupported capability and starts no mutation

#### Scenario: Large or cancelled inspection
- **WHEN** output exceeds its bound or the user cancels a running Git query
- **THEN** the owned process is terminated and reaped and a terminal bounded failure is reported

### Requirement: Require an exact approved creation snapshot
The CLI SHALL require fresh explicit approval for the exact source identity, HEAD, destination and optional branch, preserve existing edits and disable configured hooks, filters and automatic network retrieval.

#### Scenario: Detached or exact branch creation
- **WHEN** the user confirms creation at a new local path
- **THEN** Git creates a detached checkout from the captured HEAD or the exact explicitly supplied new branch without resetting another branch

#### Scenario: Hostile repository configuration
- **WHEN** repository config declares executable hooks or clean, smudge, process or required filter drivers
- **THEN** inspection and approved creation override those drivers and do not run their commands

#### Scenario: Stale or constrained request
- **WHEN** the source identity or HEAD changed, approval is absent, Plan is active or a child policy attempts creation
- **THEN** the job refuses mutation and requires a fresh approved snapshot

### Requirement: Remove only an idle clean secondary checkout
The CLI SHALL remove only an explicitly confirmed clean registered secondary worktree through Git without force, while holding repository, workspace and relevant session leases and preventing new shared execution writes.

#### Scenario: Dirty or protected checkout
- **WHEN** the target is primary, current, locked, prunable, contains tracked changes or untracked files, or crosses a reparse component
- **THEN** removal is refused and all existing files and edits remain intact

#### Scenario: Shared execution owns a target
- **WHEN** a target session lease is held or shared state has an active or cleanup-required execution, Meeting or Fusion
- **THEN** removal is refused without clearing that execution or relying on elapsed heartbeats

#### Scenario: Git mutation fails or is cancelled
- **WHEN** creation or removal has started and fails or is cancelled
- **THEN** the result marks that refresh is required, cleans the owned process and never retries, force-removes or recursively deletes the target

### Requirement: Expose explicit management commands
The CLI SHALL expose worktree list, create and remove management commands with an exact preview, fresh terminal approval or explicit per-operation --yes; Plan SHALL still reject mutations.

#### Scenario: Redirected mutation lacks approval
- **WHEN** create or remove runs without a terminal and without --yes
- **THEN** it exits unsuccessfully with an explicit approval diagnostic and starts no mutation

#### Scenario: Explicit exact operation flag
- **WHEN** the user supplies --yes for create or remove
- **THEN** approval is bound to that freshly inspected exact operation and grants no future or model-tool permission

#### Scenario: Plan with yes
- **WHEN** --plan and --yes are supplied to a mutation
- **THEN** the mutation is refused before it starts

### Requirement: Integrate worktree jobs without blocking the fullscreen owner
The fullscreen application SHALL poll explicit worktree jobs between input
events, permit them only from the idle primary interactive owner and keep
queued requests paused until an explicit queue resume. Creation and removal
SHALL use one literal absolute path and a one-use immutable preview; the
fullscreen entry SHALL create detached checkouts without changing the session
working directory.

#### Scenario: Preview receives old input
- **WHEN** keystrokes were queued before a worktree preview becomes visible
- **THEN** those keystrokes are discarded before opening its default-Cancel selector
- **AND** a fresh selection and confirmation are required for mutation

#### Scenario: Other actions compete with a local job
- **WHEN** a worktree job or its confirmation owns the interface
- **THEN** model dispatch, session and connection changes and user-terminal launches cannot overtake it
- **AND** the composer can retain edits or queue tasks without writing shared state

#### Scenario: Foreground exit races with Git
- **WHEN** the user cancels or exits while a worktree process is active
- **THEN** its whole owned process tree is stopped and verified before releasing its reservation or normal foreground handoff
- **AND** unknown cleanup latches a blocked interface until process exit
