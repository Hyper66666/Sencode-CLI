# Interrupting and continuing

Esc or Ctrl+C stops the current turn and waits for tool-process cleanup. Start
the next turn normally, or reopen the same session with `sen -c` or `sen resume`.
Completed file edits and commands remain in the project history.

On a stopped turn and before the next model request, the host checks tool-call
pairing. It restores an absent public result from the exact completed ledger
record. A call that was never admitted receives an explicit not-executed error
result and its ID is reserved against replay. Recovery does not execute tools.
An uncertain process or tool outcome still pauses for inspection.

Read-only history listing does not repair or mutate the conversation. Recovery
requires the session's execution lock and current fence. Old executors cannot
submit a delayed result into the resumed execution. Results already in history
are retained once, including when only part of a batch finished before cancel.

State reads and updates select one member within SQLite instead of copying the
combined state through one JSON arena. Other modes, checkpoints, permission
and model choices are preserved. The attempt journal keeps its 256-entry bound;
old unfinished network attempts from a quiescent predecessor are interrupted,
never presumed successful or automatically retried.
Updating an existing attempt retains the other entries. Rotation never discards
a request still running under the current execution.

A request-state storage failure is reported separately from a provider failure.
The host does not clear history, silently change providers or rerun an old shell
command to get around that failure. Genuine storage limits remain explicit.
