## ADDED Requirements

### Requirement: Reading groups preserve chronological context
The TUI SHALL fold consecutive read, list and search tools using stable identities and truthful counts. Answers, mutations and commands SHALL break groups. Errors SHALL remain visible and toggling SHALL NOT submit a draft.

#### Scenario: Streaming and expanding a reading group
- **WHEN** tools finish incrementally while the user expands a group, scrolls history or resizes
- **THEN** the same group retains its state and browsing position and shows the actual operation details

### Requirement: Activity is truthful and isolated from the composer
Explicit provider reasoning signals SHALL control Thinking; other work SHALL use Working and approvals SHALL use a static waiting state. Main and child activity SHALL appear in their conversation tails. Terminal elapsed time SHALL survive history recovery without restarting activity.

#### Scenario: Four streams and keyboard input
- **WHEN** four loopback model streams run while the user edits the composer
- **THEN** visible activity updates without resetting cursor blink or repainting idle rows and measured input latency p95 is below 50 ms on the qualified host

### Requirement: Diffs use readable semantic spans
Diffs SHALL show bounded multi-hunk line changes, three lines of context, a file summary, gray single-column line numbers and red/green changed text without full-row color backgrounds. The renderer SHALL preserve Unicode width, no-color behavior and a blank row above the composer.

#### Scenario: Two separated edits
- **WHEN** two small changes are separated by unchanged content
- **THEN** distinct hunks retain truthful context and counts instead of displaying the intervening content as a replacement

#### Scenario: Narrow Unicode display and unsupported colors
- **WHEN** the viewport narrows or NO_COLOR is enabled
- **THEN** diff wrapping remains aligned, text stays readable and no raw terminal escapes originate from model content
