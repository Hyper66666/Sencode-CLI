## ADDED Requirements

### Requirement: Reports distinguish model claims from host outcomes
The host SHALL validate bounded schema1 child reports and label their fields as
model claims while preserving separately observed status, error and attribution.

#### Scenario: Child claims successful tests after failure
- **WHEN** a child reports outcome completed and check pass but its host outcome is canceled or failed
- **THEN** the host outcome remains canceled or failed and the checks remain model claims
- **AND** Goal acceptance and execution permissions are unchanged

#### Scenario: Invalid report
- **WHEN** a final response is plain text, malformed, missing fields, oversized or has unknown fields or check statuses
- **THEN** a bounded Unicode-safe excerpt and an explicit validation diagnostic are returned
- **AND** the original response is retained in public evidence

### Requirement: Evidence reads are scoped and versioned
The host SHALL read existing retained evidence only with a valid current fence,
current read policy, an authorized session relationship and an exact source hash.

#### Scenario: Parent and child boundaries
- **WHEN** a parent reads a direct child's evidence in the same project
- **THEN** the bounded read is permitted
- **AND** a child reading its parent, sibling or unrelated session receives unavailable

#### Scenario: Deleted or changed source
- **WHEN** a referenced source is deleted or its bytes change between pages
- **THEN** the read reports unavailable or source_changed respectively
- **AND** no source tool is executed, replayed or inferred successful

#### Scenario: Ownership lost
- **WHEN** the caller's execution fence is obsolete
- **THEN** the evidence read fails before returning source content

### Requirement: Evidence pagination preserves UTF-8 and finite admission
The host SHALL admit at most 16 MiB per retained source and return at most the
requested 4..16384 bytes per page with a continuation byte offset and total size.

#### Scenario: Unicode boundary
- **WHEN** the requested page boundary intersects a multibyte code point
- **THEN** the end backs up to a valid boundary without losing or duplicating bytes
- **AND** an offset inside a code point is rejected

#### Scenario: Retained command output was truncated
- **WHEN** the command capture already discarded bytes
- **THEN** pages expose only retained result JSON including its truncation metadata
- **AND** the host does not claim discarded output is available

### Requirement: Model projection preserves durable and protocol evidence
The host SHALL provide bounded model views while retaining original public
transcripts, ledger results, tool/result identity and existing uncertainty gates.

#### Scenario: Large result and completed child snapshot
- **WHEN** an ordinary tool result exceeds 16384 bytes or children reach terminal states
- **THEN** model context contains bounded previews or reports and exact available evidence references
- **AND** small ordinary results remain identical and original public results remain intact

#### Scenario: Resume after a large result
- **WHEN** an authorized execution reconstructs its complete history tail
- **THEN** it applies the same projection before aggregate model admission
- **AND** preserves complete tool groups without replaying side effects or silently dropping rows

#### Scenario: Insufficient capacity or uncertain outcome
- **WHEN** the complete projected history cannot fit or an existing tool outcome is unknown
- **THEN** continuation refuses rather than sending a partial tool/result group or claiming completion