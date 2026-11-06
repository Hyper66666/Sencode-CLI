# CLI Responses tools, Bash execution and cursor timing

## Capabilities

Repair native OpenAI Responses turns that contain reasoning items followed by
function calls, so a validated tool call can continue through the normal
permission, scheduling and history pipeline. Make model-issued shell tools
prefer a bounded Bash process on Windows (Git Bash when installed, then other
available Bash installations), with explicit PowerShell/CMD selection and clear
shell attribution in results. Stabilize the TUI composer cursor, remove the
redundant thinking animation/text row below the composer, and reduce growing
response render work to keep streamed text and input responsive.

The model clarification tool also gains bounded answer options, keyboard
selection and explicit custom answers, with cancellation kept distinct from
both an answer and a permission grant.

Busy-turn submissions are shown as a compact grey pending preview above the
composer. Esc retracts the most recent pending message into the composer before
it can be sent, while preserving an already edited draft. Ctrl+C retains the
explicit active-turn cancellation behavior.

Three local conveniences complete this interaction batch: project-scoped prompt
history search, session-local draft stashing, and a selector for copying complete
fenced code blocks from the latest assistant answer. These operations do not
call a model or authorize tools.

Explicitly pasted original PNG/JPEG paths become blue atomic image chips. The
composer keeps file references and transmits validated image bytes to a capable
model only on submission. Pixels without an original file path use system TEMP;
the project receives no image copies. The Sengoo terminal boundary supplies
clipboard snapshots and conversion, while a bounded opt-in Base64 encoder
supports ordinary screenshots without changing the legacy encoding ABI.

## Non-Goals

This change does not add a new provider, alter API credentials, run tools
without the existing permission policy, or change the manually operated
`/terminal` pane. WSL is not silently introduced as a dependency. Provider
reasoning data is treated as untrusted opaque protocol data and is bounded
before being persisted or sent back.

## Ownership and dependencies

The provider owner owns Responses item capture and request-history encoding.
The executor owner owns Bash discovery, process lifecycle and shell metadata.
The TUI owner owns cursor visibility state, redraw cadence and composer rows.
The integration owner owns fixtures, OpenSpec validation, final candidate
builds and evidence. The change depends on the existing provider, scheduler,
process-tree cleanup and fullscreen console contracts.
