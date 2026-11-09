## ADDED Requirements

### Requirement: Explicit noninterrupting insertion
The native host SHALL accept explicitly requested queued user conditions at a
complete response or tool-batch boundary in the same execution and budgets.

#### Scenario: Second Enter
- **WHEN** a running task has queued text and the user presses Enter with an empty composer
- **THEN** the oldest item is transferred once without cancellation or parallel model submission
- **AND** menus, dialogs, drafts and other queue items retain their own state

#### Scenario: Ownership and replay
- **WHEN** steering is duplicated, stale, invalid, cancelled or unsupported
- **THEN** it cannot expand permissions, replay tools or append a duplicate user message
- **AND** unapplied text is returned paused, while an uncertain crash outcome requires manual recovery

### Requirement: Accurate compaction and notices
The UI SHALL show Compacting throughout summary generation and red NOTICE text.

#### Scenario: Successful checkpoint
- **WHEN** context reduction installs a durable checkpoint
- **THEN** a standalone 上下文已压缩 appears before continuing the task
- **AND** the legacy English compaction NOTICE is absent

#### Scenario: Failure visibility
- **WHEN** any NOTICE is displayed
- **THEN** both heading and all wrapped content use red foreground unless color is disabled
