## ADDED Requirements

### Requirement: Shared CLI configuration switching
The application SHALL read and update the CLI's existing connection store and
SHALL show the selected connection only after a committed successful operation.

#### Scenario: Choose and refresh
- WHEN the user selects a saved connection or another client changes the default
- THEN the next refreshed snapshot shows the committed selection, without changing active turns.

### Requirement: Private API editing
The application SHALL store API keys only through the operating-system credential
store and SHALL preserve unrelated fields when editing an existing API profile.

#### Scenario: Blank key and non-secret export
- WHEN an existing profile is saved with a blank password field
- THEN its existing credential remains unchanged.
- WHEN the profile is exported
- THEN no credential or credential reference is included.

#### Scenario: Invalid input or failure
- WHEN a profile is invalid, conflicts or cannot be saved
- THEN the form remains editable and the committed connection does not change.

### Requirement: Minimal accessible workbench
The application SHALL use the name sencode-config and provide a white React
interface with clear labels and without explanatory small-print paragraphs.

#### Scenario: Keyboard and empty catalog
- WHEN no connections exist
- THEN an add action remains available.
- WHEN the user searches, navigates by keyboard or presses Escape in a dialog
- THEN focus and actions remain predictable without losing unsubmitted forms silently.

### Requirement: Desktop-compatible model catalog
The application SHALL use the desktop connection format for model discovery,
enabled models, default model and image capability, without changing active turns.

#### Scenario: Discover and choose
- WHEN the user explicitly probes an API using its draft or stored credential
- THEN a bounded candidate catalog appears without automatically enabling models, changing the default or saving the draft.
- WHEN the user enables several models and selects one as default
- THEN the committed desktop-compatible configuration is visible to the CLI, and the card selector lists only enabled models.

#### Scenario: Manual models and probe failures
- WHEN the provider lacks a model endpoint or probing fails or times out
- THEN saved configuration and enabled model metadata remain unchanged and manual model entry remains available.
- WHEN the default is not enabled or model identifiers are invalid or duplicated
- THEN saving fails without mutating the configuration.
