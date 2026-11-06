# Tasks

- [x] Capture the child-event JSON projection defect and missing mode/effort controls on the installed baseline. Evidence: `sencode-cli/target/workbench-controls-baseline.json`.
- [x] Implement bounded stable child-agent summaries and parent/child event separation in Sengoo. Final native evidence: `sencode-cli/target/agent-projection-native-evidence.json`; public check: `workbench-controls.json` below.
- [x] Resolve effective medium effort with capability-aware request encoding and header display. `medium-effort-evidence.json`, `native-policy-effort-evidence.json` and the actual-request console assertions qualify it.
- [x] Implement manual/auto-edit/full policy with explicit host admission and Plan/child restrictions. `permissions-evidence.json` and `native-policy-effort-evidence.json` pass.
- [x] Add modal-safe Shift+Tab cycling and a persistent composer permission footer. `native-ui-evidence.json` and `workbench-controls.json` pass; Sengoo BackTab has independent `D:/Sengoo/target/terminal-backtab/evidence.json`.
- [x] Pass native projection, policy, effort, key/focus and existing controller regressions. Final projection rerun plus nine component suites, `public-regression-evidence.json` and `host-regression-evidence.json` pass.
- [x] Pass public real-console child streaming, effort snapshot and permission-cycle checks on one optimized main. `workbench-controls.json` 16/16 and `fullscreen-evidence.json` 24/24 qualify SHA256 `11ac156927370d3dbe366d8fd7d4f7ca6e921c7813b56a9c53bab611ad12612f`.
- [x] Validate OpenSpec, record candidate hashes/limits, package and update local aliases after installation smoke. New change strict passes; full CLI validation is 35 pass / 3 pre-existing unrelated strict warnings, documented in `sencode-cli/docs/agent-mode-controls-verification.md`. `install-smoke.json` and `installed-alias-evidence.json` pass.

Unless prefixed above, final evidence paths are under
`sencode-cli/target/agent-mode-controls-20261105/`. Historical component records
`medium-effort-evidence.json` and `permissions-evidence.json` remain under
`sencode-cli/target/`. The candidate uses an optimized source-development runtime
and is not a public-release or fresh-VM qualification.
