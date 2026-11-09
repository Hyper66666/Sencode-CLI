## ADDED Requirements

### Requirement: Evidence digest admission matches source admission
Evidence references and page verification SHALL use exact-source SHA256 with the
existing explicitly bounded 16-MiB source admission, independent of the legacy
small-identity hash default.

#### Scenario: Successful child tool returns more than 64 KiB
- **WHEN** an authorized completed child result contains 106138 bytes
- **THEN** model projection produces a valid preview and exact-source reference
- **AND** the parent and child continue without a legacy hashing argument error

#### Scenario: Evidence pages preserve authority and version
- **WHEN** an authorized requester reads multiple pages of a retained large source
- **THEN** each page verifies the same full-source digest and valid UTF-8 boundary
- **AND** changed, missing, unrelated or oversized sources do not run any tool again

### Requirement: Child coordination failures name their local stage
The controller SHALL distinguish local child projection/context failures from
shell failure, user cancellation and provider/network failure.

#### Scenario: Child projection fails after a committed tool result
- **WHEN** projection or child-context insertion fails
- **THEN** the parent records child task, tool and closed host stage and shows a specific diagnostic
- **AND** committed results remain retained and no completed tool is replayed
