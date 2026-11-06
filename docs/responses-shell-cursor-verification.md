# Responses, command shell and streaming correction

This internal Windows candidate corrects the earlier workbench candidate's
Responses reasoning/tool rejection. That diagnostic was raised by the CLI
adapter before any tool executed; the shell was not its cause.

Complete Responses output items are persisted and replayed in provider order,
including assistant phase, encrypted reasoning and function-call identities.
Stateless requests use `store:false` and request encrypted reasoning. Opaque
items stay within the captured connection, endpoint and model. Switching
targets uses public text and normalized tool history. Malformed, duplicate or
oversized items fail before tools enter the permission and execution path.

The model-facing `run_command` defaults to Bash. On this Windows host Git Bash
is available. PowerShell and CMD require an explicit shell choice; missing Bash
returns a diagnostic. Existing command approval, Plan restrictions, output
limits and process-tree cleanup are retained. Goal verification's existing
native shell and the manually opened terminal remain compatible.

The composer footer omits the thinking label and spinner. Native cursor
visibility changes only when focus changes, and an unchanged frame writes
nothing. Streaming rendering coalesces adjacent deltas already in one bounded
pump and appends a safe row suffix without erasing its visible prefix. Unicode
cluster joins, style changes and resize fall back to normal redraw. Completed
Markdown lines retain the existing incremental cache; provider data is not
delayed through artificial character playback. Host EOF waits for queued
complete events to drain and rejects a truncated final event.

## Questions, pending messages and local shortcuts

Native `ask_user` accepts two to six labelled options. The question overlay
handles arrows and Enter, a custom-answer entry and Esc cancellation, without
changing the composer draft or approving tools. Legacy free-text questions
remain supported. Invalid options are rejected before display.

Messages submitted during generation remain in a bounded FIFO. A compact grey
preview appears above the composer. Esc first belongs to a focused overlay;
otherwise it recalls the newest queued message and merges an existing draft.
Ctrl+C cancels the active turn and pauses queued dispatch. A failed or cancelled
turn does not automatically dispatch a queued write.

`/history [SEARCH]` performs literal, project-scoped prompt search with a
100-record / 512 KiB bound. Enter inserts a prompt, without sending it. Ctrl+S
and `/stash` exchange the draft with a temporary UI-lifetime stash. `/copy code`
offers complete fenced code blocks, excluding fence markers. These operations
make no model requests.

## Images

Explicit PNG/JPEG path pastes and clipboard file references retain the original
file path. Numbered chips are blue and atomic: arrow keys cannot enter their
interior; Backspace/Delete removes a complete reference without deleting the
file. Labels remain stable across draft stash and queued-message editing.
Ctrl+V and Alt+V support clipboard input; terminal-consumed Ctrl+V may arrive as
a normal path paste. Pixel-only clipboard data has no original path and is
saved exclusively into system TEMP, with a status explaining the fallback.
The project does not receive an attachments directory or image copy.

Sending requires a configured vision-capable target. Up to eight images and
8 MiB total input are accepted, subject to bounded PNG/JPEG header and dimension
checks. The persisted transcript stores path, MIME, length and SHA-256; transient
request buffers contain the bytes encoded for Chat Completions, Responses or
Anthropic Messages. Python is only used by verification fixtures, not this path.
In `sencode-config`, the image button beside an enabled model controls that
model's image capability; enable it only when the endpoint supports image input.
The database connection projection preserves the non-secret enabled-model and
capability fields, so request preflight sees the same image setting as the
configuration workbench. A real database regression covers exact model matches,
connection denial, bounds and omission of raw configuration/credentials.

Image grants belong to the accepting session catalog. Imported project history
and branches require explicit attachment again. Missing or changed source
files pause the request instead of sending substitute bytes; old references
require their original bytes, or a new context that no longer includes them.
System TEMP images can likewise become unavailable after OS cleanup.

