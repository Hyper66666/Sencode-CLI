# Windows evidence, 2026-11-04

Source baseline: Sencode `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`,
Sengoo `d46b3f6cd8d6e770734f98edc57aa67cb931e26a`; both working trees dirty.
Application SHA256 `9853763ca08f15c3b8bdd79038850438709eb30dc7a421a07139ca135cd43591`.
Compiler SHA256 `b79895635aabd0acfef17a81f9f7f0060fcc473bc56b41da47ebb7ff6912169c`.

- `target/acceptance-workbench-new-native-frozen.json`: VT bounds/Unicode/resize
  and pane execution/workspace/ledger/Plan/EOF/arrow/paste checks pass.
- `target/acceptance-workbench-product-frozen.json`: actual main pane 14 checks
  pass, plus default fullscreen and existing agent protocol regressions.
- `target/acceptance-workbench-installed-frozen.json`: same 14 pane checks through
  installed WindowsApps `sen.exe`, including real PowerShell/CMD, fresh approval,
  resize, OSC suppression, Ctrl+C and three-generation Ctrl+Q cleanup. Explicit
  close records exit_code other than the uninitialized -1 sentinel.
- `target/workbench-install-smoke.json`: package/aliases/rollback pass on this host.

All aggregate reports recheck source and compiler; product reports additionally
recheck the selected executable. Full source snapshot, host and report hashes:
`target/workbench-candidate-evidence.json`, `target/workbench-candidate-source.json`.
Strict `openspec validate add-cli-safe-terminal-pane --strict` passes.

Intermediate failed logs remain diagnostic history: the original cmd mixed
separator failure is retained separately, and final candidate tests verify the
canonical executable fix. Earlier native fixture issues (relative cwd and fake
terminal dimensions) are fixed; final runs use canonical paths and preserve
screen size when terminal dimensions are unavailable.

This is a bounded monochrome VT subset, with no alternate-screen restoration or
terminal response emulation. There is no claim of fresh-VM or live-account testing.
