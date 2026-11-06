## ADDED Requirements

### Requirement: Native file tools persist checkpoints before effects
Approved native writes and patches SHALL persist bounded exact before/after
intent before modifying a file. Interrupted operations SHALL not replay on open.

#### Scenario: Crash after file publication
- **WHEN** a prepared journal exists and the application reopens
- **THEN** current files remain unchanged until explicit user recovery.

### Requirement: Rewind verifies and confirms one file restore
Rewind SHALL require explicit fresh confirmation, exclusive execution and current
bytes matching the journal. It SHALL preserve conversation and budget history.

#### Scenario: External modification
- **WHEN** another application changes the file after its checkpoint
- **THEN** restoration fails without overwriting those bytes.

#### Scenario: New file recovery
- **WHEN** the user confirms restoring a checkpoint for a newly created file
- **THEN** only that matching file is removed and the entry becomes restored.
