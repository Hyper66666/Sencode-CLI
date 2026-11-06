# Data ownership and lifecycle

The shared catalog remains the live desktop/CLI execution authority. A CLI
connection attaches `<cwd>/.sencode/history.sqlite3` with a private alias and
installs TEMP triggers on its own connection. Each committed write to the
selected project's conversation tables is mirrored by those triggers. No global
connection table, credentials, unrelated project or provider-native binding is
copied. An attached-transaction rollback rolls back both sets of writes.

The portable file has its own schema version, project ID, last bound directory
and catalog path. A migration file lock serializes opening. A missing portable
file adopts the shared catalog's current project ID (including old path hashes),
or creates a stable ID. Opening an existing portable file validates its schema
objects and column layout; arbitrary views/triggers and unknown versions fail.

If the shared catalog already knows this ID, per-row revisions, update times and
cumulative counters are checked under a writer reservation before refreshing the
portable snapshot. Missing catalog rows or newer archived rows cause a refusal
that preserves the archive for explicit reconciliation. Equal or newer catalog
rows refresh the mirror before installing capture triggers. Renaming an idle root
updates the project's directory without changing project/session/message IDs.
An existing original root or a different existing catalog causes an explicit
conflict, not an automatic merge. Active or cleanup-uncertain execution blocks
relocation. When the old catalog is absent, `--import-history` is required to
restore an idle portable file's scoped rows; unknown execution outcomes block
import. Goal objectives and cumulative budgets survive in a paused state. Cached
model context, Plan paths, extension/checkpoint state and acceptance shell commands
are not imported. No request or tool is restarted by restoration.

Local history is untrusted data: unknown schema objects, unrelated project rows,
ID conflicts, nonregular history files and files over 256 MiB are refused. The
configuration directory must be a real directory. No local history config can
grant permission or execute SQL supplied as row content. Schema v2 checks exact
generated table/index shapes, column affinities, required values, project scope
and message roles. Both SQLite and the consuming Sengoo JSON parser validate
roles so duplicate JSON members cannot change their meaning at restoration.
This schema is private; the unreleased experimental schema v1 is refused.
The CLI appends private history patterns to `.sencode/.gitignore`, preserving
existing bytes. Close clients before copying or moving the project.

SQLite WAL does not guarantee power-loss atomicity across attached databases.
On a normal reopen the shared catalog reconciles the mirror; complete loss of
the catalog together with a power failure needs separate recovery qualification.
The worktree/checkpoint ledgers and managed native runtime sessions remain at
their existing locations and are not advertised as portable conversations.
