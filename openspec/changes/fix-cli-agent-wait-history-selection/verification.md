# Local verification — 2026-11-07

Host: DESKTOP-FUAQMFB, Windows x64. Source baselines, with this change applied:

- CLI: `b2b85ef2c8f369f2fd69ef8729ab420cc420959a`.
- Sengoo: `86c6f87975646b91c9cf2d7d069ac06ee4243b9b`.
- Compiler SHA256: `cc280b3bf0ec0bf17650b0745500c72e205ee2d2073af8ea7ed552045570f1b0`.
- Final CLI SHA256: `498085a677f7d8c66d3afcccf233b23f4e73125d0e3d0b1245afd7ceee75363d`.

This is an internal O2 `source-development` candidate, not a published release.
The local `target/agent-reading-20261107/candidate-2/build-inputs.json` records
the complete revisions and individual production/compiler/runtime source hashes;
`build-result.json` verifies those inputs did not change during compilation.

## Passed gates

- Sengoo compiler: 1,157 library tests, including positioned branch diagnostics,
  explicit-unit and early-return compatibility. LLVM 19.1.7 was on the test
  process PATH. A first repeat without clang failed eight native ABI checks;
  that environment failure is retained separately from the successful final run.
- Native CLI cases: `recall_selection`, `input_history`, `tui_input`,
  `tui_editor`, `tui_agents`, `tui_timeline`, `tui_turns`, `sessions`.
- Production executable cases on the final hash: `agent_recall_selection`,
  `session_policy_wait`, `engine_host`, `agent_reliability`, `reading_console`,
  `scroll_target`, `fullscreen`, `workbench_controls`.
- Slow synthetic child streams: explicit waiting uses four parent requests for
  two children; implicit waiting uses three requests and one terminal-results
  notification. Running child previews never become completed results.
- Real console: Unicode selection freezes selected output while generation
  continues, Esc returns to the finished result, ten-entry recall survives exit,
  switch, branch and project rename. Native tests assert exact copied Unicode
  text and Ctrl+C/right-click copy dispatch without cancelling.
- Existing 80/120/160-column reading, diff, permission/model memory, cancellation,
  one-assistant-heading, scroll and command completion scenarios remain passing.
- Both OpenSpec strict validation suites: CLI 25 items, Sengoo 70 items.

The first production batch passed six cases, then its old fullscreen assertion
expected `PROJECT PROMPTS`. The approved session-local history now displays
`SESSION INPUTS / latest 10`. Updating that assertion and rerunning fullscreen
and workbench controls passed on the unchanged final executable. The failed
batch and successful follow-up are both preserved, not relabelled.

## Packaging and installation

`scripts/smoke-install.ps1` passed with an isolated profile, workspace and command
directory. It checked executable-only startup with a system-only PATH, Unicode
arguments, bare aliases, a live image upgrade, locked-alias rollback, checksum
rejection and command collisions. This does not substitute for a fresh Windows VM.

Archive SHA256:
`44b01e365b1a0a183d0826db757df6e69d84fca7b6a5448eac62be5abd6db2fc`.

The verified payload was installed to `D:/SencodeCLI`. Both direct aliases, bare
commands and WindowsApps forwarders passed six entrypoint checks. PATH was not
changed. The previous package was checksum-verified and retained at
`D:/sencode/windows/sencode-cli/target/packages-policy-wait-final-20261106/`.
No user process was terminated. Local JSON/log evidence remains under
`target/agent-reading-20261107/`; production console snapshots are under
`target/acceptance/20261107-050844-787-11f4e6b1/` and
`target/acceptance/20261107-051036-861-ba91f302/`.

## Qualification limits

No live-provider requests were made. Actual Windows clipboard writes were not
qualified: `--clipboard` failed with WinError 5 at private window-station creation,
before changing any clipboard. The default fixture explicitly excludes that
scope; the failure is not a skipped pass. Native Unicode extraction/copy dispatch
and real-console selection passed. The existing generic clipboard API is reused.

Selection currently covers the visible viewport, preserves rendered line breaks
and is bounded to 64 KiB. Recall persists composer text; image-file bindings are
still process-local, so image chips need reattachment after restarting the CLI.
Abrupt process termination may lose queued, not-yet-flushed input. These bounds
do not change tool replay, approval or execution ownership rules.
