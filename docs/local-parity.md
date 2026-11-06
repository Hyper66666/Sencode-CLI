# Local CLI capability ledger

Architecture reference: reconstructed Claude Code 2.1.88. Public local comparison
baseline: official changelog 2.1.318, frozen for this implementation. This ledger
describes work, not a claim of complete parity. `planned` means unavailable.

| Capability | API-native starting point | Managed account | Phase / owner |
| --- | --- | --- | --- |
| Fullscreen, centered home, composer, completion | implemented; stable cursor, incremental row updates and production console evidence in [the interaction record](responses-shell-cursor-verification.md) and [tool timeline record](tool-timeline-verification.md) | shared frontend | P1 UI |
| Continuous host events, cancellation, approvals | foreground JSONL host; real pipe/provider/process fixtures | both pinned protocol adapters pass isolated fixtures | P1/P2 core |
| Three API wire protocols | deterministic fixtures pass in prior candidate | not applicable | P2 core |
| Official account routing | not applicable | Codex 0.144.4 and ACP 0.2.102 actual offline initialize pass; live login/turn unverified | P2 core/root |
| Strict Plan, foreground Goal, shared budgets | request counters tested; exact token-budget requests refused pending complete accounting | strict modes refused; explicit backend-policy consent required | P2 core |
| Automatic compaction, safe retries, reasoning continuation | coordinator/summary retry and model-scoped compaction pass; Responses ordered reasoning/tool continuation and target-scoped history implemented; parallel sampling retry remains unavailable | backend-dependent | P2 core |
| Session branch, rename, export | implemented; native session fixtures | host-owned public metadata | P3 root |
| Native file checkpoints / rewind | approved native write/patch connected; real console restore/default-cancel/external conflict pass | runtime tool snapshots unavailable | P3 root/core |
| Explicit worktrees / full conversation rewind | user CLI list/create/remove with exact preview, clean-only removal and workspace locks implemented; automatic model worktrees and full conversation rewind pending | explicit user management only | P3 child/root |
| PTY, images/PDF, clipboard media | approved PowerShell/CMD pane with Sengoo VT screen; blue atomic original PNG/JPEG references and three-protocol image input implemented; automatic PDF extraction pending | explicit user pane; unverified image contract refused | P3 foundation/root |
| Editor keymaps, Vim subset, reading focus | /keys and /read implemented; native and actual-console editor checks pass | shared frontend | P1/P3 UI |
| LSP and IDE bridge | planned | adapter-dependent | P3 child |
| MCP transports/OAuth/resources/prompts/elicitation | stdio tools subset | adapter-dependent | P4 child |
| Hooks, plugins and Sengoo executable SDK | native worker/v1 manifests, fingerprint review, fresh launches, pre/post hooks and durable outcomes pass isolated fixtures; public management passes private-candidate tests; full plugin SDK pending | native worker hooks refused by unsupported engines | P4 child |
| Memory/config provenance/search integration | read-only /memory, /config, /doctor show instructions/effective local sources; learned memory and search integration pending | allowlisted metadata only | P4 child |
| Durable children, teams and task dependencies | one-level native children exist | planned | P5 core/child |
| Workflows, monitors, loops | planned | gated by tool/budget support | P5 child |
| Explicit background jobs and attach | native API start/list/attach/logs/stop implemented; cursor gaps, identity, approval loss, Goal pause and process cleanup tested; ordinary foreground host retains JSONL pipes | unavailable | P5 core/root |
| Clean-machine delivery and rollback | isolated package, executable-only directory, stale-PATH aliases, resume and rollback checks pass; fresh Windows VM remains unqualified | pinned runtimes packaged; live account turns unqualified | P6 root |

Cloud, mobile handoff, voice, browser/computer control and direct Claude JS/TS
Mod compatibility are outside this round. Windows is first; POSIX is unverified
until separately executed. Foreground Goals pause on exit. Native requests
default to manual approval. Shift+Tab cycles manual, automatic file edits and
full permissions; this automatic mode is edit approval, not a model-based risk
classifier. See [permission modes](permission-modes.md). Strict Plan and
read-only children remain restricted in every mode. Managed accounts retain
their backend policy and reported capabilities.

Sengoo foundation evidence is described in `D:/Sengoo/docs/local-terminal-ipc.md`,
`docs/unicode-graphemes-and-file-hash.md` and `docs/string-iterator-ownership.md`.
Windows native tests cover same-user IPC, nonblocking stdin backpressure,
Unicode 17 grapheme cases, bounded file hashes and iterator Drop/handle safety.
Clipboard conversion uses isolated Win32 stubs; a real clipboard integration
test is not claimed. Explicit Agent jobs use the native named-pipe layer;
ordinary foreground workbench sessions do not yet support detach/reattach.

Baseline artifact: `target/fullscreen-baseline.json`, generated by
`scripts/record-baseline.ps1`. Final evidence must also include source hashes,
compiler hash and application hash because both repositories contain existing
uncommitted implementation. Independent human trials remain deferred.

Development after the historical `9853763c` candidate added fullscreen worktree
management, stable scrollback resize anchors, native hooks, three-protocol image
encoders and bounded >1MiB transport. These are included in the installed
interaction/tool-timeline candidates. Project-local conversation history and
root-rename recovery are tracked by `add-cli-project-local-history`.
Grok Build design provenance and remaining rendering gaps are recorded in
`docs/grok-build-design-review.md`.

The interaction correction is tracked in
`docs/responses-shell-cursor-verification.md`: Responses tool continuation,
Bash preference, stable cursor, model question choices, grey retractable
insertions, local prompt/stash/code conveniences and blue atomic original-image
chips. Candidate-specific performance measurements and hashes remain in that
record rather than being generalized across different host workloads.

The tool timeline correction adds recoverable ordinary read errors, ordered
text/tool segments, one card per call, real running-tool animation and restored
tool history. It also uses Sengoo's independently tested bounded ready-input
drain. See `docs/tool-timeline-verification.md` for the combined native, actual
console, public workflow and installed-alias evidence. These remain internal
Windows candidates, with explicit engine limits and planned capabilities above.
Long-history recovery preserves the complete stored transcript, displays the
newest bounded window, and restores valid checkpoints beyond 1000 messages.
See `docs/long-history-recovery.md` for admission limits and older oversized
sessions that require a new model session while keeping their history.

Agent event projection now keeps each child in a stable summary card, with
its model, role, activity and tool count; transport JSON is not visible text.
The native model header includes its effective reasoning effort, defaulting to
medium when permitted. See [effective effort](model-effort-default.md),
[projection design](../tests/tui_agents_reference.md) and the candidate-specific
[verification record](agent-mode-controls-verification.md).

The latest scrolling and model-memory correction is recorded in
[its candidate evidence](scroll-session-verification.md). Session targets now
survive unsent selection, resume, branching and portable-history import;
the empty composer has no placeholder. Fractional wheel input and validated
message-region reuse reduce scrolling work while keeping the composer fixed.
