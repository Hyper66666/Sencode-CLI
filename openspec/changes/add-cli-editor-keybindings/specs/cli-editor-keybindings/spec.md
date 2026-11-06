## ADDED Requirements

### Requirement: User keymaps are versioned and restricted to composer operations

The fullscreen CLI SHALL read an optional user JSON keymap from an explicitly
selected path or its documented user profile location. It SHALL bound file size,
require strict UTF-8, validate schema v1 and reject the entire configuration on
unknown fields, duplicate keys, reserved keys or non-composer actions.

#### Scenario: A valid explicit map overrides the user default

- **WHEN** SENCODE_KEYMAP names a valid map with safe composer actions
- **THEN** the fullscreen composer uses it and `/keys show` identifies its source
- **AND** no configuration file or execution policy is modified

#### Scenario: An unsafe or malformed map has no partial effects

- **WHEN** a map contains an invalid suffix after a valid binding
- **THEN** all bindings from that file are rejected and default editing continues
- **AND** the bounded diagnostic does not echo arbitrary file contents

#### Scenario: Approval and submission keys cannot be replaced

- **WHEN** a map tries to bind Enter, cancellation, a reserved chord or submit
- **THEN** configuration validation rejects it
- **AND** approval, send, cancel and exit keep their host-defined behavior

### Requirement: Vim editing is an explicit and bounded fullscreen capability

The fullscreen CLI SHALL provide `/keys vim` and `/keys default`. Vim SHALL begin
in INSERT, show INSERT/NORMAL state, preserve Unicode graphemes, provide a
documented subset of common motions/edits and retain bounded undo. It SHALL show
the explicit Ctrl+C cancellation shortcut while Escape changes editor mode.

#### Scenario: Normal-mode editing is isolated from provider execution

- **WHEN** the user enters NORMAL and performs motions, edits and undo
- **THEN** only the composer draft and cursor change
- **AND** no task is submitted until a separate explicit send action

#### Scenario: Pasted text cannot execute modal commands

- **WHEN** pasted text contains Vim keys, newlines or slash commands
- **THEN** it is inserted as literal composer text in INSERT
- **AND** it cannot approve, submit or run a command

#### Scenario: A fresh approval keeps priority over editor configuration

- **WHEN** a host approval arrives while Vim, custom keys or queue editing is active
- **THEN** the fresh approval handler retains its default-deny decision model
- **AND** editor state cannot choose or confirm an approval

### Requirement: Reading mode preserves interaction ownership

The fullscreen CLI SHALL provide `/read` to navigate cached model output while
streaming continues. Navigation SHALL not mutate the composer or execution
state; q or Escape SHALL return to the previous draft and cursor. Automatic
queue dispatch SHALL wait until reading focus is released.

#### Scenario: Streaming and queued tasks wait for explicit focus return

- **WHEN** reading mode is active and new model text or a terminal result arrives
- **THEN** the transcript anchor is preserved and the draft remains unchanged
- **AND** queued work is not automatically dispatched until reading exits

#### Scenario: Hosts without fullscreen input capability degrade explicitly

- **WHEN** a scrolling or noninteractive host supplies its command registry
- **THEN** `/keys` and `/read` remain disabled unless that host implements them

#### Scenario: Resizing keeps the visible message anchored

- **WHEN** terminal width or height changes while the user is reading earlier output
- **THEN** the lower visible message is retained by its stable identity and bounded row position as wrapping is rebuilt
- **AND** the original composer and reading focus remain intact while newer streamed output accumulates
- **AND** a user who was already following output continues following it
