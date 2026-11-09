# Verification, Windows x64, 2026-11-08

Host: DESKTOP-FUAQMFB. Baselines:

- Sencode CLI `390ddc2c6999e7eba801b9d636d4c4038226236b`.
- Sengoo `0039f59e04e68acc386c9f49497b32178bc879b9`.
- Compiler SHA256 `6507e0e2eff15fd375054334f4e4ff6bccf540431f5f81bd56625f7f0d616252`.
- Final candidate SHA256 `8b5f26657e6e254095ce6e70f5d82b66521cbf15f8d40a6b06d420d823da92bc`.

Source-development runtime, clang 19.1.7, CLI `-O 2`. Input inventories and hashes
are frozen under `target/viewport-20261108/candidate-3/`. These are uncommitted
changes on the recorded baselines, not a published release.

## Root causes and isolated checks

Read-only examination of the reported execution found a successful compaction
checkpoint and exactly 15 main + 35 child requests. The old implicit shared
50-request cap stopped the next request; this was not failed compaction.
No user messages, credentials or raw provider responses were exported.

Default request count is now unlimited for all entrypoints. Optional explicit
budgets still share accounting between parent, children, consultation, summaries
and retries. Old unmarked default-50 Goal recovery retains cumulative usage
and removes the implicit cap. Old explicitly chosen 50 cannot be distinguished
from the former default without provenance and receives this same migration.
New explicit limits retain provenance through portable project history.

`target/viewport-20261108/native-evidence.json`: five suites / ten build-and-run
steps passed: scheduler, execution diagnostics, compaction, TUI scrolling and
engine schema. Coverage includes 160 parent/child requests without a count cap,
explicit-budget counters, same-size invalidation, Unicode drafts and no-color
painting. `project-history-marker-evidence.json` separately passes portable
history/import compatibility, including the explicit-limit marker.
`tui-native-evidence.json` separately passes the existing complete native TUI
suite: append-only streaming, combining/ZWJ graphemes, resize anchors, idle
cursor, two-step Enter, pending queue, choices and atomic image chips.

`resize-live-evidence.json` records an independent native reproduction: clearing
the screen while a plain streamed row grows lost its retained prefix before
the fix (exit 1), and reconstructs the complete row after the fix (exit 0).
Invalidated frames now suppress the append-only optimization.

Eight independent Sengoo native checks are recorded in `foundation-evidence.json`.
They cover retained-handle allocation, stale generations, live-count cleanup,
JSON/owned Result compatibility and actual owned Windows process/terminal I/O.
The 12000-row paint computation changed from 485 ms to 16 ms in the recorded
old/new allocator comparison. This is distinct from terminal-delivery latency.

## Final executable: real console and synthetic providers

Recorded console: `target/acceptance/20261108-042157-785-59d928ec/scroll-target.json`.
12000 history lines, 40 wheel samples per width, nearest-rank P95 including
injection and snapshot observation:

| Width | P95 |
| --- | --- |
| 80 | 38.0501 ms |
| 120 | 35.9351 ms |
| 160 | 35.7187 ms |

The same-size poison/reconstruction comparison, repeated shrink/grow sequences,
anchored scroll, centered gray jump control and model/session memory passed.
The jump click produces no new provider request. Recorded cells were rendered
and visually inspected in `target/viewport-20261108/scrolled-120.png` and
`settled-resize.png`; these are fixture snapshots, not captures of a user session.

`unlimited-context.json` on the same executable passes 60 completed read tools,
seven automatic summaries and a final answer: 68 requests without a configured
cap. A separate old-Goal restart continues beyond its saved 75 requests while
keeping token usage, then stops on explicit cancellation.

`production-evidence.json`: all ten same-executable suites passed: unlimited
context, scroll/session target, request recovery, cancel/resume across three
protocols, Responses tools, Goal acceptance, agent reliability, fullscreen,
background jobs and public project-history recovery. The fullscreen suite
passed 25 checks, including four streaming requests with active input.
Four-stream input latency: 40 samples, reported P95 23.4393 ms, maximum
24.1808 ms. These are local console/loopback measurements.
Package isolation smoke passed both aliases, Unicode paths, forwarders and
locked-image rollback. `candidate-3/final-gates.json` and
`candidate-3/local-install-evidence.json` both passed. Fifteen installed payload
files and six alias/forwarder entrypoints match the final candidate. PATH was
unchanged, existing user processes were not stopped, and the prior package
was checksum-verified for rollback. Restart old running sessions to load this
candidate; `sen -c` continues project history.

Package: `target/packages-viewport-20261108-v2/sencode-cli-0.1.0-dev.0-windows-x64.zip`.
Archive SHA256 `ec55a9c55a6f37141f5e57f820f5e55ae4362b706012bc2b0192893d155f9596`.
No live-provider or fresh-VM success is implied by these fixtures.

## Audit and limits

`docs/limits-audit.md` compares the supplied CC/Grok snapshots and distinguishes
implemented changes from history pagination, full-output files, ranged reads,
child archival/compaction and configurable concurrency follow-ups. Fencing,
deduplication, unknown-side-effect handling, permissions and five failed-request
retries remain. Extreme layouts above 500 columns / 300 rows are not qualified.

An extra existing `views` suite failed its stale `● cli-1` assertion: unchanged
`view_sessions` emits the title, matching the user's title-based listing request.
Both `src/views.sg` and `src/tests_views.sg` are unchanged from this baseline.
This result is retained in `native-with-stale-views.json`; this change does not
claim that every repository test passes. An interrupted optional history-probe
compile and the earlier incorrect test-dispatch run are retained separately;
neither is counted as a passing gate.

The qualifications here cover local loopback protocols and an owned hidden
Win32 console. Attached Windows Terminal repaint behavior, live services,
fresh-machine installation, non-Windows execution and the complete Sengoo
ownership/sanitizer matrix remain separate qualifications.
