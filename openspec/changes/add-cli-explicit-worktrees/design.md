# Design

Inspection captures the Git executable, current directory, checkout root,
canonical common Git directory, HEAD and NUL-framed porcelain worktree records.
Git commands use literal argv and spawn_piped. A job advances only when polled;
it drains both streams with bounded storage and enforces command/overall time
limits. Missing Git and nonrepositories have explicit capability results.

Creation and removal require a fresh approval fingerprint of that immutable
inspection plus the exact operation, target and optional user branch. Mutations
reject Plan, child or noninteractive policy. Creation defaults to detached HEAD;
a supplied branch is validated exactly and created with -b, without guessing or
resetting an existing branch. Identity and HEAD are refreshed after acquiring
the common-directory and source-workspace OS locks.

Repository configuration is untrusted. The subprocess environment is cleared
and only system discovery variables are copied. Git prompting/lazy fetch are
disabled. Hooks, fsmonitor, submodule recursion, pager and external diff are
overridden. Before checkout/status the job enumerates every configured
filter.*.clean/smudge/process/required key with NUL framing and applies literal
argv overrides. Ambiguous keys are rejected. No hook, clean, smudge or process
filter may run merely because a user requested a worktree operation.

Removal must resolve an existing registered checkout, reject the primary
checkout and the current checkout or its containing directory, refuse locked,
prunable, dirty or untracked worktrees, and reject reparse path components.
It takes the target workspace lock and holds leases for all associated shared
sessions. A transaction takes a write reservation with a zero-row update before
reading shared state and prevents new session/execution writers
between verification and removal. Active, cleanup-required, Meeting and Fusion
executions are refused, never cleared. Final removal is only Git's
worktree remove -- <exact path>, without --force.

Jobs have running, complete, refused, failed, cancelled and timed-out terminal
states. Cancellation terminates/reaps the owned process before locks release;
uncertain cleanup retains locks until CLI process exit. A mutation that started
may be partial after a failure or cancellation. The result explicitly requests
a fresh inspection; no automatic replay, prune, forced cleanup or recursive
deletion occurs. Result text is untrusted and the TUI applies terminal escaping.

The application calls inspect, displays entries, builds an immutable mutation
preview, obtains explicit confirmation, then starts/polls that approved job.
The module is absent from model tools, the managed-engine protocol and generic
permission escalation. Inspect remains available during Plan.
