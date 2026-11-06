# Explicit user worktree jobs

`worktree.sg` exposes explicit local Git inspection, creation and removal to the
terminal application. These are user actions and are absent from model tools
and the managed-engine protocol. The root application integrator owns the TUI
entry points; the module does not switch the current working directory.

The independent management wrapper is `worktree_cli_run(state, cwd, arguments,
terminal)`, dispatched before creating an agent session:

```text
sen worktree list
sen worktree create "D:\\workspaces\\feature" --branch codex/exact-name
sen worktree remove "D:\\workspaces\\feature"
sen worktree create "D:\\workspaces\\offline" --yes --output-format json
```

Terminal mutation displays an escaped exact JSON preview and asks for fresh
`yes`. Redirected use refuses mutation unless the command contains explicit
`--yes`. The flag approves only the newly inspected exact operation; it changes
no model permission or future default. `--plan` rejects mutation even with
`--yes`. `list` works in Plan and needs no confirmation. The management wrapper
keeps polling and accepts Ctrl+C; the fullscreen application should use the
underlying nonblocking job APIs directly instead of blocking its main loop.

```sg
let mut job = worktree_inspect_start(cwd)?;
while not job.done {
    worktree_poll(state, current_policy, &mut job)?;
    // Continue rendering input; call worktree_cancel on explicit cancellation.
};
let inspection = worktree_result(&job)?;
let spec = worktree_mutation_spec(&inspection, "create", absolute_path, "")?;
let preview = worktree_preview(&spec)?;
let key = worktree_approval_key(&spec)?;
// Display the escaped JSON preview and obtain fresh explicit user confirmation.
let mut mutation = worktree_start(state, current_policy, spec, approved, key.as_str())?;
```

Creation defaults to a detached checkout from the inspected HEAD. A nonempty
branch must be the exact new branch supplied by the user; Git validates it and
creates it with `-b`. No existing branch is reset, and the current checkout's
index, staged/unstaged edits and untracked files are untouched.

Inspection records canonical checkout/common Git directory, HEAD, executable
and NUL-framed porcelain entries. `capability` reports `ready`, `missing_git`,
`not_repository` or `bare_repository`. Other failures retain bounded `status`,
`code`, `message` and optional Git stderr (at most 64 KiB in reports, with a
truncation flag). Both captured streams are bounded to 1 MiB, each command to
30 seconds and the whole job to 120 seconds by default.
The caller must keep polling; each poll performs at most one bounded read per
stream and a process/status transition. No Git operation uses a shell command.

Mutation fingerprints bind the exact source identity/HEAD, operation,
destination, optional branch and selected removal entry. Missing/stale approval,
Plan, child and noninteractive policies reject mutation. Pass the current
policy into every poll, so a policy change before mutation cannot reuse an
earlier permission. Cancellation terminates/reaps the owned process and never
replays it. If a mutation started, `refresh_required` is true even after a
failure: inspect again, because Git may have performed part of the operation.

The module clears the process environment, copies an OS discovery allowlist,
and disables prompting, lazy fetch, network protocols, hooks, fsmonitor,
external diff, submodule recursion and global/system config. It enumerates repository filter driver
keys and overrides clean/smudge/process/required with literal argv. Ambiguous or
oversized filter config refuses execution. Raw result strings remain untrusted;
the frontend must apply the existing terminal escaping rules.

Removal requires a real registered secondary directory. It refuses primary or
current checkouts, locked/prunable entries, reparse paths, tracked changes,
untracked and ignored files. Only `git worktree remove -- <path>` performs the
removal; there is no force, recursive delete, prune, clean or automatic retry.
The module holds common-Git-directory, source and target workspace OS locks.
Known nested project workspace locks are also held, so an idle explicit terminal
in a target subdirectory blocks removal even without an active model execution.
A separate SQLite connection reserves a writer using a zero-row update and
holds associated session leases while checking target execution state and
running final status/removal. Active or cleanup-required execution, running
tool ledger, Meeting and Fusion state refuse removal without being cleared.
New shared-state writers cannot race the final deletion. On unprovable child
cleanup, native lock owners are retained until CLI process exit.
`worktree_status` reports `shared_writes_reserved`; while true, keep rendering
and polling but defer ordinary shared-state writes from the same UI thread.
The separate guard connection uses a zero busy timeout, so another writer
causes a bounded refusal rather than freezing input. Tree quiescence is proven
with the generic Windows Job accounting API, separately from direct-child reap.

The isolated `tests/worktree_fixture.py` creates only temporary Git repositories
and databases. It validates actual Unicode/space paths, detached/exact branch,
approval and Plan, real hook/filter suppression, dirty/untracked/ignored/locked
refusal, shared session/write locks, late-writer exclusion and preservation of
all original checkout edits. Windows x64 is the initial qualification target.
No desktop/client workflow or installed command is claimed by module tests.

The final module fixture passed 37 isolated cases on Windows x64, including
nested project workspace locks, real malicious hook/filter configuration,
bounded flood output and cancellation of a real descendant process. The
independent `tests/worktree_cli_fixture.py` passed 11 headless cases and 3 real
hidden-console approval cases, with console modes restored after each run.
These wrapper cases exercise a dedicated test executable; the application
integration owner separately verifies the final public `sen worktree` entry.
