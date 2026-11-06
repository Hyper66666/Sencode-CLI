# Implementation gates

- [x] Add a Responses reasoning-item continuation fixture and protocol tests.
- [x] Persist and replay bounded reasoning items with normalized tool calls.
- [x] Add Bash discovery, shell metadata and process cleanup tests.
- [x] Convert model command fixtures to Bash syntax without weakening policy.
- [x] Stop repaint-driven cursor visibility resets and remove composer Thinking.
- [x] Reduce growing-response render work and verify incremental output and input latency.
- [x] Add bounded model question options with keyboard selection, custom answer and cancellation.
- [x] Show grey pending insertion previews and verify Esc retracts without losing drafts or cancelling the active turn.
- [x] Add local project prompt search, draft stash and complete-code copy selection with bounded native and console checks.
- [x] Reference original pasted images with blue atomic chips and bounded temporary fallback for pixel-only clipboard.
- [x] Qualify explicit image submission, target capabilities and reference recovery across the three protocols.
- [x] Run provider, executor, TUI and hidden-console acceptance on one candidate.
- [x] Update verification evidence and install smoke for the corrected candidate.

Evidence: `sencode-cli/docs/responses-shell-cursor-verification.md` and
`sencode-cli/target/interactions-final-20261105-opt/` record the candidate hash,
six final public/host suites, 24 real-console checks, isolated installation and
installed aliases. Native component evidence is linked separately. This is an
internal `source-development` candidate, not a public release qualification.
Live user clipboard, real provider services and a fresh Windows VM remain
unqualified; the clipboard boundary uses isolated fixtures and real GDI+.
