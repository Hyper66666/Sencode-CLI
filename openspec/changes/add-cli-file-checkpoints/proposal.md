# Bounded native file checkpoints

## Capabilities
Journal native UTF-8 file writes and patches before effects, retain bounded
checkpoints, preview exact restoration and require explicit confirmation. Reject
external-edit conflicts and active-session contention. Preserve transcript,
budgets and tool deduplication.

## Non-Goals
No shell, managed-runtime, Git or full-directory reversal. No automatic crash
replay and no conversational deletion. This is the file portion of P3 rewind.

Owner: root for journal, frontend and tests; core owns the one controller hook.
Uses the existing extensible shared_modes contract without a schema bump.
