# Command lifecycle verification, 2026-11-09

Baselines on DESKTOP-FUAQMFB, Windows x64:

- Sencode CLI `390ddc2c6999e7eba801b9d636d4c4038226236b`.
- Sengoo `0039f59e04e68acc386c9f49497b32178bc879b9`.
- Compiler SHA256 `6507e0e2eff15fd375054334f4e4ff6bccf540431f5f81bd56625f7f0d616252`.

Existing local viewport/runtime changes and user agent-evidence additions are
preserved. This change edits the executor, command schema advice, presentation,
its regression fixtures and docs; it does not edit the agent-evidence modules.
Candidate source hashes record the entire integrated build. Native executable
uses source-development runtime and clang 19.1.7, not a published release.

## Read-only reported evidence

Inspection of the local ledger used SQLite `mode=ro`. No credentials, unrelated
history or user database changes were needed. Commands shown in the screenshot
are multi-line scripts:

- The first directory listing also launched an owned Cargo child through
  `Start-Process`, with a 10-second overall deadline. Successful shell exit does
  not prove that child finished.
- The log-read card also searched directories and ran a piped rg query; its
  final status cannot be attributed to the first `Get-Content` line alone.
- The candidate-path script also ran Cargo with a 60-second deadline; its
  captured log included a successful build. Historical metadata does not show
  which descendant or pipe was alive at the final poll, so no exact historical
  cause is invented for that timeout.
- The rg-first script contained two later `sgc check` invocations after setting
  `SENGOO_STDLIB`. They omitted `--runtime-mode source-development`, explaining
  the recorded compiler errors. The tool result was not misassigned to rg;
  first-line-only presentation made it appear so.

## Independent regression

`target/command-diagnostics-20261109/reproduction-evidence.json`: command `exit 0`
was polled after a 500 ms delay with a 100 ms deadline. Before the change its
direct exit code was 0 but `timed_out=true` and regression exit 1. This proves
an independent completion/deadline ordering defect; it does not establish the
exact timing of an old call whose intermediate process state was not logged.

The new command-lifecycle fixture verifies late-poll completion, original output
draining, actual process timeout, parent-exit-0/active-descendant timeout,
cancellation and process-tree cleanup, PowerShell 7 preference, UTF-8 output,
multi-line identity, expanded script and the last diagnostic in a collapsed
card. It checks native process-resource counts return to zero.

`native-evidence.json`: command_lifecycle, executor, reading_experience and
protocol passed, eight build/run steps. Existing Bash default, missing command,
UTF-8 replacement/NUL handling, Windows batch quoting and historical malformed
optional flags remain covered. All records are under
`D:/Sencode-CLI/target/command-diagnostics-20261109/`.

Final candidate SHA256:
`2368e751591c63922760a423aa061b73be6d9defa18def2fdd9daf22bd6c8b93`.
`production-evidence.json` passes eight same-executable suites: command diagnostics,
agent reliability, three-protocol cancel/resume, Responses continuation, Goal
acceptance, fullscreen, background jobs and long-history scrolling. All use
synthetic loopback providers and actual owned shell/process/console operations.
The new fixture checks a later command's exit 7, actual rg success, default Bash,
descendant timeout attribution and exactly-once durable results. `final-gates.json`
passes candidate, compiler, source inventories, package and isolation-smoke hashes.

Archive: `target/packages-command-diagnostics-20261109-v1/sencode-cli-0.1.0-dev.0-windows-x64.zip`.
SHA256 `b1af12e79f219f99037332cc9f5300ec9d90715c3def0dba23888cfad6741124`.
Isolation smoke passes both command aliases, Unicode paths, clean PATH startup,
owned forwarders and locked-image rollback. Candidate `local-install-evidence.json`
passes all fifteen payload files and six installed alias/forwarder entrypoints.
The previous viewport package was verified as the rollback source. PATH was
unchanged and no pre-existing user process was stopped. Installed `sen.exe` and
`sencode.exe` both match the final candidate; existing running processes load
the update only after restart.

OpenSpec strict validation passes 35 CLI items and 75 Sengoo items.
Synthetic provider checks are distinct from live-service validation. No fresh
Windows VM, non-Windows execution or full ownership/sanitizer suite is claimed.

Sengoo's existing owned-process and monotonic-clock APIs were sufficient; no new
native API or ABI change was necessary. Its local agent instructions now state
the source-development invocation and owned-background-process behavior.
