# Explicit user terminal pane

## Capabilities

Expose the existing owned ConPTY session through a fullscreen-only `/terminal`
(`powershell` or `cmd`) action, with an exact launch preview and fresh explicit
approval. Render child bytes through a bounded Sengoo monochrome VT screen.
Preserve the chat draft and isolate terminal focus; return only after cleanup.

## Non-Goals

No model terminal tool, background shell, process replay, raw escape forwarding,
full xterm emulation or shell sandbox. Advanced full-screen applications may
use unsupported terminal features; document the supported subset.

Owner: root (pane, parser, frontend); UI child owns isolated console verification.
Depends on `add-cli-owned-terminal-jobs` and `add-cli-editor-keybindings`.
