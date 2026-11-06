# Explicit user Git worktrees

## Capabilities
Add an independently owned Sengoo worktree job for bounded, cancellable Git
inspection, explicit user creation and confirmed removal. The root application
integrator owns the terminal entry points. This child owns the module, isolated
Git fixtures and the execution/lock contract; it does not duplicate desktop
task-workspace requirements.
An independent management wrapper exposes `sen worktree list|create|remove`;
the root integrator owns argument parser additions and main dispatch.

## Non-Goals
No model tool, automatic workspace switch, branch reset, stash, clean, force
removal, remote fetch or recursive filesystem deletion is introduced. Existing
desktop task workspaces and edits in every checkout remain authoritative.

## Boundaries and dependencies
The module uses Sengoo's existing piped process, path, OS lock and SQLite APIs.
Git alone mutates its worktree metadata and checkout. Shared storage remains at
contract v1, without a schema migration. TUI integration is a separate root-owned
gate after the isolated module tests pass. Windows x64 is the initial tested
host; other platforms require their own validation.
