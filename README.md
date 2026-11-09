# Sencode CLI

Sengoo-native terminal coding agent for Windows x64. The conversation loop,
provider adapters, HTTP/SSE framing, tools, policy, Plan, Goal, MCP and terminal
editing are implemented in `.sg` source. Sengoo supplies generic TLS, process,
terminal, credential-store and SQLite interfaces.

This is a development candidate. Test configuration and test fixture source are
not release evidence; consult the recorded acceptance results before distributing
a build. The existing `sencode` Rust runtime remains a separate product binary.

## Build from source

Keep the two checkouts adjacent. This snapshot requires Sengoo revision
[`86c6f87975646b91c9cf2d7d069ac06ee4243b9b`](https://github.com/Hyper66666/Sengoo/commit/86c6f87975646b91c9cf2d7d069ac06ee4243b9b)
for its compiler and native runtime interfaces:

```powershell
git clone https://github.com/Hyper66666/Sengoo.git
git clone https://github.com/Hyper66666/Sencode-CLI.git
cd Sengoo
git checkout 86c6f87975646b91c9cf2d7d069ac06ee4243b9b
cargo build --locked -p sgc -p sgpm
cd ../Sencode-CLI
```

Build the matching Sengoo `sgc` and `sgpm`, make Clang and the Windows SDK/MSVC
linker environment available, then run:

```powershell
./scripts/build.ps1 -SengooRoot D:/Sengoo
./target/sencode-sg.exe --help
./scripts/test.ps1 -SengooRoot D:/Sengoo -Python C:/path/to/python.exe
```

The paths passed to build scripts are developer inputs. Distributed applications
must not contain a dependency on either source checkout. An installed CLI uses
only its executable and bundled native dependencies; it does not invoke a
compiler or package manager.

The React/Tauri configuration companion lives in `sencode-config/`; run
`npm ci` there before its build. Optional desktop sharing and managed account
runtimes are described in [desktop integration](integrations/desktop/README.md).
See [source provenance](docs/source-publication.md) for the extraction baseline
and which validation results apply to this source snapshot.

## Working with a project

```powershell
sen
sen --cwd C:/projects/example -p "Explain the build" --output-format json
sen resume
sen resume SESSION_ID
sen -c
sen -r "search title"
```

`AGENTS.md` and `CLAUDE.md` contribute project instructions. File reads are
bounded UTF-8 operations. Patches replace exactly one matching old fragment;
overwriting an existing file requires its expected contents, so stale edits fail.
Model and tool text is stripped of terminal control characters before rendering.
Read-only Git tools disable fsmonitor hooks, clean/process filters, external
diffs, text conversion and pagers. They omit submodule inspection and resolve
Git from an absolute PATH entry outside the project. Repositories with filter
names containing `=` are rejected before inspection.

`sencode` is an equivalent installed command. `sencode-sg.exe` is the development
binary. Without arguments, a conversation starts in the current directory;
`resume` without an ID chooses that project's most recent session.

Portable conversation history is stored in the project's
`.sencode/history.sqlite3`, with a stable project identity so renaming an idle
root retains its sessions. See [project history](docs/project-history.md) for
recovery, explicit imports and the shared desktop catalog boundary.
Resuming a session restores its last chosen supplier, model, thinking level and
permission mode, including a choice made without sending another message. See
[session selection memory and scrolling](docs/scroll-session-memory.md) for overrides
and recovery behavior.
The source review of [Grok Build](docs/grok-build-design-review.md) records the
input, rendering and scrollback ideas being applied here.

## Terminal interface

The default TTY interface is a fullscreen workbench with restrained semantic colors and an original
centered SENCODE mark, fixed composer, scrollable conversation and model status.
`--tui scrolling` retains the earlier scrollback interface; `--tui plain`,
`TERM=dumb` and redirected output use plain text. JSON output contracts remain
available. The frontend and an owned foreground execution host communicate over
bounded JSONL pipes. Explicit native API jobs also support authenticated local
named-pipe attach and bounded durable logs; see [background jobs](docs/background-agent.md).

Sessions use their first valid user message as the automatic title; ordinary
resume lists omit empty and identified child sessions. Consecutive exploration
tools collapse into expandable groups, diffs show individual changed lines, and
activity stays at the end of the conversation. See [session and reading behavior](docs/session-reading-repair.md).
GPT/Codex-compatible Responses connections also honor explicit server task
continuation while retaining the same request budget; see [the continuation contract](docs/responses-end-turn.md).

Enter sends a message; Shift+Enter or Alt+Enter adds a line. Left/right and
Home/End move the cursor, up/down moves between display rows and recalls input
history at the edges while preserving a draft. Typing `/` opens a searchable
command menu. Up/down selects; Enter or Tab completes and closes the menu.
Only a separate submission Enter executes the completed command.
Ctrl+U clears back to the start and Ctrl+W removes the previous word. Ctrl+C
cancels and Ctrl+D exits an empty prompt. Paste and input are bounded at 64 KiB.
The composer edits Unicode 17 extended grapheme clusters, including combining
marks, emoji sequences and regional flags. Cell width remains a terminal/font
convention. Resize reflows the viewport and preserves the draft. `NO_COLOR`
disables styling. Markdown supports headings, bold/code spans, quotations,
fenced code with line numbers, diff markers and simple pipe tables; this is a
safe display subset rather than a full GFM or syntax-highlighting engine.
An empty composer contains no suggested text, both while idle and during a turn.

During streaming, draft editing and history browsing stay available. Submitting
a new message queues it for the next turn, shown in grey above the composer.
Esc recalls the newest queued message and preserves the existing draft;
Ctrl+C cancels the active turn. Open pickers and approvals block
automatic queue dispatch. Approval requires fresh input after the approval is shown;
previously typed or queued `yes` cannot authorize a side effect.

Model questions can present labelled choices: use up/down and Enter, choose
the custom-answer entry to type a response, or Esc to pause without answering.
`/history [SEARCH]` searches this project's prompts; Enter fills the composer
without sending. Ctrl+S or `/stash` temporarily stashes, restores or exchanges
the draft. The stash lasts until the UI exits. `/copy code` selects a complete
fenced code block from the latest answer.

Paste a PNG/JPEG path or use Ctrl+V/Alt+V for clipboard images. Original file
references appear as blue `[image1]`, `[image2]` chips. The cursor moves across
each chip as a unit; one Backspace removes the reference and leaves the file.
The CLI sends actual image content on explicit submission to a model whose
configuration advertises image support. Original images are never copied into
the project. Pixel-only clipboard content uses system TEMP because it has no
original file path. See [image and interaction behavior](docs/responses-shell-cursor-verification.md).

`/queue` or Ctrl+Q pauses automatic dispatch while you inspect, independently
edit or cancel queued tasks. Saving an edited item does not send it; explicitly
resume the queue. `/branch`, `/rename` and `/export` operate on idle sessions.
`/rewind` previews one native file checkpoint and defaults to cancel; external
file changes are conflicts. Command and managed-runtime effects are not undone.
`/config`, `/doctor` and `/memory` inspect effective settings, local readiness
and applicable instructions without editing them. Learned memory is pending.

`/keys` selects the default editor or an optional Vim subset. `/keys show` explains
the active bindings; custom composer bindings cannot override approval or overlay
keys. `/read` gives history independent reading focus and preserves the draft.
See [the keymap schema and supported Vim keys](docs/editor-keybindings.md).
`/terminal [powershell|cmd]` opens an explicitly approved user terminal while idle.
Ctrl+Q stops its process tree and returns to the draft. The pane is disabled in
Plan; see [terminal behavior and limits](docs/user-terminal.md).

The production Windows console gate measures key injection to visible composer
text during four independent loopback SSE streams: p95 45.10 ms over 40 samples
for the scroll/session-memory candidate. This is host-specific evidence, not a
guarantee for every terminal or external provider. See the
[candidate record](docs/scroll-session-verification.md) for the measured scope.

Default permissions allow built-in reads. File modifications display the
proposed text changes for approval; commands and MCP tools require approval. Headless mode
cannot answer interactive permission requests; a required approval pauses the
turn, exits with a nonzero code and reports `success: false` in JSON, including
ordinary conversations without a Goal. Use `--auto-edit` to authorize
workspace edits or `--allow-commands` to authorize arbitrary non-interactive
commands explicitly. Command execution is not an OS sandbox. Model tools execute
non-interactive commands; the separate explicit user-terminal pane supports a
bounded VT subset for interactive shells.

In the fullscreen composer, **Shift+Tab** cycles **手动审批 → 自动审批 →
完全权限**. The current mode stays below the input. Automatic approval covers
file edits; full permissions also authorize commands and MCP. A running turn
keeps its captured policy and the footer marks a changed selection for the next
turn. The shortcut cannot approve an open permission dialog. See
[permission modes](docs/permission-modes.md).

The model header includes its effective thinking effort, normally `medium`.
Use `/model` to choose another level or `--effort xhigh` at startup. Explicit
capability limits still apply. Each child Agent has one progress card rather
than printing its transport events. See the
[verification record](docs/agent-mode-controls-verification.md).

## Plan and Goal

`--plan` and `/plan` enable read-only planning. Only the session's exact plan file
may be written. Arbitrary commands and MCP calls are denied, including calls from
children; tool descriptions cannot bypass this restriction. Approval to execute a
plan is a human decision.

`--goal OBJECTIVE` enables a foreground goal. `--check COMMAND` specifies required
verification and may be repeated. `--max-requests` is optional (default unlimited; zero disables the cap) across the whole
goal, including child and verification requests. Exact `--token-budget` execution
is currently rejected because complete token accounting is not guaranteed by
every provider stream; the CLI does not silently substitute an estimate.
Provider-reported usage and local context estimates are distinct. A verifier
failure cannot be reported as completed; repeated identical failed verification
pauses the goal. Exiting or restarting requires explicit resume.

## Providers and concurrency

The first release targets API-key connections using OpenAI Chat Completions,
OpenAI Responses or Anthropic Messages. HTTPS is required except for loopback
test/development servers. Model discovery is optional; manual model identifiers
are supported. Redirects do not forward credentials. Provider errors never cause
silent selection of a different endpoint or model.

Managed account adapters target pinned Codex app-server 0.144.4 and Sencode ACP
0.2.102. A verified runtime must be bundled beside the application; credentials
remain owned by that runtime. Selecting an account does not authorize weaker
policy: explicitly choose `/permissions backend` or `--permission-profile backend`.
The actual backend policy is shown. Strict Plan, Goal, exact budgets, native
children, compact and consult are refused for account execution until their
guarantees can be enforced. Protocol-fixture qualification and live account
qualification are separate; see [the capability ledger](docs/local-parity.md).

## Sessions and file recovery

`/new`, `/rename`, `/branch` and `/export` manage public session history. Branches
preserve Goal counters and completed tool deduplication. Exporting to a file
requires confirmation. Native writes and patches retain up to 32 exact file
checkpoints within an 8 MiB encoded journal. `/rewind` previews one file restore
and defaults to cancel. External edits, active execution and Plan mode prevent
restoration. Reopening state never automatically reverses an interrupted edit.
Shell commands and managed account tools are not covered by these snapshots;
conversation history and budgets remain recorded after a file restore.

The native Responses adapter retains complete ordered output items, including
assistant phase and encrypted reasoning, across tool continuations and restart.
Opaque items are replayed only to their original connection, endpoint and model;
switching targets rebuilds public text and tool history. Malformed items stop
before tool execution. See [the correction evidence](docs/responses-shell-cursor-verification.md).

Model-issued `run_command` uses Bash by default (Git Bash on Windows).
Windows-specific commands can explicitly select `shell=powershell` or
`shell=cmd`; a missing Bash produces a diagnostic without changing syntax.
Permissions, Plan restrictions, bounded output and process-tree cancellation
continue to apply. The manually opened `/terminal` remains PowerShell/CMD.

Each accepted request captures a connection/model snapshot. Changing defaults
does not cancel existing requests. Child tasks use independent contexts and
inherit restrictive permissions. Read-only children and multi-model consultation
can run concurrently; write tasks in the same directory are serialized. The first
release does not automatically create or merge competing Git worktrees. Explicit
`sen worktree list`, `sen worktree create PATH [--branch EXACT_NEW_NAME]` and
`sen worktree remove PATH` are available for user-directed management. Mutation
requires fresh confirmation, or explicit `--yes` in automation, and is disabled
in Plan. See [worktree limits and safety](docs/explicit-worktrees.md).

## Local MCP and skills

The stdio MCP implementation negotiates protocol `2024-11-05` for tools, including
initialization, paginated discovery, calls, cancellation and bounded output. It
does not grant server-initiated sampling or filesystem access. Server processes
have separate stdout framing and stderr drainage. Remote MCP transports are not
part of this release.

File skills are discovered under `.sencode/skills` and `.agents/skills`, with
nearer project definitions taking precedence over user definitions. Invoking a
skill adds its `SKILL.md` instructions; it does not change tool permissions.

## Shared desktop state

The shared-state contract uses the same local SQLite database, Windows credential
targets and visible session history as a compatible desktop build. Only one end
may execute a session. The observing end can display persisted updates; handoff
requires an idle session or confirmed cleanup of the previous executor. An
expired heartbeat is not sufficient to take over a live process.

Upgrade both clients together. A database backup and an exclusive migration gate
are required before upgrading; old writers must be closed. Provider-native
bindings are engine-specific. Desktop Meeting/Fusion execution is not adopted by
the CLI. Sharing is limited to the same Windows user/logon session and local
disk, not network shares or cloud synchronization.

## Tests

`src/tests_core.sg`, `tests_protocol.sg`, `tests_http.sg` and `tests_workspace.sg`
exercise policy/goal transitions, all provider adapters, byte-fragmented SSE,
HTTP framing and stale-safe file edits.

`src/tests_terminal.sg` and `tests_views.sg` cover input/layout and public metadata
views. `tests/tui_console_fixture.py` drives an isolated hidden Windows console
with the real executable, synthetic state and native console input events. It
does not interact with a user's terminal. Select it using `-Cases tui`.

`tests/provider_fixture.py` runs a real local HTTP server for
`target/tests_transport.exe`, checking four simultaneous streams, authorization
headers, three wire protocols, Unicode escapes, chunked transfer and incremental
tool arguments. `tests/mcp_fixture.py` is a deterministic stdio MCP test server.
Python is used for test fixtures only, never application execution.

The default `scripts/test.ps1` runs all named native and integration cases and
writes JSON evidence, logs, repository revisions, source hashes and the actual
compiler/executable SHA-256 under `target/acceptance/`. Provide a real interpreter
path with `-Python`; WindowsApps aliases are rejected. `-NativeOnly` selects the
explicit native subset; `-Cases core,mcp,cli` selects an explicit smaller scope.
Omitted cases are listed by scope and are not reported as passes.

`tests/cli_fixture.py target/sencode-sg.exe` uses a temporary database and a
temporary, unique Windows Credential Manager entry. It runs the real executable
outside the source tree to check read → patch → command → resume, redirected
interactive input, Plan denials, and host-verified Goal completion. The credential
is deleted on exit. `src/tests_mcp.sg` validates the stdio fixture's handshake,
pagination, raw Unicode fragmentation, bounded stderr and call timeout.
