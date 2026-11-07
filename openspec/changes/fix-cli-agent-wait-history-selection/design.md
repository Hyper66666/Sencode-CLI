## Ownership and lifecycle

The controller pumps children while the waiting parent holds no model or write
permit. Child terminal counts gate blocking wait-only retries; list_agents and
explicit zero-timeout checks remain nonblocking. A parent with no
tool work waits for all children before one internal terminal-results message.
Partial child text remains a UI preview, not a completed model tool result.
Consecutive wait/list records retain durable IDs but share one expandable view.

Composer history is versioned session metadata. It contains at most ten 64 KiB
inputs, never approvals or coordinator messages. An idle UI flushes before
submitting a request; busy edits flush after cleanup or normal shutdown. Existing
sessions fall back to their own public user messages. Switching clears recall,
draft-navigation state and selection; a branch starts a separate empty history.
Only the history JSON member is updated, preserving other shared metadata.

Selection is a Sengoo cell-to-grapheme projection. Mouse-down captures a bounded
visible output snapshot; real drag sets focus; a click alone never copies.
Streaming continues behind the selected viewport. Clipboard operations are
explicit keyboard/right-click actions; Esc clears selection before cancellation.
Resize and overlays clear stale hit targets. Selection is bounded to visible
output and excludes the composer, status, menu and approvals.

## Reference review

Claude Code's LocalAgentTask notification uses a terminal notified flag;
TaskOutputTool waits in the host and supports bounded cancellation; teammate
views project stable task identities. Its arrow history preserves a draft and
selection separates click, drag and copy. These ownership patterns are
implemented in Sengoo using existing generic terminal/clipboard interfaces.
