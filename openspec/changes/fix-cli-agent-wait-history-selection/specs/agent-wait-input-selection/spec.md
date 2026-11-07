## ADDED Requirements

### Requirement: Child waits resume on terminal progress
The controller SHALL avoid repeated parent model requests for unchanged child
status and SHALL not present partial child text as final results.

#### Scenario: Slow children with interim text
- **WHEN** a parent has finished independent work and children stream partial text
- **THEN** the host pumps children without repeated parent requests and resumes
  once with terminal child results while cancellation and budgets remain active.

#### Scenario: Repeated explicit coordination calls
- **WHEN** a blocking wait batch completes without new terminal results
- **THEN** another coordination-only parent request waits for meaningful child
  progress and the UI shows one expandable coordination group with failures visible.

#### Scenario: Explicit nonblocking status inspection
- **WHEN** the parent uses list_agents or an explicit zero-timeout wait
- **THEN** the current snapshot returns without waiting for task completion.

### Requirement: Input recall is bounded and session-scoped
The CLI SHALL retain at most ten submitted inputs for the current session and
restore them after normal exit. Other sessions and new branches SHALL not
inherit that recall ring.

#### Scenario: Restart and switch
- **WHEN** inputs are submitted, the CLI closes and the session resumes
- **THEN** Up/Down navigates its latest ten inputs and restores the unsent draft
  without borrowing entries from another session.

### Requirement: Output supports text selection and copy
The fullscreen UI SHALL support mouse drag selection and explicit clipboard
copy of rendered output without changing the composer or cancelling a request.

#### Scenario: Unicode selection during generation
- **WHEN** a user drags across Chinese, emoji or combining characters while output streams
- **THEN** complete graphemes are highlighted and copied from a stable visible
  snapshot; Esc clears the highlight before it can cancel the request.

#### Scenario: Click and focus boundaries
- **WHEN** a user clicks without dragging, resizes or opens an approval
- **THEN** no text is copied and stale selection targets cannot operate on the
  composer or an interaction overlay.
