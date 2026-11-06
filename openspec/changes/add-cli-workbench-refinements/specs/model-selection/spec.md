## ADDED Requirements

### Requirement: Enabled catalog model columns
The native CLI SHALL render saved connection channels in paired columns, with
each channel's complete enabled model directory listed vertically underneath.
Rows SHALL retain the full connection/model identity, label, runtime state and
capability metadata. Discovered but disabled models SHALL NOT become selectable
because they appear in discovery results or share a model id with another
connection. More than two channels and long directories SHALL remain reachable
by navigation and scrolling.

#### Scenario: Two channels share a model id
- **WHEN** channels A and B both enable model X and A also enables Y
- **THEN** A lists X and Y, B lists X, and selecting B/X captures B/X without
  changing A or merging the two X entries

#### Scenario: Full enabled directory
- **WHEN** a connection enables multiple models while its default names one model
- **THEN** every enabled model is shown, and discovery-only models are omitted

#### Scenario: Unavailable account channel
- **WHEN** a managed account reports blocked/unsupported state or lacks the
  required runtime capability
- **THEN** its channel remains visible with the reason and the CLI does not
  convert its name or saved models into a capability grant

### Requirement: Second-level reasoning selection
Enter on a model SHALL open a separate effort list before any target update.
The supported local preference vocabulary SHALL match desktop Sencode exactly:
`low`, `medium`, `high`, `xhigh`, `max`. Model/runtime restrictions SHALL narrow
the list. Escape SHALL return without changing the current target. The final
selection SHALL atomically capture connection, model and effort for later turns.

#### Scenario: Two explicit selections
- **WHEN** the user presses Enter on an enabled model
- **THEN** only the effort list opens, and a second deliberate Enter commits its
  connection/model/effort tuple

#### Scenario: Capability denies effort
- **WHEN** the connection/runtime or model explicitly denies reasoning effort
- **THEN** configured effort lists cannot override that denial, and selecting a
  nonempty effort fails before a request starts

#### Scenario: Cancel selection
- **WHEN** the user exits the model or effort selector
- **THEN** the previously selected tuple and any running turn remain unchanged

### Requirement: Protocol effort encoding and snapshot isolation
Every accepted native request SHALL retain the selected connection/model/effort
tuple, including tool continuations, compaction, child requests and consultation
requests. Native encoders SHALL use desktop sampling-types mappings. Empty effort
SHALL preserve the legacy request shape. Unknown values SHALL fail validation
instead of silently selecting another level or provider.

#### Scenario: OpenAI maximum preference
- **WHEN** a native Chat or Responses request captures effort `max`
- **THEN** its wire value is `xhigh` and its captured local preference stays `max`
  with Chat `reasoning_effort` or Responses `reasoning.effort`

#### Scenario: Messages extra-high preference
- **WHEN** a native Messages request captures `xhigh`
- **THEN** adaptive thinking and `output_config.effort=high` are emitted, while
  `max` emits `output_config.effort=max`

#### Scenario: Legacy and invalid values
- **WHEN** effort is empty or contains a value outside the five desktop levels
- **THEN** empty omits reasoning fields; invalid input fails before network I/O

#### Scenario: Switching while a turn runs
- **WHEN** the user selects another tuple for future sends
- **THEN** the accepted turn and its child/continuation request encoding retain
  their original tuple, and usage attribution retains connection/model identity
