# Tool timeline reliability

The frontend seals an assistant segment before the next tool, notice or diff.
A tool's start and terminal state share one request-scoped call ID and one card.
Updating that card does not split a later streamed paragraph. Paths remain on
the completed card, terminal states absorb delayed starts, and the reading
anchor survives card growth and resize.

Main and child conversations use a small activity marker at their visible tail.
An explicit provider reasoning signal selects Thinking; other execution uses
Working and an approval shows a static waiting state. Tool headings stay static.
The composer has no Thinking indicator; activity ticks do not rewrite its borders
or toggle cursor visibility. Set `SENCODE_REDUCED_MOTION=1` for static markers.
Completion freezes the card. The native terminal's actual blink timing is not
inferred from ANSI sequence assertions.

Resume reconstructs cards from canonical assistant tool calls and results in
the existing SQLite public history. Incomplete, malformed and uncertain results
are shown as interrupted. Restoration cannot execute tools or resume a Goal.
No database migration or JSONL event-schema change is required. Existing project
`.sencode` portability and execution fencing remain in place.

Long transcripts use a separate bounded newest-history projection with the
stored total visible in the status bar. Model recovery reads the compaction
checkpoint and its complete canonical tail. The limits and older-session
behavior are documented in [long-history-recovery.md](long-history-recovery.md).
The independent public fixture also checks resume after renaming the project.

The tool error policy is documented in [tool-error-recovery.md](tool-error-recovery.md).
Ordinary read errors are model-visible results; unknown side effects remain
host stops. Ctrl+C keeps pending work paused until explicit `/queue resume`.

## Verification boundaries

`tests/agent_reliability_fixture.py` uses an isolated project outside the source
tree, a loopback model service, random fixture credentials and a real owned
Windows console. Its baseline at `target/agent-reliability/baseline-v5-final.json`
reproduced five failures: headless read recovery, reversed live ordering,
duplicate cards, missing resumed cards and terminal read recovery. Real file
editing, Bash verification and terminal restoration already passed on that
baseline. Reference code locations are recorded in
`tests/agent_reliability_reference.md`.

`src/tests_tui_timeline.sg` exercises live and restored ordering, independent
same-name calls, terminal-state absorption, visible-only activity, reduced
motion, focus, partial cancellation, elapsed time and reading anchors.
`src/tests_tui.sg` includes blue atomic image references, one-press deletion,
Unicode editing, queueing and incremental paint regressions. The editor test
explicitly preserves Ctrl+C's queue pause before an explicit resume.

The accompanying Sengoo fix is a generic Windows input boundary repair:
`read_event(0)` drains a bounded batch of irrelevant KEYUP/focus/mouse records
instead of reporting no input while a real key is already queued. Both native
and public Sengoo probes cover cancellation, deadlines, bounded batches and
split UTF-16 emoji. Its independent evidence is
`D:/Sengoo/target/terminal-polling/evidence.json`.

Final candidate hashes, native checks, real-console acceptance, installation
and measured latency are recorded in the candidate evidence directory. This
remains a `source-development` Windows x64 internal candidate. Loopback fixtures
do not qualify a paid provider, real user clipboard, macOS/Linux or a fresh VM.

## Earlier Windows candidate, 2026-11-05

The earlier optimized executable was
`5b34aaf31a90a964b2b4bc3334f61277d4bd40deed92a711fe28a37d6c52d973`.
It is installed as both `D:/SencodeCLI/bin/sen.exe` and `sencode.exe`; the
WindowsApps forwarders resolve to the same tested version. Bare aliases were
checked with `--help` and `--version` without opening user configuration.

The later session/reading candidate supersedes that installed version. Its
evidence and current local alias hash are recorded in
[the session/reading verification report](session-reading-verification.md).

All candidate evidence is in
`target/tool-reliability-r2-20261105-opt/`:

- `build-inputs.json` and `build-result.json`: full baseline SHAs, source,
  compiler and runtime hashes, optimization level 2, unchanged build inputs.
- `agent-reliability.json`: 7 checks, including real read/patch/Bash test,
  continued conversation, corrected reads, stable cards and resume.
- `tool-animation.json`: 13 real-console samples over 672 ms; all three star
  shapes appear without changing the draft, cursor or persisted tool identity.
- `long-history-public.json`: 12 checks; 1008 saved messages restore their
  newest Chinese tail before and after renaming the project directory.
- `fullscreen.json`: 24 checks, including images, choices, retractable pending
  messages, live editing and four simultaneous SSE streams. Input-visible p95
  is 25.0308 ms (40 samples); stream-render lag p95 is 63 ms, a separate metric.
- `native.json`: views, timeline, editor, Markdown, input and pending regressions.
- `long-history-runner.json`: standard-runner state, checkpoint/context and
  public resume regressions, including loopback compaction and exact budgets.
- `integration.json`: Responses continuation, external CLI, management,
  project-local history, engine host and request-recovery host all pass.
- `install-smoke.json` and `installed-verification.json`: isolated install,
  bare aliases, startup/resume, stale PATH, locked-file rollback, executable-only
  and development-tool-free PATH checks, followed by local installed hashes.

Sencode baseline: `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`.
Sengoo baseline: `d46b3f6cd8d6e770734f98edc57aa67cb931e26a`.
Both worktrees contain existing uncommitted implementation; these are baseline
revisions, not a release SHA. Long-history native evidence is separately recorded
in `target/long-history-evidence.json`. The three affected CLI changes pass
strict validation. All Windows changes still have three unrelated pre-existing
failures, recorded in the candidate's `openspec-all.log`.
