## ADDED Requirements

### Requirement: Ordered native conversation projection
The Sengoo frontend SHALL preserve assistant text and tool event order, update
one card per execution-scoped call ID and preserve the visible reading anchor.

#### Scenario: Interleaved model and tools
- **WHEN** text, tool start, more text and tool completion arrive
- **THEN** text precedes the tool card, later text follows it, and completion
  changes that card without adding a second card or splitting the later text.

#### Scenario: Independent same-name calls and delayed updates
- **WHEN** two calls have the same tool name or a terminal card receives a late running event
- **THEN** distinct IDs remain distinct and terminal cards cannot restart.

### Requirement: Bounded activity in the tool card
Running tool headers SHALL show lightweight activity and elapsed time using
Sengoo state and existing differential painting without composer animation.

#### Scenario: Animation and focus
- **WHEN** a running card is visible and no modal owns focus
- **THEN** its activity advances without changing the draft, scroll anchor,
  composer borders or cursor visibility; hidden, completed and reduced-motion cards do not tick.

### Requirement: Public history restoration
Canonical assistant tool calls and results SHALL restore ordered tool cards
without executing tools or interpreting unknown outcomes as success.

#### Scenario: Resume after interruption
- **WHEN** history contains a call with no terminal result
- **THEN** the restored card is interrupted and static, and no replay occurs.
