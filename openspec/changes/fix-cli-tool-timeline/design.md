# Design

Assistant deltas form a mutable tail with stable identity. Before appending a
tool, notice, diff or other message, seal the visible tail into its existing
position. A later delta starts a new segment. Updating an existing tool never
seals or reorders another segment.

Tool cards use the execution/request and tool-call IDs, never the tool name or
path, as identity. Terminal states absorb delayed running events. Their text
and error previews are bounded and sanitized. Public messages and canonical
tool-call/result pairs restore cards without executing any tool. An unresolved
historical call is interrupted, not running or automatically retried.

Only visible running tool headers animate at 120 ms. Cached wrapped history
and the input are reused; elapsed time is derived from the shared animation
clock. Approval and selectors pause decorative motion. Reduced motion is
available through SENCODE_REDUCED_MOTION. Completion freezes the marker. No
animation or Thinking row is added underneath the composer. Cursor visibility
changes with focus only, never with animation ticks.

SQLite and existing fencing remain authoritative. This is an additive public
projection of existing data with no new stored secrets, credential reads or
model requests. Non-TTY output remains the execution host's existing contract.
