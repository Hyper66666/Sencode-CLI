# Implementation gates

- [x] Reproduce fatal read error, reversed text/tool order and duplicate cards on the installed baseline with a loopback service and real hidden console.
- [x] Implement ordered Sengoo stream segments and stable tool-card updates.
- [x] Add visible-only activity animation, elapsed time and static terminal states.
- [x] Restore canonical public tool history without replay or false running state.
- [x] Pass native timeline, image atom, Markdown, editor and streaming regressions.
- [x] Pass independent read/error-recovery/edit/test/continue and real-console latency checks on one optimized candidate.
- [x] Validate both changes, document source/evidence hashes and update local sen/sencode installation.

Baseline reproduction: `sencode-cli/target/agent-reliability/baseline-v5.json`.

Final Windows x64 candidate: `5b34aaf31a90a964b2b4bc3334f61277d4bd40deed92a711fe28a37d6c52d973`.
Evidence: `sencode-cli/target/tool-reliability-r2-20261105-opt/`:
`native.json`, `agent-reliability.json` (7 checks), `tool-animation.json`,
`fullscreen.json` (24 checks, four-stream input p95 25.0308 ms),
`integration.json` (6 suites), `install-smoke.json` and
`installed-verification.json`. Long-history recovery has its own change and
`long-history-public.json` (12 checks). The optimized build records unchanged
production inputs, compiler and both dirty-tree baseline SHAs.

Each affected change passes strict validation. All Windows changes report
34 passed / 3 pre-existing failures in `add-fusion-selection`,
`add-git-workspace-management` and `add-grok-desktop-backend`; these are recorded
in `openspec-all.log`. This candidate does not claim live paid-provider,
human-clipboard, other-platform or fresh-VM qualification.
