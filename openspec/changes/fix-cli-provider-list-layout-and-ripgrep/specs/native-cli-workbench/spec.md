## ADDED Requirements

### Requirement: Conversations originate at the top of the workbench
The CLI SHALL place short conversations immediately below the header, retain its bottom composer and separator, and render effective manual permission in light blue, auto permission in yellow and full permission in red when colors are enabled.

#### Scenario: First streaming answer
- **WHEN** a first message receives a short streamed answer
- **THEN** its transcript starts at the top and the unused space follows the transcript, with no activity animation in the composer

#### Scenario: Pending permission change
- **WHEN** permission changes during an accepted request
- **THEN** the current and next permission labels keep their own semantic color and the active permission is not replaced

### Requirement: Every configured supplier is available in the grouped model menu
The CLI SHALL list all saved suppliers and their enabled models in supplier order, using supplier headings followed by selectable model rows and preserving supplier identity for duplicate model names.

#### Scenario: Navigation and request selection
- **WHEN** a user moves down past a supplier's last model and selects a model in the next supplier
- **THEN** selection crosses the heading without submitting, effort selection captures that supplier and model, and only the next accepted request uses it

#### Scenario: Configuration refresh
- **WHEN** another local configuration client saves another supplier while the CLI is idle
- **THEN** reopening the model menu reads that supplier and its enabled models without altering the existing target or contacting suppliers
