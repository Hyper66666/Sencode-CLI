# Session, diagnostics and reading repair

The first nonempty visible user message gives an ordinary session its title.
Whitespace is collapsed and the title is limited to 30 Unicode scalars, matching
the desktop. Manual names and branch names remain authoritative. Ordinary
history and resume queries filter empty sessions and positively identified child
sessions before sorting and limiting results. `/agents` has a separate catalog.
Legacy records without reliable child provenance are retained. The project-local
`.sencode/history.sqlite3` identity remains independent of the root folder name.

Consecutive file reads, directory listings and searches appear as one collapsed
exploration group. Its counts describe distinct completed operations. Click the
heading or press Ctrl+O to expand details; failed operations remain visible.
Answering, writing or running a command ends the group. Expansion follows stable
tool IDs, so streamed updates and resizing do not reset it.

Diffs use line-level changes with three context lines around each hunk. A heading
such as `Edited path (+2 −2)` precedes grey line numbers, red deletions and green
insertions. Change lines have no solid background. The bounded comparison marks
oversized cases as simplified; a simplified summary cannot authorize a write.
Narrow the edit and request a complete preview instead.

An active main or child conversation ends in `Thinking` only when the provider
reports an explicit reasoning phase. Other work uses `Working`; approvals show a
static waiting state. Completed and stopped turns retain a grey elapsed note.
History restoration does not restart an animation. The composer stays static,
with one blank display row above it. `NO_COLOR` disables semantic color spans.
Short conversations begin below the top header, with unused space following
their messages. See [provider layout and search](provider-layout-and-search.md)
for supplier grouping, permission colors and the bundled search tool.

Known command exits, provider failures, cancellation, request budgets and unknown
tool outcomes have separate diagnostics. Ordinary command errors return to the
model; unknown side effects and incomplete cleanup pause without replay. See
[execution diagnostics](tool-output-diagnostics.md) for the compatible result
fields, and [Responses continuation](responses-end-turn.md) for the GPT/Codex
task-continuation contract.

Acceptance evidence distinguishes native checks, isolated loopback provider
tests, owned real Windows console tests, installation smoke checks and live
services. A synthetic service is not evidence of a live provider succeeding.
