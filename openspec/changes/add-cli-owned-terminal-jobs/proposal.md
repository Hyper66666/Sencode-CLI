# Explicit user terminal jobs

## Capabilities
Add a standalone Sengoo `pty_session` module for explicitly approved user
terminal jobs, backed by the sibling Sengoo `add-windows-owned-pty` capability.
It owns process-tree cleanup, the same shared workspace OS write lock used by
agent tools, and bounded VT display bytes. The platform implementation agent
owns this module and isolated probes; the root integrator owns TUI entry points.

## Non-Goals
No model tool, managed-runtime escape hatch, automatic approval, full terminal
emulator, background execution, desktop schema migration or cross-platform
qualification is introduced. The module has no provider credential access.

## Boundaries
Native code handles only generic ConPTY ownership. Sengoo owns validation,
approval snapshot, path guard, environment policy, lock lifecycle and display
buffering. Existing noninteractive run_command permissions remain unchanged.
