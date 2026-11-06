## ADDED Requirements

### Requirement: Explicit local attachments SHALL capture bounded immutable content
Only explicit user selection SHALL capture a local attachment. The application
SHALL validate authorized local paths, use the generic bounded file snapshot,
inspect copied bytes and bind each draft asset to its session and digest.
Ordinary pasted prose SHALL NOT implicitly read or upload a file.

#### Scenario: The source changes after capture
- **WHEN** a draft asset is accepted and the old pathname now contains different data
- **THEN** the request references the already captured digest/bytes or reports a missing asset
- **AND** no silent pathname reread changes the attachment.

#### Scenario: Input is rejected or the user discards a draft
- **WHEN** capture fails, exceeds limits or an owned draft is explicitly removed
- **THEN** partial resources are released and no request is sent
- **AND** the selected source file is never deleted or overwritten.

### Requirement: Provider requests SHALL preserve ordered media and target capability
Each accepted turn SHALL freeze connection/model and ordered text/media parts.
Each adapter SHALL require an explicit media capability, encode its qualified
protocol representation and check the complete request against all transport
limits before outbound I/O. Unsupported content SHALL NOT disappear silently.

#### Scenario: A model or request limit cannot accept an image
- **WHEN** vision capability is unknown/unsupported or serialized content exceeds a local limit
- **THEN** the UI reports the specific reason and an explicit user choice is required
- **AND** a loopback observer sees no provider request or automatic target switch.

#### Scenario: A text-only tool conversation continues after an image turn
- **WHEN** the next turn contains tool outputs and ordinary text
- **THEN** ordered retained media and tool IDs remain correct for that adapter
- **AND** legacy text-only history keeps its prior compatible request behavior.

### Requirement: Shared attachment history SHALL survive restart and fenced handoff
Accepted public messages and compatible asset references SHALL be persisted
under existing execution fencing/changelog rules. Restart SHALL verify retained
assets and report missing/corrupt or unsupported references explicitly. Shared
schema/asset changes SHALL have a desktop compatibility/version gate.

#### Scenario: An idle image conversation moves between desktop and CLI
- **WHEN** the old executor has released authority and the other client loads public history
- **THEN** both clients resolve the same compatible image asset or expose an explicit unsupported state
- **AND** a delayed obsolete executor cannot alter the new owner's message/reference.

### Requirement: PDF header capability SHALL NOT imply full PDF acceptance
The UI SHALL distinguish header metadata, native document submission, extraction
and rendering. Missing engines SHALL produce a truthful unsupported status with
no dependency installation. Full PDF/multimodal gates SHALL require their own
implementation and installed/offline evidence.

#### Scenario: A PDF is recognized but no qualified engine or adapter exists
- **WHEN** the user selects a local PDF with a recognized header
- **THEN** header facts and unsupported functions are visible
- **AND** it is not counted as a successfully sent or parsed PDF.
