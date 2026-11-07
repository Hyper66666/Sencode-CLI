## Why

One-second child snapshots repeatedly wake the parent model with unchanged or
partial results. Consecutive waits also clutter the transcript. Composer recall
is process-local and fullscreen mouse reporting has no text selection.

## Capabilities

- Gate child-only parent continuations on terminal progress; deliver complete
  child results once and retain responsive cancellation and shared budgets.
- Collapse consecutive coordination calls, retaining expandable call details
  and visible failures.
- Save the latest ten submitted inputs per session in portable project history.
- Select rendered output with the mouse and copy the highlighted text.

## Non-Goals

No new team execution mode, provider-text rewriting, provider qualification or
shared global prompt history. Agent and rendering behavior remains Sengoo-owned.
