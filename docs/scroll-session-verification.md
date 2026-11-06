# Scroll and session target candidate — Windows x64, 2026-11-06

Candidate: `target/scroll-session-target-20261106/candidate-2/`.
Sencode baseline `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`; Sengoo baseline
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`. Both checkouts contain existing
uncommitted work; the full input hashes in `build-inputs.json` identify this
candidate. Build checks confirmed inputs stayed unchanged.

- Application SHA-256: `125d3441e4dcc37a5486916e69a5c04aeaadc5d9c43f2c65bb25c1b3ffc08002`.
- Compiler SHA-256: `cf52f7a8ea6bdad280844a327beb9452980ee2f723324a3dd6155626f08f093b`.
- Package SHA-256: `61c148541fdb4ea752e2bb5d496183b85f1959e89334c90a68afe6510ace3544`.
- Package: `target/packages-scroll-session-final-20261106/sencode-cli-0.1.0-dev.0-windows-x64.zip`.

All application changes are Sengoo. The existing native terminal event API
already exposes signed fractional wheel deltas; no application-specific native
renderer or alternative agent implementation was added. Scroll timing uses
Sengoo's existing independently tested monotonic clock.

`scroll-target-complete.json`: **29 passed** on the final executable in an owned
hidden Windows console and isolated profile. Covers empty idle/busy composers,
fractional wheel movement, region output equal to a forced full repaint, full
oldest pages, unsent target changes, three public resume forms, in-app switching,
branching, CLI overrides, immutable running requests, post-cleanup preference
save, directory rename, guarded independent import and removed-provider failure.
Actual synthetic requests verify supplier/model/effort routing, not just headers.

Wheel injection-to-visible p95 over ten notch samples per width:

| Width | p95 |
|---|---|
| 80 | 40.36 ms |
| 120 | 26.46 ms |
| 160 | 31.25 ms |

`fullscreen.json`: **25 passed**, including slash two-Enter focus, cursor, drafts,
streaming Markdown, queues, provider catalog, attachments, approvals and cancel.
With four concurrent loopback SSE streams, 40 typing samples measured p50
22.79 ms, p95 **45.10 ms**, maximum 54.25 ms. These are separate input and scroll
workloads on this host; they do not measure external API latency.

`product-evidence.json`: all seven affected regression groups passed against the
same executable hash. Includes workbench controls (19), reading console (14),
public sessions (14), agent reliability (7), persistent execution host,
Responses explicit end-turn continuation and public portable-history recovery.
Tool recovery still completes a real read → patch → Bash test → next turn.
These use fixture credentials and loopback providers; no paid/live API was used.

The native renderer test also verifies zero output on an unchanged view,
sub-line accumulation, focus reset, resize fallback, unchanged draft/cursor,
80/120/160 columns with and without color, and one-row scroll output smaller
than one third of a complete frame. The full native frame/interaction executable
passed separately (`native-tui-result.log`). Final native gate evidence lives in
`native-evidence.json` beside this candidate.

`install-smoke-final.json`: both aliases pass with System32-only tool lookup, an
external Unicode/metacharacter workspace and an owned installed prefix. Checks
include no-argument startup, current-directory forwarding, bad arguments,
resume admission, pinned ripgrep, tampered payload rejection and locked upgrade
rollback. `rollback-evidence.json` separately verifies previous → candidate →
previous through both installed aliases without altering PATH.

The final installation smoke also keeps an owned stdio execution host alive
across upgrade. Two busy program backups were reported and preserved until that
host shut down normally; the fixture then removed only those owned files.
Only tracked backups with access/sharing/lock failures after a committed update
qualify for deferred cleanup. Failed publication, rollback and unrelated cleanup
errors still fail. This installer-only repair leaves the application hash and
all 287 production compilation inputs unchanged.

`local-install-evidence.json`: the final package is installed at `D:/SencodeCLI`.
All 15 payload hashes, both manifests, the install marker, and six direct/bare/
WindowsApps entrypoint checks passed. Existing user sessions stayed running;
their already-mapped old backup was preserved. PATH was unchanged. Reopen the
CLI to use the updated executable; `sen -c` continues the most recent session.

This remains a source-development internal build (`release_eligible=false`).
The host has development tools; the restricted-PATH/executable-only checks are
not a fresh Windows VM. Public release, independent trials, other platforms,
real provider qualification and new desktop handoff coverage are not claimed.
OpenSpec for this change passes strict validation. Whole Sencode validation is
38 valid / 3 pre-existing unrelated invalid changes: `add-fusion-selection`,
`add-git-workspace-management`, `add-grok-desktop-backend`.
