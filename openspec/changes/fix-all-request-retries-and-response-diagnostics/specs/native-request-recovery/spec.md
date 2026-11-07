## ADDED Requirements

### Requirement: Five retries for every native model request failure
The controller, child agents and consultation SHALL allow five retries after
the initial failed model request regardless of HTTP status or stream progress,
while preserving cancellation, permissions, execution ownership and budgets.

#### Scenario: HTTP 400 and HTTP 200 partial responses
- **WHEN** a model request fails with HTTP 400 or a partial HTTP 200 response
- **THEN** up to six total attempts use the same provider and accepted history
- **AND** retry events show progress and do not execute any completed tool again

#### Scenario: Cancellation and budget exhaustion
- **WHEN** the user cancels or the existing execution budget cannot admit more requests
- **THEN** retries stop, cleanup finishes and the task remains resumable

### Requirement: Failed attempts remain provisional
An unaccepted streaming answer SHALL be replaced on retry in both live UI and
stored history, without deleting completed messages or tool results.

#### Scenario: Stream fails twice before success
- **WHEN** two attempts emit text but fail validation and the third succeeds
- **THEN** only the third answer becomes canonical and the user's draft survives
- **AND** a completed tool preceding the requests executes exactly once

### Requirement: Successful HTTP status cannot mask a response error
Failure reports SHALL identify transport/protocol stages and closed provider
error categories, with HTTP 2xx shown only as secondary response context.

#### Scenario: Truncation or provider failure after HTTP 200
- **WHEN** the body, SSE event or provider response is incomplete or reports failure
- **THEN** the final diagnostic includes the error category, stage and retry count
- **AND** persisted attempt evidence contains no raw provider error body or credentials

### Requirement: Windows batch output uses executable line endings
Built-in .bat/.cmd writes SHALL use CRLF without BOM, and permission preview
SHALL reflect the same resulting content.

#### Scenario: Mixed line endings and a Unicode workspace
- **WHEN** a batch file is created or patched with LF or mixed line endings
- **THEN** normalization is idempotent and execution from a Unicode path with spaces preserves commands
- **AND** other file types retain their original content
