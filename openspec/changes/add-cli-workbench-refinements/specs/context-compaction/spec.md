## ADDED Requirements

### Requirement: Sencode-aligned occupancy policy and complete tail selection

The native API engine SHALL estimate context occupancy locally and trigger
automatic compaction at 85 percent by default, target 50 percent occupancy, and
retain whole conversational units by serialized byte budget. The estimate SHALL
be labelled as a local estimate rather than provider usage or remaining quota.
Schema 1 configuration SHALL remain readable; explicitly configured older
thresholds SHALL be retained and missing optional fields SHALL use new defaults.

#### Scenario: Automatic and manual compaction use different triggers

- **WHEN** estimated occupancy remains below the trigger and the input byte
  ceiling has not been reached
- **THEN** an automatic check SHALL NOT send a summary request
- **AND** an explicit manual compact operation MAY request reduction below the
  automatic threshold when there is a reducible older prefix

#### Scenario: Older low thresholds remain readable

- **WHEN** a schema 1 document declares a trigger from 1 through 50 percent and
  omits target_percent
- **THEN** the target SHALL adapt to half of the trigger with a minimum of 1%
- **AND** the legacy 1% trigger MAY use an implicit equal 1% target
- **AND** explicitly configured targets SHALL still be below their trigger

#### Scenario: Uneven history retains units by size

- **WHEN** recent units have different serialized sizes
- **THEN** the retained tail SHALL be chosen against the target budget rather
  than a fixed number of messages
- **AND** an assistant tool-call group and every matching tool result SHALL
  remain indivisible, including out-of-order results within the same group

#### Scenario: Incomplete or malformed tool relationships cannot be compacted

- **WHEN** tool calls are unresolved, duplicated, orphaned or have invalid ids
- **THEN** the engine SHALL reject compaction without changing active context
- **AND** it SHALL NOT create an artificial tool result to repair the history

### Requirement: Compaction results are fenced to their exact source snapshot

The engine SHALL bind each compaction plan to the SHA256 of its exact source
context, the current true user-message identity and a complete unit boundary.
It SHALL preserve the original system and project instructions verbatim, retain
the current user task, and mark the continuation summary as historical data.

#### Scenario: A same-count edit occurs during summarization

- **WHEN** any source message changes after a summary plan is created even if
  message count remains the same
- **THEN** validation SHALL reject the stale result with conflict status
- **AND** the changed source SHALL NOT be overwritten by the old summary

#### Scenario: A generated summary is not a new user task

- **WHEN** previously compacted history is compacted again
- **THEN** the summary carrier SHALL NOT replace the latest real user task
- **AND** the summarization prompt SHALL require still-relevant prior
  continuation facts, exact paths, evidence and uncertain side effects

### Requirement: Summary cleaning and quality precede context replacement

The engine SHALL strip leading drafting blocks and summary wrappers, neutralize
control tags quoted in substantive sections, and preserve substantive numbered
sections. The default accepted summary SHALL contain at least 500 Unicode
scalars, fit its planned byte allowance, and produce at least 20 percent
serialized-history reduction. These numeric limits MAY be explicitly configured
within validated bounds.

#### Scenario: A valid summary contains private drafting

- **WHEN** a summary response contains a leading analysis block and a valid
  substantive summary
- **THEN** only the cleaned substantive summary SHALL enter model context
- **AND** private drafting SHALL NOT enter the visible transcript or text stream

#### Scenario: The provider returns a short or ineffective summary

- **WHEN** the summary is too short, malformed, oversized or insufficiently
  reduces context
- **THEN** the engine SHALL reject the replacement and pause the current Goal
- **AND** it SHALL retain the old active context and previous durable checkpoint
- **AND** it SHALL NOT silently issue an extra quality-retry request

### Requirement: Durable replacement preserves public history and accounting

The execution owner SHALL persist a fenced context checkpoint before replacing
the active owning JSON document. It SHALL retain the public transcript and all
cumulative request accounting. Internal summary requests SHALL use the same
connection snapshot, scheduler admission and Goal request budget as ordinary
requests, without appearing as public assistant messages. A compaction phase
event SHALL allow the frontend to display progress separately from thinking.

#### Scenario: Repeated compaction replaces the owning document

- **WHEN** multiple compaction cycles complete successfully
- **THEN** each committed active context SHALL use a fresh owning JSON document
- **AND** unreachable nodes in an older document arena SHALL NOT accumulate
- **AND** the public transcript SHALL still contain the original user turns

#### Scenario: A summary request fails or the process restarts

- **WHEN** summarization fails or the execution host restarts after a prior
  successful checkpoint
- **THEN** the previous complete checkpoint and public history SHALL remain
- **AND** resume SHALL retain cumulative ordinary and summary request counts
- **AND** unknown tool outcomes SHALL NOT be replayed by compaction

#### Scenario: Backend capability does not support native context replacement

- **WHEN** a managed engine owns its own model context and compaction behavior
- **THEN** the native API compaction rules SHALL NOT claim to control that engine
- **AND** the workbench SHALL use its declared capability or show its limitation
