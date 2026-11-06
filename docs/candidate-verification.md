# Windows development candidate verification

The CLI is implemented in Sengoo. Python and PowerShell in `tests/` and
`scripts/` are build, installation and test drivers; an installed CLI does not
invoke them to run its agent loop. Commands selected by the user or model may
invoke the corresponding system tools.

The uncommitted candidate is based on:

| Source | Baseline revision |
| --- | --- |
| Sengoo | `d46b3f6cd8d6e770734f98edc57aa67cb931e26a` |
| Sencode | `a468086401a0d19077b5cf0b6aea3ecff0f04c9a` |

Evidence was produced on Windows x64, 2026-11-04. These baseline revisions do not
identify the modified binaries: match executable SHA256 in the package manifest
and the installation/provider evidence. This work has not been publicly released.

## Checks run on this host

| Area | Executable evidence |
| --- | --- |
| Compiler and editor tools | Compiler 1152 tests; sgc 511 tests, LSP 190 tests, attribute evidence verifier 1 test; installed-runtime distribution 15 tests |
| Ownership | Generated LLVM and split C runtime instrumented with AddressSanitizer; 26 allocated resources released exactly once, String handle count returns to zero; borrowed nested/whole-value replacements included |
| Transport | Four real loopback streams, all three protocols, raw Unicode split across byte boundaries, tool-argument deltas, TLS fixture/certificate rejection, bounded buffers, cancellation, zero residual handles/workers |
| Application | Real executable in a temporary external project: read, patch, command, resume latest/by ID, resume an ID older than 100 sessions, Plan restrictions, Goal verification and pauses, independent child contexts and tool results |
| Scheduling | Four global/two per-connection requests, write FIFO by canonical directory, child cancellation, shared request/token budgets, read-only consultation |
| Shared state | Native Sengoo helper and Rust desktop in separate processes; active-session exclusion, observing startup, idle handoff, public history, preference cursor, engine-binding mirror, obsolete event rejection |
| Desktop regression | Persistence/send-transaction/ACP integration: 160 passed, native subprocess case run separately; projection suite: 61 passed; required shared-store gate includes all 13 tests with zero ignored |
| Official packages | Repacked source archives/registry bundle, checksum verification, external locked consumers, package tests and CSV/SQLite persistence consumer: 18 checks |
| Installation | Both identical aliases in an isolated profile with Windows-only PATH: help, version, invalid arguments, Unicode argv/cwd, native dependency audit, doctor, literal no-argument startup and resume latest/by ID |

Use the matching current reports under `target/`; intermediate candidate reports
remain diagnostic history. A final package must be retested after its executable
changes. Source-development Sengoo runtime provenance is recorded explicitly and
is not a published toolchain qualification.

The desktop/state source hashes and log hashes are recorded in
`target/shared-integration-evidence.json`. Its 160-test run leaves the required
native subprocess case to `scripts/test-shared-store.ps1`; the latter runs all
13 shared-store tests with `--include-ignored`, including that real cross-language
process test. There are no skipped required shared-store checks.

## Workbench installed candidate (2026-11-04)

The current installed application SHA256 is
`9853763ca08f15c3b8bdd79038850438709eb30dc7a421a07139ca135cd43591`.
Both owned installation prefixes contain these bytes. Existing WindowsApps
native forwarders target `D:/SencodeCLI/bin`; bare help/version succeed from
`C:/Users/admin`, outside both source checkouts. No real user database or API
credential was opened by these checks.

`target/acceptance-workbench-new-native-frozen.json` passes five groups / ten
steps: editor integration, bounded VT/resize, terminal execution/ledger/Plan,
job admission/retention, and 37 real isolated worktree operations.
`target/acceptance-workbench-product-frozen.json` passes nine groups / ten steps:
external CLI, fullscreen, actual terminal pane, background public commands,
worktree public commands, engine host, managed protocol fixture, request recovery
and scrolling fallback. Source, compiler and executable hashes are rechecked.

`target/acceptance-workbench-installed-frozen.json` repeats the four fullscreen,
terminal-pane, background and worktree groups through installed WindowsApps
`sen.exe`. Console checks cover double Enter, fresh approvals, Chinese output,
resize, OSC isolation, Ctrl+C, child/grandchild exit, CMD natural exit and
terminal restoration. Terminal ledger records a real exit code on explicit close.
Background checks include lifetime limits, observer/control boundaries, Goal
refusal without retained control, stop cleanup and public log cursors.

