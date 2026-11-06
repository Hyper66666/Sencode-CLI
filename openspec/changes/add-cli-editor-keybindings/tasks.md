# Owner and baseline

UI owner: `/root/reference_tui_commands`; umbrella:
`add-cli-fullscreen-local-parity`. Integration owner retains frontend/main,
diagnostics, packaging and candidate freeze. Baseline repository HEAD:
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a`; host `DESKTOP-FUAQMFB` (Windows x64).
Existing uncommitted work is preserved and is not implied by this SHA.

- [x] Add strict keymap schema, reserved-input policy and pure editor contracts.
- [x] Re-run standalone native schema/Vim/Unicode/paste/undo tests after the last independent audit edits, including duplicate JSON members and escaped aliases.
- [x] Add read-only keymap file fixture (valid, invalid UTF-8, oversize, defaults).
- [x] Connect fullscreen `/keys`, current mode indicator and explicit cancel hint.
- [x] Connect `/read` focus and safe return to the original composer.
- [x] Run native UiApp integration tests, including queue/approval boundaries and stream-completion anchors.
- [x] Run actual Windows console keymap/Vim/read/default-Escape checks (11 independent checks).
- [x] Validate this OpenSpec child and record exact private candidate evidence (production14, four SSE streams, p95 23.2116 ms).
- [x] Preserve a stable visible message through 80/120/160-column reflow and a new streaming tail, with full native UiApp suite plus 5 actual Windows-console checks (`target/worktree-tui/resize-console-evidence.json`, rendering-only synthetic driver; focused follow-up owner: `/root/worktree_tui`). Final combined production candidate remains the integration owner's gate.
