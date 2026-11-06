# Explicit user terminal jobs

`src/pty_session.sg` is the independent Sengoo owner for Windows user terminal
jobs. The frontend must provide an explicit launch/approval interaction before
calling it. It is not registered as a model tool and does not change permission
for noninteractive `run_command` or managed account execution.

## Frontend integration

1. Create `PtySessionSpec` using `pty_session_spec(executable, absolute_cwd)`.
   Push owned `String` argv into `spec.args`; set optional string/null values
   in `spec.env`. Default dimensions are 96x28. Whole-parent `inherit_env=true`
   is rejected by the CLI owner. The underlying std::pty remains generic.
2. Call `pty_session_preview(workspace_root, &spec)` for an escaped JSON launch
   preview, and retain `pty_session_approval_key(workspace_root, &spec)` with
   that interaction. Keep the exact spec until the user approves. Do not log
   the preview: explicit environment/argv may contain sensitive user input.
3. Call `pty_session_start(&state, workspace_root, &policy, spec, approved,
   approval_key)`. Missing approval, changed request data, Plan, child-policy
   depth and noninteractive policy are rejected. Permission to run ordinary
   commands or edit a workspace does not approve an interactive terminal.
4. Retain the owning `PtySession` in the frontend. Call `pty_session_read`
   with a mutable Buffer and poll bounded intervals; forward only explicit
   user terminal bytes through `pty_session_write` with the current policy.
   `pty_session_resize` changes the live dimensions. The module does not read
   keyboard events or route model text to a shell.
5. Call `pty_session_close` on explicit cancel, tab close or frontend exit.
   Scope Drop also terminates the owned tree. Entering Plan must close the
   existing terminal or refuse the mode change: an already running shell can
   continue effects without new input. Writes independently reject Plan.

The module requires the sibling Sengoo `std::pty` implementation and
`tree_quiescent()` method. Windows-only qualification applies; there is no
portable fallback shell. `pty_session_status` returns current id/cwd, direct
exit and code, tree quiescence, lock ownership, cleanup state and byte counts.
Call read/poll/refresh first to advance observed process state.

## Workspace and environment

Start requires absolute local-disk workspace/cwd, rejects UNC/device paths,
checks every existing directory ancestor for reparse points, and requires
canonical cwd to be inside canonical workspace. It checks again after taking
the same shared workspace OS lock used by tool execution, keyed by workspace
root rather than a selected child directory. An active writer makes creation
fail without starting a child. Ordinary external OS applications do not obey
this cooperative lock; it is not a system sandbox or a defense against a
hostile OS actor replacing directories between individual checks.

The child starts with a cleared environment. A fixed allowlist copies Windows
OS/tool discovery, temp and home directories, architecture and processor
metadata; provider keys, managed auth overrides and arbitrary parent variables
are excluded. Explicit `spec.env` string edits or null removals apply afterward.
Names use bounded ASCII letters/digits and `_().-`, compared without case.
There are at most 32 edits, 128 argv, 8192 bytes per argv/edit value, and a
262144-byte serialized approval snapshot. Native ConPTY command-line limits
still apply. Proxy/certificate settings can be supplied as explicit user edits;
the module does not copy all parent networking configuration.

The workspace lock stays held while any descendant remains in the owned job.
Direct shell exit and an idle screen are insufficient. A natural end releases
only after `tree_quiescent` and direct-child reap. Close verifies termination,
reap and quiescence before release. Unknown Drop cleanup deliberately detaches
the native lock owner so the OS retains it until that CLI process exits; it
does not make a heartbeat-based takeover or silently declare the workspace idle.

## Display bytes

Read and write use independent bounded std::pty queues. `session.display`
retains the latest 256KiB raw VT bytes. `bytes_seen`, `dropped_bytes` and retained
length identify its absolute position; `pty_session_display_copy` copies it
into a sufficiently large caller Buffer. A ring cut may occur inside UTF-8 or
an escape sequence. A frontend must reset/resynchronize its incremental decoder
and terminal parser when it observes a dropped offset.

The module never prints raw output. The frontend must emulate or safely filter
terminal sequences; it must not write the ring directly into the user's outer
terminal. Full emulation, scrollback, renderer and keyboard focus are separate
frontend work. Transcript/state snapshots are not automatically persisted, and
processes are never replayed or resumed after restart.

## Isolated Windows evidence

Build the standalone test using the matching development compiler and the
existing sgsqlite module map, then run:

```text
sgc --runtime-mode source-development build src/tests_pty_session.sg -O 0 -o target/tests_pty_session.exe
python tests/pty_session_fixture.py target/tests_pty_session.exe
```

The fixture passed on Windows x64 on 2026-11-04 (1.84 seconds). It creates an
isolated SQLite database and Unicode workspace, never opens the normal user
store, and uses fake provider-key sentinels. It checks approval/Plan/stale
requests, out-of-workspace and real junction rejection, Unicode PowerShell
Read-Host/echo, provider environment isolation, natural release, a surviving
descendant after shell exit, cancel and Drop, and more than 500KB of output
within the 256KiB display cap. Normal owner counters return to zero.

A separate test process deliberately loses a valid native process identity to
simulate unknown cleanup. Another process cannot take the workspace lock while
the owner remains alive; terminating that owner releases the retained OS lock.
No current user terminal, real credentials or existing project files are used.

These are working-tree results based on Sencode
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a` and Sengoo
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`, with clang 19.1.7 and MSVC.
Root TUI integration and final same-candidate evidence are separate gates;
this document alone does not claim the terminal pane is exposed in a release.
