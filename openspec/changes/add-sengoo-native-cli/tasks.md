# Implementation gates

- [x] P0 record baselines and approved behavior/ownership.
- [ ] P0 freeze byte, process, event and shared-store contracts.
- [ ] P1 generic Sengoo JSON/transport/process/TTY facilities (sibling change).
- [ ] P2 compile and run native single-provider tool/edit/test/resume loop.
- [ ] P3 three protocols and shared connections/history/idle handoff.
- [ ] P4 subagents, consultation, Plan, Goal and local stdio MCP.
- [ ] P5 package Windows application with its native dependencies.
- [ ] P5 external project and tools-absent installation acceptance.
- [ ] Existing desktop and Sengoo compatibility checks.

CLI modules/tests/build owner: CLI agent. Shared store/desktop integration,
cross-repository builds, resource regressions and evidence: root integrator.
No phase is complete merely because its skeleton or mock tests exist.

The current scrolling-TUI and global-command follow-up is tracked separately in
`tasks-tui.md`; its requirements each have one implementation owner.

## Windows candidate evidence

The narrower checked items below do not close clean-machine, live-provider,
cross-platform or independent-trial gates. See
`sencode-cli/docs/candidate-verification.md` for evidence and delivery limits.

- [x] Native Sengoo CLI runs an external read/patch/command/resume tool loop.
- [x] Installed aliases `sen` and `sencode` start in the current directory and
  support `resume` with or without a session ID.
- [x] Three provider protocol fixtures, asynchronous children, consultation,
  Plan/Goal, local MCP and shared budget/permission fixtures run natively.
- [x] Verify all desktop acceptance paths claim a shared lease and stale
  pre-dispatch/error/state callbacks cannot release a later execution.
- [x] Verify read-only Git operations cannot execute repository hooks or filters.
- [x] Repackage and verify the identical final CLI bytes on PowerShell 7 and 5.1.
