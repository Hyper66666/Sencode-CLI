# Live steering and compaction feedback

## Why
Queued input cannot currently join a running task. Internal summary requests
overwrite Compacting with ordinary activity, and failure notices are muted.

## Capabilities
- An explicit second Enter transfers the oldest queued message into a native
  task at a complete response/tool boundary, without aborting an HTTP request.
- Compaction retains its activity phase and reports 上下文已压缩 as information.
- NOTICE headings and bodies use the existing error foreground.

## Non-Goals
No remote in-flight prompt mutation, managed-runtime steering emulation,
permission expansion, tool replay, new background mode or database migration.
The integration owner owns the input/control, controller and TUI changes.
