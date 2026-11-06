## ADDED Requirements

### Requirement: Project-local portable conversations
The CLI SHALL persist scoped conversation data beneath the project `.sencode`
directory and SHALL identify it independently of the root directory name.

#### Scenario: Rename an idle project
- WHEN the user closes the CLI, renames a project root and resumes from it
- THEN the same project, session and message IDs and contents are available.

#### Scenario: Adopt legacy catalog records
- WHEN a directory-bound existing project has no local history yet
- THEN opening it copies its own records without changing session IDs or
  copying other projects or connection credentials.

#### Scenario: Restore after catalog loss
- WHEN an idle project carries a valid local history, its old catalog is absent
  and the user explicitly selects `--import-history`
- THEN a new catalog imports its public conversation and usage, preserving Goal
  budgets in a paused state without starting a Goal, replaying a tool or resuming
  a provider-native session.
- AND cached model context, Plan paths and acceptance shell commands are omitted.

### Requirement: Safe history ownership and recovery
The CLI SHALL reject ambiguous project copies and unresolved execution ownership.

#### Scenario: Original folder still exists
- WHEN a copied history is opened while its original root exists
- THEN the CLI reports a conflict and does not merge conversations.

#### Scenario: Active execution or another catalog
- WHEN relocation has an active or cleanup-uncertain executor, or a different
  existing catalog is bound to the portable history
- THEN startup refuses independent execution authority.

#### Scenario: Transaction rollback and malformed archive
- WHEN a mirrored transaction rolls back
- THEN neither file exposes the rolled-back change.
- WHEN the local database contains an unknown schema object or incompatible version
- THEN startup refuses to import or execute it.

#### Scenario: Catalog is stale or archive roles are ambiguous
- WHEN the catalog is missing archived records or has older per-row revisions
- THEN opening refuses to overwrite the newer archive.
- WHEN duplicate or escaped JSON role fields disagree with the message role
  according to SQLite or the consuming Sengoo parser
- THEN ordinary opening and explicit import both refuse without changing history.

#### Scenario: Private local ignore rules
- WHEN project history is first opened
- THEN history database and migration-lock patterns are appended to
  `.sencode/.gitignore` without replacing its existing contents.
