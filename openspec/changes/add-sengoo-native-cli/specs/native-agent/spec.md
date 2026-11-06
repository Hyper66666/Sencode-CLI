## ADDED Requirements

### Requirement: Agent business logic executes in Sengoo
The native CLI SHALL implement provider parsing, tools, scheduling, modes and
terminal interaction in Sengoo using generic system runtime APIs.

#### Scenario: A user completes an external project change
- **WHEN** the packaged CLI receives a coding request
- **THEN** it streams a supported API, performs authorized tools, verifies the
  result and persists a resumable conversation without a local compiler.

### Requirement: Modes and descendants preserve authority
Plan and Goal SHALL use persistent host state, and descendants SHALL inherit
the parent's effective capability restrictions.

#### Scenario: A Plan child requests a shell or MCP tool
- **WHEN** any descendant requests an execution/write-capable tool in Plan
- **THEN** it is rejected before execution and the workspace is unchanged.

#### Scenario: Goal verification is unavailable
- **WHEN** required verification cannot run
- **THEN** Goal pauses with a reason and is not marked complete.

### Requirement: Interactive sessions use a scrolling terminal interface
The CLI SHALL show workspace, session, selected model, mode and keyboard hints
with a wrapping multiline composer. TUI rendering SHALL stay in Sengoo, preserve
conversation scrollback and neutralize untrusted terminal controls. Redirected
structured output SHALL retain its existing schema and contain no UI escapes.

#### Scenario: A user edits Chinese and multiline input after resizing
- **WHEN** an interactive user pastes Unicode text, moves the cursor, resizes the
  console and recalls a history entry
- **THEN** cursor placement follows display cells, the composer redraws within
  the new width and returning from history restores the user's current draft.

#### Scenario: A user types while consultation or MCP is running
- **WHEN** a busy operation reads input before the next ordinary prompt
- **THEN** bounded noncancel input is retained for that prompt and cannot approve
  a later side effect; cancellation still stops the owned operation.

### Requirement: Installed short commands preserve the caller's project
The Windows installer SHALL provide `sen` and `sencode` through the user command
search path, without replacing unrelated commands. It SHALL offer owned
forwarders through an existing user command directory so an inherited PATH can
discover the install without manually adding its binary directory.

#### Scenario: A shell retains its pre-install PATH
- **WHEN** the shell already searches the selected command directory and invokes
  `sen` or `sencode` in an external project
- **THEN** the installed CLI starts in that directory with the original arguments,
  including `resume` and an optional session ID.
