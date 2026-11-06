# Project-local portable CLI history

## Why

The user requires conversations to travel with the project's `.sencode` folder,
including when its root directory is renamed. A directory hash in a global
catalog cannot provide that identity or carry the conversation data.

## Capabilities

- A versioned `.sencode/history.sqlite3` contains a stable project ID and only
  that project's public sessions, messages, tool outcomes, modes and usage.
- CLI writes update the local copy in the same attached SQLite transaction.
- Idle relocation rebinds the existing project ID; missing catalogs can explicitly
  import an idle portable history without rerunning work.
- Existing directory-bound projects are adopted without changing session IDs.

## Non-Goals

No API secrets, official runtime credentials, automatic Goal recovery, folder
copy merging, cross-machine active execution or cloud synchronization. Desktop
currently continues to write its shared catalog; its latest changes are captured
when this CLI next opens the project. This change does not qualify continuously
portable desktop-only writes or power-loss atomicity of two WAL databases.

## Ownership and dependencies

The history foundation owner maintains `project_history.sg`; the fixture owner
maintains its independent probe and expanded regression suite. The integration
owner maintains main startup, public acceptance, packaging and documentation.
Shared storage v1/schema29 remains execution authority. Existing OS locks,
fencing, changelog and tool deduplication stay in force.
