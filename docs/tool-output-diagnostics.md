# Tool output and execution diagnostics

Command stdout/stderr retain valid UTF-8 spans even when other bytes are malformed.
Only malformed subsequences become U+FFFD. Structured command content adds
`stdout_lossy`, `stderr_lossy`, `stdout_bytes` and `stderr_bytes`; byte counts refer
to captured original bytes, before replacement. This does not guess legacy
encodings. Embedded NUL is displayed as visible `\0`; `stdout_nul_escaped` and
`stderr_nul_escaped` mark this conversion and preserve diagnostic text after NUL.
Explicit PowerShell commands configure UTF-8 within their child shell;
model-facing commands continue to default to Bash.

Installed command jobs can use the bundled ripgrep without an inherited tool
PATH. Use `rg -n -g "*.html" "pattern" .` across shells. Bash also expands bare
file globs; PowerShell and CMD pass `*.html` literally to native executables.
Exit 1 from ripgrep means no match and remains an ordinary result for the agent.

A known nonzero process exit is an error result delivered to the model. A proven
prelaunch configuration failure adds `launch_failed`, `no_side_effects`, and its
original `error_code`. Process/IO errors after spawn remain conservative; unknown
effects or unverified cleanup pause execution and forbid automatic replay.

Host result schema 1 retains `code`, `success` and `content`, adding monotonic
`elapsed_ms` for executed submissions and a `diagnostic` object for failures.
The diagnostic's `reason`, `stage`, `tool` and `call_id` attribute the actual
boundary. `outcome_unknown` is explicit evidence, never inferred from code 20;
`automatic_replay_forbidden` is true for unknown effects/cleanup. Provider,
context, budget and permission failures have their own messages. The first cause
survives cleanup; subsequent cleanup uncertainty can strengthen its pause rule.

The diagnostic context is a private actor-local host record. It is never stored
in a raw-terminal input queue or mistaken for a key. Original numeric statuses
and existing `engine_result` callers remain compatible.
