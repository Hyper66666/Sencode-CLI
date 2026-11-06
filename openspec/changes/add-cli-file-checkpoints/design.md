# Checkpoint journal

The native file tool holds the session execution lease, workspace write permit
and OS workspace lock. It computes an exact before/after pair, persists prepared
intent, revalidates current bytes, publishes the file atomically and commits
complete status. No write proceeds if checkpoint persistence fails.

The journal retains at most 32 edits and 8 MiB of encoded state. Completed older
entries can be evicted; unresolved intent blocks eviction. An interrupted write
is never retried by opening the database. Explicit restoration accepts prepared
entries only when current bytes match the expected after value.

Rewind previews the diff, presents a fresh-input default-cancel selector, then
reacquires session execution and workspace locks. It rechecks bytes and records
restoring intent before changing one file. A newly created file is removed;
an existing file is atomically restored. Failure leaves an explicit journal
record. Unknown restoring entries require manual inspection, not automatic replay.

Files are limited to the same 1 MiB UTF-8 boundary as native tools. Paths pass
the workspace traversal/reparse guard. This is process-coordinated protection;
an external application can still race the final filesystem operation. Shell
effects and official runtime tools do not have file snapshots in this version.
