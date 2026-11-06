## ADDED Requirements

### Requirement: Public history never silently truncates

The state layer SHALL return complete history or an explicit resource error.
It SHALL provide absolute count/range/tail queries and report total count and
offset for every successful history document. Resource admission SHALL occur
before allocating oversized row text.

#### Scenario: A session contains more than 1000 messages

- **WHEN** a 1105-row session fits the public document admission
- **THEN** complete history SHALL include all 1105 rows and its newest message
- **AND** a range starting at 1000 SHALL return the requested later rows
- **AND** a tail starting at 1100 SHALL return all five newer rows in order

#### Scenario: The complete transcript exceeds a document bound

- **WHEN** node or byte admission prevents returning complete history
- **THEN** the query SHALL fail 13 instead of returning a successful prefix
- **AND** the transcript and newest message SHALL remain unchanged

### Requirement: Recent windows are a separate presentation projection

The recent query SHALL anchor at the newest message, preserve ascending order
and report its actual offset and full count. Only resource failures MAY shrink
the window; strict model/history APIs SHALL NOT use this behavior.

#### Scenario: Rich recent rows exceed JSON node admission

- **WHEN** a 512-row UI request exceeds document admission
- **THEN** a smaller newest window SHALL be retried and its actual offset reported
- **AND** an oversized single newest row SHALL fail explicitly
- **AND** malformed JSON SHALL remain an error rather than hiding older rows

### Requirement: Checkpoint restore uses absolute complete canonical tails

The controller SHALL validate checkpoint `messages_seen` against the SQL count
and combine retained checkpoint messages with every newer public row. It SHALL
validate canonical assistant/tool-result pairing and enforce 1000-message and
786432-encoded-byte model admission without clipping history.

#### Scenario: A compacted session resumes beyond the old query limit

- **WHEN** a valid checkpoint has consumed 1103 public rows and later rows form a tool unit
- **THEN** restore SHALL retain the checkpoint and the complete newer unit
- **AND** reopening after another appended message SHALL include that newest tail
- **AND** cumulative budget fields SHALL remain unchanged

#### Scenario: A checkpoint begins at an orphan result

- **WHEN** the checkpoint/tail combination lacks a matching assistant tool call
- **THEN** restore SHALL fail without submitting malformed context or replaying a tool

#### Scenario: An old uncheckpointed session exceeds admission

- **WHEN** canonical model context cannot fit its count or byte bound
- **THEN** execution SHALL fail 13 with an explanation that public history remains intact
- **AND** no partial context or incomplete summary SHALL be submitted

### Requirement: Count pressure compacts before structural exhaustion

The controller SHALL request normal canonical compaction at 850 messages even
when byte/token thresholds are not reached. A successful checkpoint SHALL use
the absolute SQL public count and preserve cumulative request/token accounting.

#### Scenario: A long compacted session has 900 small new messages

- **WHEN** 1900 public rows restore into a checkpoint plus 900 small newer rows
- **THEN** automatic compaction SHALL run through the existing provider request path
- **AND** `messages_seen` SHALL become 1900 even if full public history exceeds JSON admission
- **AND** one summary request reporting 101 tokens SHALL add exactly one request and 101 tokens
- **AND** reopening SHALL reconstruct the exact reduced context and accumulated budgets
