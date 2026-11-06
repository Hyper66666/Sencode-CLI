# Tool failures and continuation

Built-in file and hardened Git reads return ordinary path, not-found,
permission, I/O, parse, timeout, bound and UTF-8 failures as error results. The
controller persists the original call ID and error code, emits its final
failed tool event and continues the model loop. For directory reads, use `.`
for the workspace root and non-empty relative paths for descendants. Absolute
paths, parent escapes and symlink traversal remain rejected.

The model can correct its arguments using a new call ID. Reusing a completed
ID returns the exact cached result without executing or emitting a second
running/completed event. A failed Git read does not cancel unrelated safe
reads, and their results remain in declaration order after each owned process
tree becomes quiescent. The host never automatically retries a tool.

Editor path and preview failures before checkpoint admission have proof that
no write occurred; those errors can also continue. Once a checkpoint mutation,
general command, MCP or coordinator operation starts, an unclassified host
failure retains uncertainty and pauses execution. Its durable result carries
`outcome_unknown`; a repeated ID pauses again without replay. Cancellation,
interrupted execution ownership, invalid handles and exhausted resources also
remain host stops. Approval denial and hook trust/policy failures keep their
existing pause behavior.

The status-7 minimal reproduction and before/after logs are under
`target/controller-recovery-*`. The named native regression is
`src/tests_controller_recovery.sg`, driven by
`tests/controller_recovery_fixture.py`. It uses isolated databases and files,
tests with normal and empty PATH, and makes no provider requests or credential
access. Final executable/provider/TUI behavior has separate integration
evidence; library/controller probes do not certify that boundary by themselves.
