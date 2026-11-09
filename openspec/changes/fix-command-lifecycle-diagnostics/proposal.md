# Command lifecycle and script diagnostics

The reported cards mix shell exit status, descendant lifetime, multi-command
scripts and preview truncation. Diagnose from read-only ledger evidence before
changing behavior. Implement in Sengoo; existing process/clock APIs suffice.

Capabilities: precise process/descendant timeout classification, completion
before deadline decisions, monotonic timing, safe PowerShell 7 selection with
legacy fallback, and readable multi-line command/error previews.

Non-goals: automatic rerun of commands, relaxing process-tree ownership,
silently changing shell choice, implicit detached jobs or unbounded output.
Existing side effects, permissions and request retries retain their contracts.
