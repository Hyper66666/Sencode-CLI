# Agent presentation and mode controls

The screenshot defect came from treating each child transport envelope as a
tool transcript entry. The frontend now owns a bounded Agent projection. Each
child has one card with its model, role, latest activity, preview and tool count.
The actual child controller's `turn.tool_calls` and `tool_completed` events feed
the same card. Internal session and connection IDs remain keys, not UI text.
Malformed payloads cannot fall back to printed JSON. Missing, cancelled and
unknown outcomes cannot become successful completion.

This uses the behavior described in
[the reference notes](../tests/tui_agents_reference.md): stable Agent progress
identity, separated transport events and incremental updates. All new Agent,
model and permission presentation logic is Sengoo.

The top-right model label includes effective reasoning effort, defaulting to
`medium` for native models that permit it. An in-flight turn retains its model
and effort in the header; a later selection applies to the next turn. Displaying
an implicit default does not turn it into an explicit catalog constraint on a
manually typed model. See [effective effort](model-effort-default.md).

Shift+Tab cycles **手动审批 → 自动审批 → 完全权限**. The footer always names
the policy; during a turn it retains the active policy and shows a changed
selection with `→ 下轮`. Automatic approval covers file edits. Full permissions
also authorize commands and MCP. Plan and read-only children remain restricted.
Approval dialogs, questions and selectors own keyboard focus: Shift+Tab cannot
select Allow, approve a request or change policy through them. Account engines
show backend permission status; native APIs cannot pretend to use backend
consent. See [permission modes](permission-modes.md).

Sengoo's terminal runtime additionally recognizes standard `ESC[Z` as BackTab,
matching the native Windows Shift+Tab event. This is an additive input parser
repair with split-input, ordinary Tab, paste and EOF regressions, not a new ABI.
Its independent evidence is
`D:/Sengoo/target/terminal-backtab/evidence.json`.

## Baseline and evidence

Host: Windows x64, `DESKTOP-FUAQMFB`. The worktrees contain existing uncommitted
work; exact source and compiler hashes qualify each artifact in addition to
these full baseline revisions:

- Sencode: `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`.
- Sengoo: `d46b3f6cd8d6e770734f98edc57aa67cb931e26a`.

The installed baseline executable
`5b34aaf31a90a964b2b4bc3334f61277d4bd40deed92a711fe28a37d6c52d973`
reproduced raw child JSON, missing default-medium/footer display, and Shift+Tab
changing a permission dialog's selection from Deny to Allow. The owned test
then confirmed Enter wrote its disposable file. This evidence is
`target/workbench-controls-baseline.json`; no user workspace or credentials
were used.

The final candidate and exact acceptance results are recorded in
`target/agent-mode-controls-20261105/summary.json`. All provider calls in these
checks are synthetic loopback traffic. Actual remote model compatibility,
fresh Windows VM installation and a human trial are separate unqualified gates.
The local artifact uses the optimized source-development runtime and is an
internal candidate, not a production release qualification.

Final executable SHA256:
`11ac156927370d3dbe366d8fd7d4f7ca6e921c7813b56a9c53bab611ad12612f`.
The same executable was packaged and installed as both `sen` and `sencode` in
`D:/SencodeCLI/bin`; the existing WindowsApps forwarders were updated and
checked separately. No PATH change was needed.

| Verification | Result |
| --- | --- |
| Workbench controls, real owned Windows console | 16/16, including actual medium/xhigh requests, child reads, current/future targets and modal-safe permissions |
| Existing fullscreen interactions | 24/24, including Unicode, four streams, queues, approvals, image chips and terminal restoration |
| Read/patch/Bash, ordering and resume reliability | 7/7 |
| Project-local long history and root rename | 12/12 |
| Responses continuation and three host suites | Passed |
| Native UI and policy/effort suites | Nine suites passed; final Agent projection rerun after retaining the latest tool name |
| Isolated installation | Startup, resume, stale PATH, executable-only directory and locked-file rollback passed |
| Sengoo BackTab and existing terminal integration | New 1/1 plus existing 6/6 passed |

During four simultaneous loopback SSE streams, 40 injected keystrokes had
p95 input-to-composer latency of 25.70 ms on this host. The growing-paragraph
probe recorded 30 visible updates with p95 lag of 78 ms; these are measurements
for this candidate and workload, not universal terminal guarantees.

The earlier component source snapshots differ only in the later Agent module,
its regression test and the fullscreen fixture. The final Agent native probe
qualifies the updated module; the final public console probe qualifies its
host route. Fullscreen assertions were adapted to the new model label and to
check an actually preserved image draft instead of a footer prose suffix that
can be clipped after the persistent permission label.

The new CLI OpenSpec change passes strict validation. The CLI's full validation
reports 35 passed and three pre-existing strict warnings in
`add-fusion-selection`, `add-git-workspace-management` and
`add-grok-desktop-backend`. Sengoo's full validation reports 68/68 passed.
