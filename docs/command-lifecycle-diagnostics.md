# Command failures and shell scripts

`run_command` returns the result of one shell invocation. Several lines in its
`command` argument are a script, not independent tool calls. A first-line `rg`
preview does not identify the command which failed later in the script.

Cards now identify multi-line scripts by interpreter and nonempty line count.
Expanding a card shows its bounded script preview after the result. Original
arguments and results remain in the existing tool ledger. Long diagnostics
include the last diagnostic first, then beginning and end excerpts; original
captured stdout/stderr remain unchanged.

New additive command-result fields:

| Field | Meaning |
| --- | --- |
| `termination_reason=exit` | Command, pipes and owned tree settled normally; inspect `exit_code`. |
| `termination_reason=timeout_process` | Deadline expired while the direct process was still active. |
| `termination_reason=timeout_descendants` | Direct shell exited but owned descendants were still active at expiry. |
| `termination_reason=cancelled` | User cancellation requested; tree cleanup precedes completion. |
| `timeout_ms` / `elapsed_ms` | Configured deadline and monotonic observed elapsed milliseconds. |

Existing `exit_code`, `timed_out`, `cancelled` and `is_error` retain their
compatibility. Direct exit 0 plus descendant timeout is an error; the shell's
successful exit does not prove its complete process tree finished. Old results
without new metadata render a conservative process-cleanup timeout explanation.

The executor observes completion before evaluating a deadline. A command already
quiescent when polled is not marked timed out just because observation was late.
Remaining finite buffered output is drained with bounded reads before completion.
Unknown outcomes and cleanup failures still retain execution/write ownership.

The model-facing default remains Bash. Explicit `shell=powershell` prefers an
installed PowerShell 7, with Windows PowerShell fallback. Both configure child
UTF-8 output; no persistent shell or environment settings are changed.

Use focused calls. `rg` exit 1 means no matches. Reading an existing error log
only prints that log; a later command can still set the script's failing status.
Await build commands with an adequate whole-script timeout. `Start-Process` or
shell `&` does not detach a child from this owned execution tree. Use explicit
managed jobs for persistent background work. Commands are not automatically
replayed after side effects or uncertain completion.

When building Sengoo from source with `SENGOO_STDLIB`/`SENGOO_RUNTIME` overrides:

```text
sgc --runtime-mode source-development check path/to/program.sg
sgc --runtime-mode source-development build path/to/program.sg
```

Installed mode deliberately rejects those source overrides. Do not remove its
check or retry the same invocation to bypass the documented runtime selection.