The pre-install four-stream production measurement is p95 23.17 ms across 40
input-to-visible samples. This uses real loopback SSE and Win32 console input;
it is not a claim about external API latency or every terminal host.

The ZIP SHA256 is
`59ed80b5ab91571d7287323ae16bbafcfa3df80b819060f1812d58ceb426104b`.
`target/workbench-install-smoke.json` passes isolated restricted-PATH aliases,
Unicode external workspace, resume, tamper/conflict rejection and rollback.
Pinned Codex/ACP binaries and their notices are unchanged from the prior package.
`target/workbench-candidate-evidence.json` links the reports, installed bytes,
compiler hash and `target/workbench-candidate-source.json` dirty-tree snapshot.

The compiler is `b79895635aabd0acfef17a81f9f7f0060fcc473bc56b41da47ebb7ff6912169c`.
The new borrowed String / Drop forwarding fixes pass 1155 compiler tests and
native O0/O2 regressions, with preserved value-based Drop ABI. Sengoo OpenSpec
strict validation passes 60/60. Windows OpenSpec retains three pre-existing
unrelated invalid changes; candidate child changes validate independently.

The candidate adds `/keys`, the documented Vim subset, `/read`, the explicit
`/terminal` pane, `sen worktree` and `sen agent` jobs. It does not close P3–P6:
foreground detach, full worktree TUI, media, LSP/IDE, hooks/plugins/SDK, remote
MCP, durable teams/workflows/monitor/loop and clean-VM/live-account qualification
remain separate work. Independent trials are deferred by the user.

## Previous fullscreen candidate (2026-11-04)

The previous application SHA256 is
`9e3d4980aefd5e221663d764e583d42983cd3b32668517e7e7e66cfc100b154a`.
Both owned prefixes contained these bytes before the workbench update.
WindowsApps native forwarders target the D: installation.
Bare `sen --version` and `sencode --help` pass outside the source checkout.

`target/acceptance-fullscreen-native-frozen.json` passes 17 groups / 34 steps;
`target/acceptance-fullscreen-integration-frozen.json` passes 18 groups / 31
steps. Both recheck source and compiler hashes before accepting the result.
Earlier aggregate reports correctly failed source drift and remain unchanged.
`target/fullscreen-candidate-source.json` records both dirty working trees and
full source hashes before development resumed.

`target/fullscreen-installed-console.json` repeats all 14 production console
checks through installed WindowsApps `sen.exe`, with isolated temporary state.
The production screen/input test uses four actual loopback SSE connections;
the pre-install run measured p95 23.31 ms across 40 input-to-visible samples.
This is a host-local fixture result, not a public-service or fresh-VM result.

The ZIP SHA256 is
`f2d17923213669f6cd8b1f64848e6e4e2d80133e68df689cffb27429e17731e0`.
It includes pinned official Codex 0.144.4 and locally built Sencode ACP
0.2.102, their notices and the audited VC runtime dependency. Actual offline
initialize handshakes pass for both binaries; authenticated turns are unrun.
`target/fullscreen-install-smoke.json` passes tools-absent PATH, both aliases,
Unicode external workspace, resume, tamper/conflict rejection and rollback.
This does not qualify a development-tools-free Windows VM.

This candidate contains full-screen completion, queue editing, native file
checkpoints, readonly diagnostics, bounded retries and model-scoped automatic
compaction. The new keymap/Vim/reading, terminal-pane, worktree and background
work started afterward and is not represented by this installed hash.

## Earlier scrolling TUI candidate

`target/acceptance/tui-final-evidence.json` passes all 14 cases / 26 steps on the
updated source, including the existing provider/tool/Plan/Goal/child regressions.
It rechecks the compiler, CLI sources and Sengoo standard-library sources.
`target/tui-console-evidence.json` passes 12 actual hidden Windows-console checks:
Unicode edits, multiline and bracketed paste, history drafts, Tab commands,
110→48→110 reflow, eight-row input with the cursor at Home, cancellation,
model/Plan/session views, resume, mode/codepage restoration and NO_COLOR.
Legacy `ReadConsoleOutputW` on this host cannot return supplementary emoji even
after direct `WriteConsoleW`; this is calibrated separately. UTF-8 preservation
is also checked through the Sengoo queued-input and external argument tests.

The earlier application SHA256 is
`c0d1619428642c4efd2955d43c1c552ba82ca98db497f3b89236c3a566c4b5d3`.
The ZIP in `target/packages-tui-20261104/` has SHA256
`1c7e278468cddc8860e9ec0b34c19cf6a0d24223df4f0a0919974726a83008dc`.
`target/install-tui-evidence.json` and `target/install-tui-evidence-ps51.json`
record matching package checks on PowerShell 7 and 5.1, including stale PATH,
Unicode/metacharacters, native forwarding, conflict/tamper rejection and rollback.