Native clipboard tests use isolated OS substitutes and real GDI+ conversion.
A private window station could not be created on this host (error 5), so live
clipboard integration remains unverified. Tests never read or overwrite the
user's interactive clipboard. The real console path-paste checks and loopback
provider image checks are separate evidence.

## Candidate and evidence

The final Windows x64 candidate is
`target/interactions-final-20261105-opt/sencode-sg.exe`, SHA-256
`ccfc3da145314e6143516abab169aa313a80eb97da506d0898589ba99969b823`.
It is built with `-O 2`, `source-development`; `release_eligible=false` remains
explicit. The source tree is dirty, with Sencode baseline
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a` and Sengoo baseline
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`. Full production input hashes and
compiler identity are in the candidate's `build-inputs.json`.

The final real-console gate passes 24 checks, including blue chip color,
one-Backspace deletion at the original paste cursor, missing-image draft
recovery, real image content on the wire, questions, pending insertion recall,
history/stash/copy, diff approval, checkpoints, exit restoration and resume.
Four actual loopback SSE streams produce p95 input latency **22.7401 ms** over
40 samples (maximum **25.395 ms**). Growing Markdown shows 29 intermediate
updates with p95 visibility lag **63 ms** and maximum **94 ms**. These are local
Windows console measurements, not guarantees for other terminal hosts.

The package is
`target/packages-interactions-20261105-opt/sencode-cli-0.1.0-dev.0-windows-x64.zip`,
SHA-256 `be59484d9fd1decb4948b89ba28d3bd562f72fb1b3b2b38af7592b0ff765ab87`.
The `fullscreen.json`, `integration-acceptance.json` and `install-smoke.json`
in the final candidate directory record their separately executed gates.
Loopback fixtures do not qualify a real provider service or official account.

All six public/host suites pass on that exact executable: Responses tools,
external CLI read/patch/test and Plan/Goal, management policy, portable project
history, execution host, and request recovery. The isolated install smoke
checks both aliases with a System32-only dependency PATH, an existing command
directory, Unicode cwd, no-argument startup and resume shortcuts. It is not a
fresh Windows VM qualification.

The candidate is installed at `D:/SencodeCLI`; installed `sen.exe` and
`sencode.exe` match the candidate SHA-256. Both report
`sencode 0.1.0-dev.0 (Sengoo native)` and preserve `resume`, `-c`, and `-r` in
their help. `installed-verification.json` records the resolution and hashes.
No commit, push, real-provider request or user-project edit was performed.

Independent component evidence:

- `target/interaction-render/evidence.json`: native TUI regression, exact
  frontend branch probes and complete frontend type check.
- `target/render-latency/evidence.json`: final native TUI regression and paired
  measurements for skipping image-token work in ordinary text input. Native
  frame timing excludes console writes and is not the 50-ms acceptance gate.
- `target/image-reference-evidence.json`: three-protocol original-file image
  conversion, resource rejection paths, local history and branch grants.
- `target/clipboard-attachment/path-evidence-final.json`: Unicode original-path
  recognition and no image copy, without clipboard access.
- `D:/Sengoo/target/clipboard-image/evidence.json`: clipboard OS-boundary
  fixtures, real GDI+ conversion, and the explicitly unqualified private station.
- `D:/Sengoo/target/encoding-bounded-evidence.json`: opt-in bounded Base64,
  legacy compatibility and an independent Rust integration harness.

The changed Sencode OpenSpec passes strict validation. The repository-wide
run also records three unrelated existing failures in `add-fusion-selection`,
`add-git-workspace-management` and `add-grok-desktop-backend`; it is not labelled
an all-pass gate. Sengoo's full strict run passes 66 items.

Two unoptimized v5 console runs missed the four-stream input target (p95
55.57 ms and 67.11 ms). Their failed evidence remains in
`target/interactions-final-20261105-v5/`. The install candidate is built with
`-O 2` and includes the no-image fast paths; its complete console gate is
recorded separately. No threshold or sample count is relaxed.
