## Goal acceptance

finish_goal keeps summary and adds optional checks (1–32 nonblank command
strings, at most 8192 bytes each and 65536 total). Configured checks win. When
none exist, the model proposes meaningful executable acceptance assertions.
The host persists their source before running them, shows exact commands when
approval is required, and only completes after all exit successfully. Missing
proposals are recoverable tool results so the model can correct the call.

Failed checks return evidence for correction. Two unchanged failures pause;
unavailable verification, denied permission or cancellation pause immediately.
Pause reasons survive persistence and receive distinct host diagnostics. Plan,
shared budgets, workspace locks and cleanup requirements remain authoritative.
No configured command is silently replaced. Saved model checks remain pinned on
resume. Ordinary follow-ups do not implicitly resume a Goal.

Model-proposed commands default to Bash and may select PowerShell/cmd via shell.
Existing configured checks retain PowerShell semantics. Check source and shell
are saved in additive metadata and recovered with pinned checks before a resumed
request; this avoids reinterpreting Bash checks as PowerShell on restart.

## Compact footer

Use the reference tools' context-sensitive hint hierarchy, implemented in Sengoo.
Keep colored current/next permission labels, compact queue count only when tasks
exist, and a small right-aligned hint for the current focus. Commands remain in
/help and key bindings in /keys show. Suppress routine readiness/progress duplicates. Preserve a
separate line for actionable notices and keep the existing frame/cursor budget.
Only explicit cancellation is labeled cancelled; verification pauses are paused.
Normalize permission labels before measuring their UTF-8 color spans. Hints use
the footer's dim base style so Unicode normalization cannot invalidate an
additional hint span. Identical frames do not send cursor or paint updates.

## Verification

Native policy/schema/diagnostic/footer tests, synthetic real-host Goal acceptance
and approval checks, owned Windows console snapshots at 80/120/160 columns,
existing Plan/engine/permission recovery regressions, package/install verification.
Fixture evidence is separate from live-provider and clean-VM qualification.
