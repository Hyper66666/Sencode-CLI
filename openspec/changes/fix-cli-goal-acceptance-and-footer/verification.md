# Goal acceptance and composer footer evidence

Host: DESKTOP-FUAQMFB, Windows x64, 2026-11-07. Both repositories had local
changes; the recorded input manifests, rather than HEAD alone, identify the
tested implementation. No commits or remote updates were made for this change.

Baselines:

- Sencode CLI: `b2b85ef2c8f369f2fd69ef8729ab420cc420959a`.
- Sengoo: `86c6f87975646b91c9cf2d7d069ac06ee4243b9b`.
- Compiler SHA256: `cc280b3bf0ec0bf17650b0745500c72e205ee2d2073af8ea7ed552045570f1b0`.
- Final candidate SHA256: `834c2719dcfd9014beab9840dbf3f6ed39b3ee975dbe31cf9bc5c0091b66e844`.

Candidate inputs and build result are in
`target/goal-footer-20261107/candidate-2/build-inputs.json` and
`build-result.json`. Compilation used the source-development runtime and O2;
the build verified that its compiler and recorded source inputs did not change.
This is an internal development candidate, not published-release evidence.

## Native verification

`target/goal-footer-20261107/native-evidence.json` records passing `goal_footer`,
`core`, `engine`, `execution_diagnostics`, `tui_modes`, `reading_experience` and
`plan_turn`. This run preceded the final footer span correction.

`target/goal-footer-20261107/native-final-evidence.json` records passing
`goal_footer` and `tui_modes` on the final source. The added regression renders
active manual permissions, a future `自动审批 · 文件编辑` label and an approval
hint together at 80/120/160 columns. It verifies light-blue/yellow color spans,
identical NO_COLOR text, successful colored painting and no writes on unchanged
frames. Permission labels are normalized before byte offsets are measured.

## Initial candidate regression

The initial candidate passed its Goal checks but failed `workbench_controls`
when opening an approval after selecting a future automatic permission label.
Normalizing the Unicode separator changed the byte offsets of a hint color
span and caused error 20. The final implementation normalizes labels before
recording spans and uses the footer's dim base style for hints. The initial
candidate was not installed. Its failed evidence is retained in
`target/goal-footer-20261107/production-evidence.json`.

## Final candidate and installation

`target/goal-footer-20261107/production-final-evidence.json` passed all six
production-executable suites against the final candidate with unchanged inputs:

- `goal_acceptance_host`: 11 scenarios, including model-proposed checks,
  actual failing-check repair, pinned checks through restart, exact-command
  approvals, cancellation cleanup and ordinary-mode refusal.
- `workbench_controls`: 19 scenarios including permission colors, future/active
  permission separation, approval focus and the previously failing transition.
- `session_policy_wait`: 27 scenarios including permission persistence,
  project-folder rename, pending work, cancellation and transcript grouping.
- `plan_turn_host`: 14 scenarios covering completion, interruption, failure,
  budget/preflight refusal, crash recovery and queued follow-ups.
- `engine_host`: streaming, approval, cancel, provider snapshots, restart,
  compaction, consultation and refusal to replay uncertain tool outcomes.
- `request_recovery_host`: bounded retries, refusal to replay sent/streamed
  requests, cancellation, per-attempt budgets, automatic compaction and restart.

Owned-console snapshots at 80/120/160 columns are in
`target/acceptance/20261107-192143-321-d5403a34/goal-acceptance.json`.
The normal footer contains only `完全权限 | Shift+Tab` and a right-aligned
`/help`; its second line is blank. Approval/focus controls replace the idle hint.

Package:
`target/packages-goal-footer-20261107-final/sencode-cli-0.1.0-dev.0-windows-x64.zip`.
Archive SHA256:
`ff5f92f5ede21a88e616a6e0b8beff337e8b29085c4f5522db5a9f2ac95157df`.
The package retains pinned ripgrep, managed runtime binaries, licenses and the
required runtime DLL. Packaging did not fetch sources or tools.

`candidate-2/install-smoke.json` passed isolated installation, sanitized PATH,
Unicode/metacharacter paths, both bare command aliases, startup/resume probes,
tampered ripgrep rejection, running-image upgrade and rollback on locked alias.
`candidate-2/local-install-evidence.json` records successful installation at
`D:/SencodeCLI`, 15 verified payload files and six verified command entrypoints.
Both installed binaries match the final candidate. PATH was unchanged and the
two pre-existing user processes remained alive. Locked old program backups are
retained for those sessions until they exit; new launches use the new binary.

The previous Plan-turn package is retained for rollback:
`target/packages-plan-turn-20261107-final/sencode-cli-0.1.0-dev.0-windows-x64`.
All its payload checksums were verified before the update; its executable hash
is `29502855f4c08de6d6d1f9768eb4b1a6230e2b7a8200014c6cec0acf1f81a3be`.

## Reference design and boundaries

The compact focus-sensitive hierarchy was studied in the local Claude Code
`PromptInputFooter.tsx` and Grok Build `agent_view/key_owner.rs` references.
Implementation remains Sengoo in `src/tui.sg`. No native boundary or compiler
change was required for this fix.

Loopback-provider tests exercise real execution hosts, owned Windows consoles,
temporary projects and synthetic credentials. They are separate from calls to
a live model service. Sanitized-PATH installation checks on this development
host do not constitute fresh Windows VM qualification.
