## ADDED Requirements

### Requirement: One-turn Plan overlay
Plan SHALL constrain only the selected conversation turn and its children, then
clear after completion, cancellation or abnormal interruption.

#### Scenario: Completed plan
- **WHEN** a planning reply and its tools finish
- **THEN** the next user or queued turn uses the underlying selected approval permissions without Plan

#### Scenario: Interrupted plan
- **WHEN** the user cancels, execution fails or its host stops unexpectedly
- **THEN** the foreground clears Plan while retaining execution cleanup and replay safeguards

### Requirement: Non-restorable planning activation
Session recovery SHALL NOT activate Plan from historical metadata.

#### Scenario: Restart after crash
- **WHEN** a process exits during Plan or a legacy session contains active=true
- **THEN** resuming starts outside Plan unless the user explicitly selects Plan again

### Requirement: Preserve permissions and plan artifacts
Automatic Plan exit SHALL NOT grant approvals, execute a plan, or delete artifacts.

#### Scenario: Underlying manual approval
- **WHEN** Plan ends while manual approval is selected
- **THEN** the next modifying tool still requires manual approval
