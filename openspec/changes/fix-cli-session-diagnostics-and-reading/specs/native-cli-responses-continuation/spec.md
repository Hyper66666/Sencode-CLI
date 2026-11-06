## ADDED Requirements

### Requirement: Explicit Responses intermediate answers continue the same task
The Sengoo API engine SHALL preserve Responses message phases and explicit end_turn state through parsing, persistence and scoped history replay. Only a validated completed response with explicit end_turn=false SHALL request automatic continuation. Continuation SHALL retain the task, connection snapshot, permission policy, tool identities and cumulative budget.

#### Scenario: Intermediate answer then final answer
- **WHEN** a completed Responses response declares end_turn=false without local tool calls
- **THEN** the main or child Agent requests the next response in the same task, preserves the ordered phased messages and does not mark the task complete

#### Scenario: Missing or unsafe continuation signal
- **WHEN** end_turn is missing or true, or the response is refused, incomplete, malformed or cancelled
- **THEN** the host does not infer continuation from wording, model name or message phase

#### Scenario: Switching target and restoring history
- **WHEN** a user switches connection or model or explicitly resumes stored public history
- **THEN** server-scoped opaque state does not cross target boundaries, saved control metadata grants no authority to resume work, and cumulative budgets do not reset