The application is installed at `D:/SencodeCLI/bin`; owned native forwarders in
`%LOCALAPPDATA%/Microsoft/WindowsApps` target it. The earlier owned C: prefix was
also updated to the same application bytes so pre-existing PATH entries cannot
select the old interface. No real user state or credential was opened by these
installation checks. `target/tui-installed-console-evidence.json` repeats all 12
console checks through the installed WindowsApps `sen.exe`. Independent bare
`sen`/`sencode` startup and resume from two external folders with neither install
bin in PATH pass in `target/installed-global-command-evidence.json`.

`target/tui-candidate-evidence.json` ties those earlier reports and artifacts
together. Fresh-VM, public-provider and independent-trial limitations below still
apply. The following older evidence is retained as historical provenance.

## Earlier local candidate

`target/acceptance/final-evidence.json` records all 12 CLI cases and 23 steps as
passed, with the compiler and application source hashes rechecked at completion.
This includes the Plan/readonly-child Git hook and clean/process/textconv filter
regressions, ordinary headless permission failures and a closed stdout pipe.

The final executable SHA256 is
`3aeddc990a429921479b2e35e4019a353370121efd76f4a004959cc45eb88628`.
Both aliases in `target/packages-verified/` have those same bytes. The ZIP SHA256
is `984088e6d16c2e7328708a90d15bed64ac1b80af6268d8e616fe0de2da239ee6`.
`target/install-evidence-verified.json` and
`target/install-evidence-verified-ps51.json` record the PowerShell 7 and 5.1
isolated installation checks. `target/candidate-evidence.json` ties these reports
to the shared-state and ownership reports.

The candidate has also been installed into the current user's independent
`%LOCALAPPDATA%/SencodeCLI` prefix, adding its `bin` to the user PATH.
`target/user-install-evidence.json` records successful installed help/version
checks. That installation did not open or migrate the user's real database.

## Reproduce

Run `scripts/test.ps1` with the matching Sengoo checkout and a real Python
interpreter for the protocol fixtures. `scripts/test-shared-store.ps1` additionally
requires Rust and the desktop backend dependencies. Pass `-RustOnly` on hosts
without packaged frontend/runtime resources: that option validates Rust state
integration, not a complete desktop installer.

Run `scripts/package.ps1` with every required non-system redistributable supplied
through `-RuntimeDll`, then `scripts/smoke-install.ps1` against the resulting
directory. The latter never changes the user's PATH or uses their database,
connections or API credentials. Local tests use unique disposable credential
targets and remove them on completion.

## Open delivery gates

- A fresh Windows VM, public-provider requests and independent user trials have
  not been qualified. Restricted PATH on a development host does not establish
  clean-machine compatibility. Independent trials were deferred by the user.
- The desktop was compiled/tested as a Rust backend with explicit resource
  overrides; a complete desktop installer and frontend package are separate
  gates. Existing desktop data is not migrated by any acceptance test.
- Upgrading an existing schema 28 store requires closing older desktop clients
  and a compatible desktop backup/migration. The CLI refuses that uncoordinated
  upgrade. Automatic old-client admission exclusion is not yet qualified.
- Incomplete desktop executions and CLI tools without a cleanup certificate
  remain interrupted and cannot be taken over merely because their lock is
  released. Automated cross-process tool-tree cleanup certification is pending.
- Required Linux/macOS and release-toolchain matrices are not replaced by these
  Windows checks. Two historical Sencode changes plus the older backend delta
  still fail repository-wide strict OpenSpec validation; this CLI change is
  validated independently.
- Protocol fixtures are not an assertion of compatibility with every provider,
  model or reasoning extension. Official OpenAI documentation could not be
  retrieved from this host during the final audit (TLS connection failure).
- One nested-loop owned `String` return is still conservatively rejected by
  borrow checking. The CLI uses an owned copy; the exact reproducer and diagnosis
  are in the Sengoo checkout's `docs/cli-borrow-limitations.md`.
- The complete fullscreen CLI now has real-console multiline/resize and queued
  input evidence, including four real SSE streams. Other terminal hosts, live
  MCP servers and interactive human accessibility checks remain separate gates.

The package remains a development candidate until the applicable delivery gates
are closed. Refer to `shared-state/README.md` for exact shared-store guarantees.
