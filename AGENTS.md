# Sencode CLI

Read `openspec/AGENTS.md` and `openspec/config.yaml` before architecture or
capability changes. Run OpenSpec commands from this repository root.

Keep agent logic, protocols and the terminal UI in Sengoo under `src/`.
`sencode-config/` owns the React/Tauri configuration companion. Generic native
capabilities belong in the adjacent Sengoo checkout. Preserve shared-state
contracts, upstream notices and existing user changes.

Keep credentials, user histories, reference source trees, generated binaries
and caches out of Git. Use Lore-format commit messages with concrete validation
and remaining limitations. Never claim fixture tests are live-provider evidence.

For cleanup, inventory literal paths, remove files individually and remove
directories only when empty; do not use recursive deletion commands.
