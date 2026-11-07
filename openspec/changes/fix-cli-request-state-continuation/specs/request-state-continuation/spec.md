## ADDED Requirements

### Requirement: Bounded state replacement
The host SHALL read and update independent mode members without parsing the
combined state into one JSON arena, preserving unrelated members and format.

#### Scenario: Long request history
- **WHEN** valid combined state fits the existing JSON bounds
- **THEN** updating an attempt to accepted or cancelled succeeds
- **AND** unrelated state and execution fencing remain intact

#### Scenario: Aggregate state exceeds one arena
- **WHEN** independent bounded state fields together exceed 4096 JSON nodes
- **THEN** request updates, remembered models/permissions and branching still work
- **AND** portable import validates only its allowed metadata without enabling permissions

#### Scenario: Full attempt journal
- **WHEN** an existing attempt is updated in a 256-entry journal
- **THEN** the other entries remain intact
- **AND** admitting a new attempt evicts only the oldest non-live entry, or refuses if all entries are live

### Requirement: Evidence-based continuation
The host SHALL reconcile only structurally valid trailing missing tool results
under current execution authority, without invoking a tool during recovery.

#### Scenario: Tool never admitted
- **WHEN** a persisted assistant call has no public result and no ledger claim
- **THEN** continuation records that the tool was not executed
- **AND** sends balanced context to the model without running the old call

#### Scenario: Completed ledger result missing from public history
- **WHEN** the ledger certifies completion and its matching public result is absent
- **THEN** continuation restores the exact saved result once
- **AND** no old side effect is repeated

#### Scenario: Uncertain result
- **WHEN** cleanup or the tool outcome remains uncertain
- **THEN** the host refuses automatic continuation and preserves evidence

### Requirement: Request-state diagnostics
Request evidence persistence failures SHALL be identified independently of
provider transport or protocol failures.

#### Scenario: Response received before evidence save fails
- **WHEN** request bookkeeping fails after receiving a model response
- **THEN** the diagnostic identifies request-state persistence
- **AND** no new tool is executed through this failure path
