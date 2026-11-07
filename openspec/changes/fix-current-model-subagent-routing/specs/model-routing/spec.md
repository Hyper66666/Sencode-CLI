## ADDED Requirements

### Requirement: Current target inheritance
Children SHALL inherit the current native request's immutable provider, model,
effort and transport snapshot when no different target is selected.

#### Scenario: Saved default differs
- **WHEN** the running model differs from its provider's saved default
- **THEN** an untargeted child uses the running model and effort even if saved defaults change

### Requirement: Configured target search
The host SHALL resolve enabled model IDs, labels and case-insensitive fragments
across providers, preferring exact IDs and rejecting ambiguous distinct targets.

#### Scenario: Fragment selects another provider
- **WHEN** the user requests terra and only provider B enables gpt-6.1-terra
- **THEN** spawn_agent resolves provider B and invokes gpt-6.1-terra

#### Scenario: Several matches
- **WHEN** the best-ranked matches identify distinct models or ambiguous providers
- **THEN** the tool returns bounded candidates without starting a child or falling back

#### Scenario: Unavailable target
- **WHEN** a model is absent, discovered-only or requires an unsupported runtime
- **THEN** the parent receives a recoverable result explaining the limitation

### Requirement: Public directory and request identity
Agents SHALL receive truthful configured request identity and be able to search
the enabled public directory without exposing private configuration.

#### Scenario: Model switch or resume
- **WHEN** a main or child request starts after a model switch or session resume
- **THEN** its outbound context identifies that request's configured target without persisting stale identity in history

#### Scenario: Plan directory search
- **WHEN** a parent in Plan invokes list_models
- **THEN** it receives a bounded public directory without writes, credentials or provider calls
