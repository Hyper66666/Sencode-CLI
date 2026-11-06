## ADDED Requirements

### Requirement: Child events have bounded agent presentation
The fullscreen frontend SHALL project child events by stable identity into
readable summaries, never raw protocol JSON or parent answer text.

#### Scenario: Interleaved child output
- **WHEN** multiple agents stream text and tool updates while the parent answers
- **THEN** each agent has one stable progress identity, terminal states are
  accurate and the parent text retains chronological order

#### Scenario: Malformed event
- **WHEN** a child payload is malformed, unknown or contains terminal controls
- **THEN** the frontend does not print its raw envelope, terminate execution or
  claim successful completion

### Requirement: Effective effort is visible and sent
The frontend SHALL display the selected model and effective reasoning effort,
using medium as the implicit default where model capabilities allow it.

#### Scenario: Default supported effort
- **WHEN** a reasoning model supporting medium is selected without an override
- **THEN** the header displays medium and the next provider request sends medium

#### Scenario: Unsupported effort
- **WHEN** a model explicitly denies reasoning effort or excludes medium
- **THEN** the implicit selection does not claim medium and an explicit
  unsupported setting is rejected without a provider request

#### Scenario: Next target selected during streaming
- **WHEN** the user changes model or effort during a running request
- **THEN** the header retains the running target until completion and the new
  selection applies only to the next request

#### Scenario: Manually entered model
- **WHEN** a native model is entered without adding it to the enabled picker
- **THEN** its implicit effort is resolved from connection capabilities and
  displaying that default does not make the model fail catalog admission

### Requirement: Permission modes are explicit and modal safe
The composer SHALL cycle manual, auto workspace edit and full tool approval on
Shift+Tab and show the selected mode below its input. Changes apply to future
requests and cannot override Plan, child-role or engine capability restrictions.

#### Scenario: Composer cycle
- **WHEN** Shift+Tab is pressed in an idle or streaming composer
- **THEN** the selected future mode advances without submitting or modifying
  the draft, while a running request keeps its original policy

#### Scenario: Approval or picker focus
- **WHEN** an approval, question or selector owns input focus
- **THEN** Shift+Tab cannot silently approve a tool or change permission mode

#### Scenario: Full mode still respects Plan
- **WHEN** full mode is selected and a Plan task requests a write, shell or MCP
- **THEN** the Plan restriction still rejects it

#### Scenario: Permission display follows the actual engine
- **WHEN** a native API connection is selected with a remembered backend profile
- **THEN** the footer displays the actual native policy and backend consent
  cannot be presented as a native permission mode
