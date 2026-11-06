## Why

The approved fullscreen CLI plan requires configurable input and familiar modal
editing without allowing a keymap or pasted text to change execution authority.
The existing Unicode editor, command menu and queue provide the base, but users
cannot yet inspect effective keys or choose a bounded Vim-style composer.

## What Changes

- Add a versioned, user-owned JSON keymap, read only with strict size/UTF-8 checks.
- Add fullscreen `/keys` selection, effective binding help and a small Vim subset.
- Add a fullscreen `/read` transcript browsing mode that preserves the composer.
- Preserve Enter completion, explicit submit, fresh approvals, queue ownership
  and normal default-mode Escape cancellation.

## Capabilities

- New: `cli-editor-keybindings`.
- Depends on sibling `add-cli-fullscreen-local-parity` for the Sengoo-owned UI,
  command registry, Unicode layout and host lifecycle. This child solely owns
  composer key configuration, modal editing and auxiliary transcript navigation.
- Generic terminal events remain the existing Sengoo standard-library contract.

## Non-Goals

Full Vim, macros, arbitrary command bindings, command execution, privilege or
approval remapping, writing configuration files, native terminal changes,
background agents and support claims for untested terminal hosts.

## Impact

Only fullscreen Sengoo UI modules and their regression fixtures change. Default
editing remains unchanged unless a user explicitly selects Vim or configures a
keymap. The execution host, desktop database, diagnostics and provider contracts
remain owned by their existing integration owners.
