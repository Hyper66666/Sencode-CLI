## ADDED Requirements

### Requirement: Completed commands are not expired by delayed observation
The Sengoo executor SHALL observe process and tree completion before deciding
deadline expiry, using monotonic elapsed time.

#### Scenario: Completed process observed after its deadline
- **WHEN** a command and all descendants have already exited before a delayed poll
- **THEN** buffered output is drained and returned without a fabricated execution timeout
- **AND** exit code and complete cleanup remain required before lease release

### Requirement: Owned descendants and direct exit have distinct diagnostics
Command output SHALL distinguish timeout, cancellation and direct process exit
through additive compatible result metadata.

#### Scenario: Shell exits successfully while a descendant is still running
- **WHEN** the deadline expires before the owned process tree becomes quiescent
- **THEN** the executor stops and reaps that tree and reports a descendant timeout
- **AND** direct exit 0 is not displayed as successful command completion

### Requirement: Script display preserves command boundaries and decisive errors
Command cards SHALL identify multi-line scripts and preserve a bounded expandable
script preview together with beginning and end of command diagnostics.

#### Scenario: Later command fails after a successful search
- **WHEN** the first line runs rg and a later compiler command fails
- **THEN** the card identifies the full script rather than blaming rg alone
- **AND** the end of stderr remains visible when warnings exceed the preview

### Requirement: Explicit PowerShell uses a system installation
Explicit PowerShell SHALL prefer installed PowerShell 7 with Windows PowerShell
fallback, without workspace interpreter shadowing or changing the default Bash.

#### Scenario: Modern and legacy shell availability
- **WHEN** a noninteractive PowerShell command is requested
- **THEN** an available system PowerShell 7 is selected before the legacy shell
- **AND** Unicode I/O, explicit exit status, permission and process ownership are preserved
