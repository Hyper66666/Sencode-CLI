## ADDED Requirements

### Requirement: Empty composer has no preset text
The idle and running-turn composer SHALL show an empty editable body when the
draft is empty. Existing borders, prompt marker and permission footer remain.

#### Scenario: Empty draft during idle and streaming
- **WHEN** a user opens a fresh session or clears the draft while a turn runs
- **THEN** the composer body contains no placeholder or suggested prompt
- **AND** native cursor blink and draft editing remain available.

### Requirement: Scrolling is responsive and preserves the viewport
The CLI SHALL retain sub-notch wheel movement, bound scroll-only repaint cadence,
and reuse verified overlapping screen cells without moving the header or composer.

#### Scenario: Continuous wheel input
- **WHEN** a user scrolls through a long conversation, including fractional wheel input
- **THEN** no accumulated movement is lost, the viewport stops at a full top page, and input remains responsive without repainting unchanged mouse motion

#### Scenario: Streaming, overlays and resize
- **WHEN** scroll input overlaps new text, a picker, an approval or resizing
- **THEN** input focus and reading anchors remain correct and incompatible cell shifts use ordinary row rendering

### Requirement: Resume restores the conversation model target
The CLI SHALL restore a session's last selected supplier, model and thinking effort,
including a selection made after its last model request. Permission restoration
is independently owned by `fix-cli-permission-memory-and-agent-wait`.

#### Scenario: Exit after choosing another model
- **WHEN** a user selects a model, exits and resumes through the CLI or session picker
- **THEN** the header and next request use that session's saved target instead of the global default

#### Scenario: Running turn and explicit overrides
- **WHEN** a user changes target during a request or resumes with explicit target flags
- **THEN** the running target is unchanged, pending selection persists after cleanup, and explicit flags override only their corresponding target scope

#### Scenario: Portable or unavailable target
- **WHEN** the project is renamed, branched or imported, or its saved supplier was removed
- **THEN** bounded model preferences travel with its history and a removed supplier is reported without silently requesting a different provider

### Requirement: Updating an installed CLI preserves running sessions
After all payload and command publications commit, the installer SHALL retain
only tracked busy backup files rather than fail or stop an existing process.
Failed publication and rollback errors SHALL remain failures.

#### Scenario: A running image holds its old program backup
- **WHEN** a session is open while an atomic update publishes the new CLI
- **THEN** the existing process keeps running, new commands use the installed
  version, and retained owned backup paths are reported for deferred cleanup
- **AND** unrelated cleanup errors, locked alias publication and rollback
  failures are not converted into successful installation.
