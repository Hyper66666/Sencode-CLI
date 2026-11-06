# Fullscreen worktree integration

The application owns a `FrontWorktree` state machine and calls the existing
`worktree_inspect_start`, `worktree_start` and `worktree_poll` APIs between
terminal events. It never calls the standalone blocking management wrapper.
The idle foreground application is the only entry point; model tools, children
and managed-engine protocol remain unchanged.

`/worktree` and `/worktree list` inspect the current checkout. The first UI
version accepts `/worktree create ABSOLUTE_PATH` and
`/worktree remove ABSOLUTE_PATH`. The entire remaining text is one literal
absolute path, including spaces. Creation is detached; an exact new branch is
still selected through `sen worktree create PATH --branch EXACT_NAME`.

An operation proceeds through idle, inspecting, awaiting confirmation,
mutating and terminal result states. A mutation first obtains a new inspection,
captures an immutable spec and approval fingerprint, prints its escaped exact
preview, discards pending console input and opens a default-Cancel picker.
Confirmation is one-use and cannot outlive that picker. The approved job still
refreshes source identity, HEAD and target under the module's existing locks.
Plan permits inspection and refuses create/remove before inspection begins.

Inspection and mutation pause queued submissions. Input editing and rendering
continue; a model submission cannot overtake a local worktree job. The queue
stays paused after completion or cancellation until explicitly resumed.
Ordinary application actions, connection/session changes and user terminal
launches are refused while an operation or its confirmation owns the UI. This
also prevents ordinary SQLite writes during the module's removal write
reservation. The idle execution child receives no submission in that interval.

Ctrl+C or Esc cancels the current job. Exit first closes the job and certifies
the owned process tree before normal handoff. Cancellation after a mutation
started always requests fresh inspection and never replays or force-cleans.
Unprovable process cleanup enters a sticky blocked state: no queued request,
ordinary database write, user terminal or later worktree action may run before
the application exits. Existing retained native locks are not cleared by UI
state resets.

The slice also makes fullscreen and scrolling help consume the same command
registry with host-specific availability. Scrolling help excludes fullscreen
editing, clipboard, terminal and worktree commands that its dispatcher does not
implement. `/model` describes model selection; it does not claim an exposed
reasoning-level selector.

Verification must use an isolated real Windows console and production main,
with fresh/default-deny approvals, changed HEAD, Plan, cancellation, same-root
exclusion, queue deferral, no spawned terminal ledger and restored console
modes. Synthetic state coverage additionally verifies sticky unknown cleanup
and that a consumed approval cannot be reused. Installed artifacts are not
overwritten by development verification.

The private Windows x64 candidate
`8C0C384135B37D6DB0E25179AD5839905EC72F77D012E25CB7BF3213B36B7A39`
passed 13 real-console checks in `target/worktree-tui/console-evidence.json`.
The controller used temporary repositories, profiles and databases, no provider
or credentials, and a separately compiled Git shim only for deterministic
reserved-removal/inspection cancellation. The real Git cases and synthetic
slow-process cases are named separately in that evidence. The temporary
removal held an actual SQLite writer reservation, refused competing frontend
actions, retained queued input, reaped an actual descendant and allowed a new
writer only after cleanup. This verifies the private candidate; the final
combined/installed executable remains an independent integration gate.
