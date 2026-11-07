# Agent waits, session recall and output selection

The parent waits in the Sengoo execution host when it has no independent work.
Partial child text updates a stable Agent card; it is not a completed tool result.
Blocking wait-only batches resume on a new terminal child result instead of
requesting another model response every second. Cancellation and the shared
request budget remain active. Explicit list/zero-timeout checks stay nonblocking.
The system prompt asks for one delegation announcement and one useful summary.
This prevents the unchanged-status loop; it cannot guarantee that a provider
never writes redundant prose for other reasons.

Consecutive wait/list tool records share one expandable Agent-status group,
retaining original tool IDs and ledger records. Failures remain visible. Existing
child cards keep one identity across their requests; child previews and tool
details do not become separate assistant headings.

Input recall is a versioned member of the session's existing shared_modes JSON.
It holds ten submitted composer values, excludes approvals, preserves unrelated
Goal/policy metadata, and respects active execution fencing. Idle submissions
flush before dispatch. Queued inputs flush after cleanup or normal shutdown;
an abrupt process kill can lose queued inputs that were never submitted to the
execution host. Sessions without recall metadata migrate their own public user
messages only. Branches reset recall even when their transcript is copied.

Output selection converts screen cells into whole Unicode graphemes, with a
bounded visible snapshot while the host streams. Copy is an explicit action;
Esc, typing, wheel scrolling, resize and interaction overlays clear stale targets.
Selection does not change the composer or authorize tools. See
[editor keys](editor-keybindings.md) for usage and bounds.

## Reference review

Reviewed the supplied Claude Code snapshot's LocalAgentTask notification code,
TaskOutputTool completion waits, TeammateSpinnerTree, useArrowKeyHistory, and Ink
selection/use-selection. The useful ownership patterns are atomic terminal
notifications, stable task projections, draft-preserving recall, separate
anchor/focus state and explicit copy/focus handling. The implementation remains
Sengoo and uses Sengoo's existing generic terminal and clipboard boundary.

During this implementation an unpositioned unit/bool diagnostic made CLI errors
hard to locate. Sengoo now reports `if-without-else-value` with the branch span,
enclosing function and repair hint. Branch semantics and runtime ABI are unchanged.

## Verification

`recall_selection` exercises recall bounds, multiline drafts, coordination groups,
Unicode/reverse/multiline selection, no-color highlight and focus safety.
`input_history` exercises persisted session isolation, fencing and Goal metadata.
`agent_recall_selection` exercises the real native host/Windows console against a
slow loopback provider, selection, restart/switch/branch/rename. Its optional
`--clipboard` scope additionally exercises actual clipboard copy inside a private
window station. Isolation failure fails that scope; the default scope never
changes the user's clipboard and does not count as a Windows clipboard pass.
These are fixture checks, separate from live-provider and installation evidence.
