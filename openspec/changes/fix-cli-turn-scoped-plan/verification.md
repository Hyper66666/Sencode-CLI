# Verification — 2026-11-07

Host: `DESKTOP-FUAQMFB`, Windows x64. Existing unrelated working-tree changes
were retained. This is an internal source-development candidate.

## Inputs

- CLI baseline: `b2b85ef2c8f369f2fd69ef8729ab420cc420959a`.
- Sengoo baseline: `86c6f87975646b91c9cf2d7d069ac06ee4243b9b`.
- Compiler SHA256: `cc280b3bf0ec0bf17650b0745500c72e205ee2d2073af8ea7ed552045570f1b0`.
- Executable SHA256: `29502855f4c08de6d6d1f9768eb4b1a6230e2b7a8200014c6cec0acf1f81a3be`.
- ZIP SHA256: `2aac32524957601adf7a2044daaf480be7a811b3c1a982bcb2d19e90cf1249ed`.

Complete input hashes and build logs are under
`target/plan-turn-20261107/candidate-2/`. All 536 recorded build inputs matched
after regression. The implementation uses Sengoo; no compiler/runtime change
was required for this repair.

## Executed checks

`native-final-evidence.json` passed six gate cases: plan_turn, core, commands,
tui_modes, session_permissions and engine. Later edits affected only Python
fixtures, not the implementations or native tests.

The production candidate passed the 14-check Plan fixture, including success,
Esc/Ctrl+C cancellation, provider failure, exhausted request budget, preflight
rejection, scrolling mode, automatic queued follow-up, host termination, legacy
metadata and resume after crash. Read-only execution is enforced during Plan;
subsequent ordinary turns can edit under the selected base permissions. Captured
children remain constrained until cleanup.

The initial production batch recorded an old worktree fixture failure: its
composer parser treated the empty `>` marker as a draft after placeholder removal.
The console-cell JSON contained valid Unicode; garbled diagnostic log decoding
was not the cause. The parser was corrected and the worktree case rerun. Original
failure evidence is retained. Prior passed cases in that batch were plan_turn_host,
engine_host, session_policy_wait and workbench_controls. Only the unrelated
worktree fixture changed between production batches.

`production-final-evidence.json` retains those four successful cases and the
original worktree failure. `production-completion-evidence.json` passed
worktree_tui_console (12 checks), model_routing_host (42 requests across three
protocols) and request_recovery_host (retry, cancellation, repeated compaction,
public history and cumulative budget recovery). All seven named production
cases therefore passed on the same executable, across the two retained batches.

Loopback providers, isolated SQLite state and owned hidden Windows consoles were
used. No paid/live provider calls or user histories were accessed. Clearing Plan
does not bypass unknown-outcome, old-execution or process-cleanup protections.

## Delivery

The versioned Windows package passed `candidate-2/install-smoke.json`, including
bare entrypoints, system-only PATH, Unicode paths, running-image upgrades,
checksums and rollback. `candidate-2/local-install-evidence.json` verified all
15 installed payloads and six direct/bare/WindowsApps entrypoints in
`D:/SencodeCLI`. PATH was unchanged. The prior executable
`05361fb9f77f263b13491665c09a72b60c24482a9a481057accb0e853c38cf85`
has a checksum-verified rollback package. Running user processes were preserved.

`verification-summary.json` records the combined gates, source consistency and
installed executable. OpenSpec strict validation and `git diff --check` passed.
No fresh-VM qualification or public release was performed.
