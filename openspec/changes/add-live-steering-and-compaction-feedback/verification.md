# Verification

Host: DESKTOP-FUAQMFB, Windows x64, 2026-11-09.
CLI baseline: `84e76706a61abda3d3e6fb0702814c5bf166b5b2`.
Sengoo baseline: `30adea0d2e421d751da59af43a84c6f9e2e7fbfa`.
Existing unrelated changes, credentials and user histories were preserved.
The installer stopped no user process; its installation inventory contained no
running user CLI processes. No commit, push or public release is part of this change.

## Candidate

- `target/live-steering-20261109/candidate-3/sencode-sg.exe`
- SHA256 `a563a26b29c323b2b3ad7936db932ad5661825bb0c0743d72bf6c2f1b3fcccc8`
- Source runtime, optimization 2; `build-inputs.json` pins source hashes,
  compiler and clang; `build-result.json` confirms unchanged inputs.
- Compiler SHA256 `6507e0e2eff15fd375054334f4e4ff6bccf540431f5f81bd56625f7f0d616252`.
- All product changes are Sengoo. Python/PowerShell only drive verification
  and packaging. No new native boundary was required for these features.

## Native checks

The `live_input`, `engine_control` and `context_compaction` cases pass.
The original compile-and-execute evidence is retained as
`target/live-steering-20261109/native-before-fixture-budget.json`.
After correcting only the unrelated Python fixture budget, the exact native
binaries were rerun with fresh state. `native-evidence.json` records the
unchanged compiler/compiled sources, original evidence hash, current input
hashes and binary hashes. No modified Sengoo input was accepted for reuse.

Coverage includes first/second Enter, FIFO, duplicate transfer suppression,
multiline/menu/dialog focus, stale IDs, unknown policy fields, cancellation,
red wrapped notices, no tool hit targets on notices, NO_COLOR, summary activity,
complete context units, and retained cumulative accounting.

## Host and Windows console checks

The final executable passes the dedicated three-protocol steering fixture
(12 named checks) and the owned native Windows console fixture (4 checks).
These cover in-flight HTTP completion, durable acknowledgment, single execution
of a command, paired tool history, cancellation before insertion, duplicate IDs
after restart, actual second Enter, retained drafts, private summary reasoning,
Compacting, Chinese completion, red console cells and restored terminal modes.

`target/live-steering-20261109/production-evidence.json` records ten passing
integration suites against this exact executable: live steering host/console,
request recovery, three-protocol cancel/resume (24 checks), Agent reliability,
Responses tool continuation, Goal acceptance, large child evidence,
workbench permissions/model controls, and fullscreen (25 checks).
The fullscreen fixture measures 40 input samples with four active loopback SSE
streams: p95 21.3894 ms, maximum 22.0603 ms. This is the measured native Windows
console workload, not a claim about other terminal hosts or remote latency.

The broad recovery fixture previously pinned the compaction Goal to 30 requests.
Its later six-attempt summary failure reached that explicit saved cap; passing
50 on a later turn correctly did not silently override the user's saved budget.
The compaction fixture now selects the ordinary unlimited mode explicitly and
asserts that it remains unlimited. The separate two-request budget exhaustion
case is preserved. The failed run remains in
`production-fixture-budget-failure.json`; it is not counted as a pass.

## Package and gates

Prepared package:
`target/packages-live-steering-20261109-v1/sencode-cli-0.1.0-dev.0-windows-x64.zip`
SHA256 `e68beac41e9cf0c4e5d3fb208def7a3f0b0e76f1aa535d601c6b7f90a54b9181`.
The isolated installer/rollback/alias smoke passes against this executable.
Strict OpenSpec validation passes 37 CLI and 75 Sengoo items.

`candidate-3/final-gates.json` passes source/binary hashes, native re-execution
provenance, all ten integration suites, archive/smoke checks and strict specs.
`candidate-3/local-install-evidence.json` confirms installation into
`D:/SencodeCLI`: 15 payload files and six direct/bare/forwarder entrypoints
match the candidate, with PATH unchanged. Both `sen` and `sencode` are updated.
Rollback is the previous evidence-digest package, executable SHA256
`02134a38cb7a98ce726619b44299e64ff5e6654dbdbf1e57bdd098f975bb0410`.
The rollback manifest and every payload checksum were verified. Running-image
upgrade/rollback behavior was separately exercised by the isolated installer smoke.

## Limits

These are local source-development, loopback-provider, owned-console and
installation checks. They do not establish live-service, fresh-VM, four-platform,
or all-repository qualification. Managed backend steering is explicitly refused.
An in-flight remote request/tool batch finishes before the condition is consumed.

The previously recorded generic engine-host ordinary Goal-followup failure
(`context_recovery`, code13) is outside this passing subset and is not claimed
fixed. Its installed-baseline/candidate comparison remains under
`target/evidence-digest-20261109/engine-baseline.json` and
`production-with-existing-engine-failure.json`. Existing language ownership
limitations also remain; the Agent ecosystem roadmap is a proposal, not a
claim that the SDK packages are already available.
