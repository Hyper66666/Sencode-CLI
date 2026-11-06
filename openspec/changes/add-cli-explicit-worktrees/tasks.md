# Tasks

- [x] Implement independent asynchronous inspect and approval contracts with bounded piped Git jobs (`sgc check`, matching development toolchain).
- [x] Implement detached/exact-branch creation, path and configuration guards without changing current edits.
- [x] Implement clean nonprimary/noncurrent removal, shared workspace/session leases and transactional execution refusal.
- [x] Verify missing Git/nonrepository, Unicode/spaces, malformed framing, cancellation, deadlines and exact branch behavior (`tests/worktree_fixture.py`: 37 combined isolated Windows x64 cases passed).
- [x] Add focused synthetic slow/flood process cases to verify both-stream 1MiB capture bounds, 64KiB report truncation and actual descendant cancellation (included in the same 37-case fixture).
- [x] Verify malicious hooks/filters, disabled network protocols, dirty/untracked/ignored refusal, real junction/current/primary refusal, nested workspace locks and lock/execution races without real user data (included in the same 37-case fixture).
- [x] Validate this child change, document Windows evidence and public integration API (`openspec validate add-cli-explicit-worktrees --strict`).
- [ ] Integrate explicit terminal worktree entry points (owner: root; application gate).
  Public `sen worktree` routing and installed WindowsApps alias pass all 14
  wrapper checks on `9853763c...`, recorded in
  `target/acceptance-workbench-installed-frozen.json`. Nonblocking fullscreen
  selector/mutation integration is in progress and keeps this gate open.
- [x] Verify independent `worktree_cli` command wrapper with TTY approval/nonTTY refusal and exact --yes semantics (`tests/worktree_cli_fixture.py`: 11 headless and 3 real hidden-console cases passed); parser/main remain root-owned, with final public-main candidate verification tracked by the integration owner.
- [x] Implement the delegated fullscreen owner (`frontend_worktree.sg`) and real-console native state checks for idle/Plan, fresh/default-deny/consumed approval, changed policy, create/remove, queue pause, cancellation and sticky unknown cleanup (`target/worktree-tui/native-console-evidence.json`, Windows x64, development compiler `CF52F7A8EA6BDAD280844A327BEB9452980EE2F723324A3DD6155626F08F093B`).
- [x] Run `tests/worktree_tui_console_fixture.py` against production main for fresh approval, changed HEAD/target, Plan, reserved removal cancellation, descendant cleanup, queue deferral and terminal-mode restoration (`target/worktree-tui/console-evidence.json`: 13 checks passed, Windows x64, binary `8C0C384135B37D6DB0E25179AD5839905EC72F77D012E25CB7BF3213B36B7A39`); keep final combined/installed-candidate verification with the integration owner.
