# Responses continuation, shell execution and cursor stability

## ADDED Requirements

### Requirement: Responses reasoning items continue tool turns
The native Responses adapter SHALL preserve validated reasoning output items
and include them in the next input when a response also contains a function
call.

#### Scenario: reasoning followed by a function call
- **WHEN** a Responses stream emits a reasoning item, fragmented function-call
  arguments and `response.completed`
- **THEN** the CLI stores the bounded item, presents the function call to the
  normal permission and scheduler path, and sends the item plus tool output on
  the continuation request

#### Scenario: malformed or incomplete item
- **WHEN** an item is malformed, exceeds its limit or its completion cannot be
  correlated with an output index
- **THEN** the turn pauses with a diagnostic and no tool is executed or replayed

#### Scenario: switching connection or model
- **WHEN** a resumed session targets a different connection, endpoint or model
- **THEN** its request uses public text and normalized tool history without
  forwarding opaque items from the previous target

### Requirement: model shell commands prefer Bash
The `run_command` tool SHALL default to an available Bash executable on
Windows, while retaining explicit PowerShell/CMD selection, timeout, permission
and process-tree cleanup guarantees.

#### Scenario: Git Bash is installed
- **WHEN** a permitted command is run with Git Bash available
- **THEN** it executes with Bash semantics, reports the selected shell and
  drains both output streams to quiescence

#### Scenario: Bash is unavailable
- **WHEN** no safe Bash executable can be resolved
- **THEN** the CLI returns a clear diagnostic without silently switching shell
  syntax or executing a repository-local shadow shell

### Requirement: composer cursor is stable
The fullscreen renderer SHALL avoid resetting cursor visibility on every frame
and SHALL remove the redundant composer Thinking activity row.

#### Scenario: typing during a busy turn
- **WHEN** the UI repaints while input is focused and a provider is streaming
- **THEN** the cursor blinks at a stable cadence without one-second visible
  resets or redraw-induced jumps, and the composer has no Thinking glyph/text

#### Scenario: exit or overlay focus
- **WHEN** the user opens an approval/menu overlay or exits the workbench
- **THEN** cursor visibility and terminal modes are restored exactly once

### Requirement: growing streamed responses remain responsive
The TUI SHALL update newly arrived text incrementally, limit redundant render
work, and preserve completed Markdown blocks and the user's scroll position.
It SHALL consume actual provider deltas without artificial character playback.

#### Scenario: long Markdown answer grows during input
- **WHEN** a provider streams a long answer with paragraphs and fenced code
  while the user edits a draft or cancels
- **THEN** successive partial content is visible before completion, input and
  cancellation remain responsive, and stable content is not repeatedly parsed

#### Scenario: idle and historical view
- **WHEN** the visible content and cursor are unchanged, or the user scrolls
  back while new deltas arrive
- **THEN** unchanged frames emit no terminal output and arriving text does not
  force the viewport back to the latest message

### Requirement: model questions offer keyboard choices
The native `ask_user` tool SHALL accept an optional bounded list of two to six
labelled options with optional descriptions. The question overlay SHALL allow
arrow-key selection, Enter confirmation and a custom text answer, keeping the
composer draft separate. Question answers SHALL NOT grant tool permissions.

#### Scenario: choose an option
- **WHEN** a model asks a valid question with options
- **THEN** the UI shows the options, consumes arrow keys inside the overlay and
  sends the chosen label only after a fresh explicit Enter

#### Scenario: custom answer or cancellation
- **WHEN** the user chooses a custom answer or presses Esc
- **THEN** custom text requires explicit submission; Esc cancels the interaction
  and pauses the turn without turning cancellation into an answer

#### Scenario: invalid or legacy question
- **WHEN** options are malformed, duplicated or exceed the bounds
- **THEN** validation rejects the call before opening the overlay
- **WHEN** a legacy question omits options
- **THEN** its existing free-text interaction remains available

### Requirement: pending insertions can be retracted
Messages submitted during an active turn SHALL remain a visible, bounded FIFO
queue until accepted for a later turn. The message area SHALL show a compact
grey pending preview directly above the composer, including text and count.
The CLI SHALL distinguish pending messages from content already sent to a model.

#### Scenario: retract before sending
- **WHEN** the user presses Esc with a pending message and no focused overlay
- **THEN** the most recent pending message is removed from the queue and made
  available in the composer without cancelling the current turn or losing an
  existing draft

#### Scenario: focus and cancellation
- **WHEN** an approval, picker or menu owns focus
- **THEN** its Esc action consumes the key without retracting or cancelling
- **WHEN** there is no pending message, or the user explicitly presses Ctrl+C
- **THEN** the existing active-turn cancellation action remains available

### Requirement: local prompt and copy conveniences
The fullscreen CLI SHALL provide project-scoped `/history [SEARCH]`, a
session-local draft stash via Ctrl+S and `/stash`, and `/copy code` for complete
fenced code blocks. Each operation SHALL remain local and preserve permission
policy. Search SHALL be bounded and literal, including Unicode queries.

#### Scenario: recall a project prompt
- **WHEN** the user searches and selects a prompt from the current project
- **THEN** Enter fills the composer without sending it, prompts from other
  projects are absent, and Esc closes the search without a model call

#### Scenario: stash and exchange
- **WHEN** Ctrl+S is pressed at composer focus
- **THEN** a nonempty draft can be stashed, an empty draft can restore it, and
  two nonempty values are exchanged without loss or submission
- **WHEN** an overlay owns focus
- **THEN** the shortcut does not modify the underlying draft

#### Scenario: copy code
- **WHEN** `/copy code` selects a complete fenced block
- **THEN** only its code is copied; fence markers are excluded and an incomplete
  block is never silently presented as a complete block

### Requirement: pasted images retain original paths and atomic chips
The fullscreen composer SHALL recognize explicitly pasted PNG/JPEG file paths
and clipboard file references without copying original files into the project.
It SHALL display referenced attachments as blue atomic `[imageN]` chips with
stable path mappings, and SHALL submit image bytes only to a captured capable
target after explicit user submission. Clipboard pixels without a source file
SHALL use a bounded system temporary cache, never a project image copy.

#### Scenario: paste original image paths
- **WHEN** the user pastes quoted image paths or clipboard image files
- **THEN** the composer shows numbered blue chips, preserves the original paths,
  and makes no model request or project image write

#### Scenario: atomic editing
- **WHEN** the cursor crosses a chip or Backspace/Delete removes it
- **THEN** the cursor stays at chip boundaries and one deletion removes the
  entire chip reference without deleting the original file

#### Scenario: pixel-only clipboard and terminal interception
- **WHEN** the clipboard contains only pixels or the terminal consumes Ctrl+V
- **THEN** explicit Alt+V remains available; pixel data is converted to a bounded
  temporary PNG and the UI identifies the lack of an original file path

#### Scenario: image transmission and recovery
- **WHEN** an explicit image-bearing request is sent or resumed
- **THEN** image references require session grants and matching metadata before
  bounded bytes are hydrated into the three protocol formats; unsupported
  targets, missing files and changed files are diagnosed before transmission
