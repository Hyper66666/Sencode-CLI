# Design

Keep one state owner for each command, both output pipes and its process tree.
Poll actual completion before evaluating a monotonic deadline. Once the direct
process and all descendants are quiescent, drain buffered bytes without marking
an already completed command as execution timeout. Never release the write lease
while descendants can run. Classify expiry as direct-process or descendant
lifetime and preserve the direct exit code as a separate fact.

Use additive result metadata, keeping existing exit_code/timed_out fields. Show
timeout/cancellation before exit status and show the tail as well as the start
of stderr so the decisive diagnostic is not hidden behind compiler warnings.

Keep Bash as the model-facing default. Explicit PowerShell uses an installed
system PowerShell 7 before Windows PowerShell 5.1, without workspace interpreter
lookup or changing the user's environment. Tool advice separates focused calls,
explains owned descendants and does not encourage unsupervised Start-Process.

Command cards identify multi-line scripts with interpreter and nonempty line
count. Their expandable body preserves the script within the existing bounded
preview so a failure in a later command cannot appear to belong only to line 1.
Imported historical results without new fields keep a conservative fallback.

Owner: integration agent for executor, presentation and named regression files.
Leave the user's existing agent-evidence work intact and include its source
hashes in the integrated candidate rather than editing those files.
