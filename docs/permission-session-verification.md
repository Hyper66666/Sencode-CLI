# Permission memory and agent waits — Windows x64, 2026-11-06

Candidate: `target/policy-wait-20261106/candidate-6/`, host `DESKTOP-FUAQMFB`.
Sencode baseline `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`; Sengoo baseline
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`. Both checkouts contain existing
uncommitted work. `build-inputs.json` records all 290 compilation inputs and
compiler identities; the build verified that they stayed unchanged.

- Application SHA-256: `23e8635ba2b25b9f16f63db723c51056b09f178b4ba274d50c33b4c631c98d4c`.
- Compiler SHA-256: `cf52f7a8ea6bdad280844a327beb9452980ee2f723324a3dd6155626f08f093b`.
- Package SHA-256: `c980bc61eb251cd382f2a339324ccfcaea201d2c74535efb901e81bfa29627fc`.
- Package: `target/packages-policy-wait-final-20261106/sencode-cli-0.1.0-dev.0-windows-x64.zip`.

All application changes in this fix are Sengoo. Existing SQLite, process,
terminal and monotonic-clock interfaces suffice; no application logic was
moved into native code or Python. Python is used only for isolated test drivers.

`target/policy-wait-20261106/reproduction.json` reproduces the screenshot with
the previous installed executable: a bounded child wait returns while its
parent remains in scheduler waiting state, and model-slot contention is treated
as fatal code 12 with a budget diagnostic. Cleanup then cancels healthy children.
The final controller resumes bounded waits and pumps children/control input
while capacity is unavailable. It charges requests only after acquiring a slot.
Real shared-budget exhaustion remains code 13; cancellation remains code 19.

`product-evidence.json` records **11 passing product groups** against the final
application hash. Detailed reports are under
`target/acceptance/20261106-053022-435-02c50610/`:

| Group | Verified behavior |
|---|---|
| Session policy / waits (27 checks) | One and two slow children finish; cancellation; real budget limits; actual edits under restored permissions; unsent changes; six immediate-startup permission cycles; command-line overrides; in-app switching; Plan isolation; directory rename; one heading per user at 80/120/160 columns |
| Execution host | Session contention returns a result without killing the host; the same unaccepted request ID succeeds after idle handoff; approvals, cancellation, replay refusal, Plan/Goal and persistent submissions |
| Managed host | Explicit backend consent, strict-mode refusal, both managed adapters, streaming, approvals, cancellation and process cleanup using verified synthetic runtimes |
| Workbench controls (19 checks) | Permission colors, Shift+Tab focus, immutable active permissions, next-turn changes, model/effort routing and child cards |
| Reading console (14 checks) | Collapsed reads, expansion, multi-hunk diff, colors, activity placement and 80/120/160-column reflow |
| Agent reliability (7 checks) | Failed-read correction, stable tool identity, history without replay and actual read → patch → Bash test → next turn |
| Scroll / model memory (29 checks) | Empty composer, fractional wheels, region repaint equivalence, model memory, in-app branch, overrides, directory rename and guarded history import |
| Fullscreen (25 checks) | Commands, two-Enter completion, drafts, streaming, queues, approvals, attachments, cursor and terminal restoration |
| Responses continuation | Explicit end-turn handling and continued task context |
| Public sessions (14 checks) | Titles, root/child filtering, stale picker revalidation, branch and project-local history |
| Portable history | Renamed project, stable identities, preserved paused Goal budget and explicit missing-catalog recovery |

Native `scheduler`, `session_permissions`, `tui_turns`, `tui_timeline` and `engine`
suites passed in `../candidate-5/native-evidence.json`. The last change only adds
the engine's structured admission-failure guard. Its native schema suite was
rebuilt and passed again in `engine-native-evidence.json`; `native-reuse.json`
verifies that the other four suites' compiler worksets exclude that changed
module and all their compilation inputs remain unchanged. Tests also cover
no-op preference writes, active ownership rejection, preserved budgets, local
branches, rejected permission import, hidden coordinator context with retained
elapsed metadata, and zero terminal output for offscreen activity.

In the final owned Windows console, four concurrent loopback SSE requests and
40 typing samples measured p50 **26.21 ms**, p95 **38.32 ms**, maximum **42.53 ms**.
Wheel injection-to-visible p95 over ten samples per width was **31.60 ms** at
80 columns, **31.56 ms** at 120 and **30.32 ms** at 160. These are local console
measurements, separate from network latency or other terminal hosts.

The change passes strict OpenSpec validation. Whole Sencode validation is
39 passed / 3 pre-existing failures: `add-fusion-selection`,
`add-git-workspace-management`, and `add-grok-desktop-backend`.

This is an internal source-development candidate (`release_eligible=false`).
All service tests use isolated profiles, fixture credentials and loopback
providers. Live-provider qualification, new desktop handoff coverage, other
platforms and a fresh Windows VM are outside this fix's recorded evidence.

`install-smoke-final.json` passes for both aliases with System32-only tool
lookup, an external Unicode/metacharacter workspace and executable-only
installation. It also verifies tampered payload rejection, pinned ripgrep,
locked-upgrade rollback, and an owned running host surviving an upgrade. During
that test, two tracked busy backups were retained until the host exited normally.

`rollback-evidence.json` verifies the previous scroll/model-memory package →
this candidate → the previous package through both installed command aliases,
without changing PATH.

`local-install-evidence.json` records installation at `D:/SencodeCLI`, all 15
payload hashes, both manifests, the marker and six direct/bare/WindowsApps
entrypoint checks. Both installed application hashes match the final candidate.
All 290 compilation inputs and PATH remain unchanged. Installation stopped no
processes; the existing mapped backup and newly deferred image/runtime backups
were retained. Reopen the CLI to load the new image; `sen -c` continues the most
recent project conversation.
