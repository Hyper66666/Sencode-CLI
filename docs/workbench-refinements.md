# Workbench refinements

The fullscreen CLI uses an original monochrome pixel wordmark with a two-cell
extrusion. Narrow terminals use the compact wordmark. Thinking and compaction
have separate animations; incremental repaint preserves the draft and history
reading position. `NO_COLOR` keeps readable markers without renderer colors.

`/model` opens enabled models grouped by connection, with two connection columns
on wide terminals. Up/down stays in the current channel, left/right changes
channels, and typing filters the catalog. Enter opens the effort list; a second
selection commits connection, model and effort together for future requests.
The current tuple stays selected. Provider default clears an explicit effort.
Native protocol encoders support the desktop effort vocabulary; individual
remote models can reject a level. Explicit configured capability restrictions
are checked again by the execution host before network access. Managed account
backends currently expose provider default only.

Native write and patch approvals show unified snippets from complete files, with
actual old/new source line numbers. Removed lines are red, added lines green,
and unchanged context retains both line numbers. Page Up/Down scrolls an approval
preview. Denial keeps the file unchanged; successful edits add an EDIT card.
Diff previews are bounded to 128 KiB of combined source and replacement and
8,192 lines per file. A changed middle range is one deterministic hunk with three
context lines on either side. Shell and managed-runtime changes do not fabricate
native edit cards.

Chinese-leading Markdown, emoji and non-heading hash prefixes no longer create
invalid one-byte UTF-8 strings. A request failure remains visible in the
workbench. If the host fails, queued tasks pause and owned processes are cleaned
up before an explicit `/resume` or `/new`. Reconnection never replays tools.

See [model selection](model-selection.md) for wire mappings and
[context compaction](context-compaction.md) for continuation and quality gates.
Scheduling uses bounded read blocks, preserves declared result order, and puts
exclusive writes and commands behind barriers. Hardened Git reads use actual
pollable process jobs; configured hooks take the existing serial path. Canceled
workers retain their permits until process-tree quiescence and usage accounting
are confirmed. Local file reads remain bounded synchronous operations in the
execution host; the separate frontend continues accepting input.

Verification uses temporary workspaces, loopback providers, temporary credentials
and actual hidden Windows console cells/attributes. Provider fixtures, native
module checks and installed-package checks are recorded separately. No private
user project, connection or conversation is modified by these tests.
