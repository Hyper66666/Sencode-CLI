## ADDED Requirements

### Requirement: Evidence-based native retry
The native engine SHALL bound and cancel individual request retries and SHALL
charge each attempt to the shared request budget. It SHALL preserve connection
identity and distinguish provider-reported usage from unavailable usage.

#### Scenario: Provider asks for bounded backoff
- **WHEN** an attempt receives 429 or retryable 5xx before streaming
- **THEN** the coordinator honors a valid bounded Retry-After, polls cancellation,
  and retries at most twice using fresh attempt IDs and the same provider target.

#### Scenario: An attempt may already have effects
- **WHEN** streaming started or transport cannot prove no request was emitted
- **THEN** the failed attempt stops without automatic request or tool replay.

#### Scenario: Backoff is canceled or over budget
- **WHEN** cancellation, request limits or excessive server delay applies
- **THEN** the engine stops and persists observed usage without starting another attempt.

### Requirement: Native context reduction preserves execution facts
The native engine SHALL automatically summarize complete historical units under
model-scoped or explicit limits, retain original public history and recent tool
pairs, and preserve cumulative Goal accounting outside the reduced context.

#### Scenario: Native context reaches its configured threshold
- **WHEN** an active native request would cross its local estimate or byte cap
- **THEN** a shared-budget summary request produces and checkpoints a smaller
  valid context before execution continues and emits one automatic-compact notice.

#### Scenario: Tool continuation or summary is incomplete
- **WHEN** history has unresolved tool calls or compaction fails validation
- **THEN** no tool block is truncated, the previous context checkpoint remains
  valid, and execution pauses with a reason.

### Requirement: Opaque Responses state remains opaque
Validated Responses continuation SHALL preserve canonical public output items
without reconstructing reasoning state or changing host tool authority.

#### Scenario: Reasoning output precedes a host function call
- **WHEN** documented completed output provides the required continuation items
- **THEN** the next Responses request sends those items unchanged alongside the
  matching function output, and unsupported state is rejected before execution.
