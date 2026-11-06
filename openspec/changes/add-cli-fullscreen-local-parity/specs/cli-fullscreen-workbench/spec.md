## ADDED Requirements

### Requirement: Responsive fullscreen projection
The TTY frontend SHALL own a monochrome fullscreen projection with a centered
home, fixed composer and independently scrollable transcript. Native rendering
and agent execution SHALL remain separate concerns.

#### Scenario: Stream while editing
- **WHEN** a provider emits text while a user edits a draft
- **THEN** incremental text and the draft are both visible without raw stdout
  corrupting layout, and the draft remains after cancellation.

#### Scenario: Follow behavior
- **WHEN** the user scrolls upward while a response grows
- **THEN** the viewport remains anchored until the user explicitly returns.

### Requirement: Registry-driven completion
One command registry SHALL drive help, parsing, aliases, descriptions, capability
availability and completion.

#### Scenario: Enter only completes
- **WHEN** Enter selects a visible slash suggestion
- **THEN** it fills the command and closes the menu without execution, and a
  subsequent explicit Enter may execute that command.

#### Scenario: Unavailable command
- **WHEN** a capability is absent or not implemented
- **THEN** it cannot execute and its unavailable reason is shown.

### Requirement: Restore and plain output
Fullscreen state SHALL restore on normal exit and unwinding; non-TTY and plain
output SHALL preserve existing data contracts without screen controls.

#### Scenario: Exit restores terminal
- **WHEN** a fullscreen session exits normally or after a handled failure
- **THEN** its screen, mouse, cursor and console modes are restored.
