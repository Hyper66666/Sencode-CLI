# Evidence digest verification, 2026-11-09

Host DESKTOP-FUAQMFB, Windows x64. Baselines:

- Sencode CLI `84e76706a61abda3d3e6fb0702814c5bf166b5b2`.
- Sengoo `30adea0d2e421d751da59af43a84c6f9e2e7fbfa`.
- Compiler SHA256 `6507e0e2eff15fd375054334f4e4ff6bccf540431f5f81bd56625f7f0d616252`.

No existing user process was stopped for diagnosis. The user's database was
queried with SQLite mode=ro. Raw user history, command output, credentials and
configuration are not copied into these evidence artifacts.

## Reported failure

The last main command in the screenshot is complete, exit 0, elapsed 500 ms,
not cancelled, not timed out, not truncated. The following request's failed
attempt recorded code 2, HTTP status 0 and no provider failure stage. During
that request a child committed a successful command whose exact encoded tool
result is 106138 bytes. The request failed milliseconds after that commit.

The child projection calls evidence_reference -> state_digest -> legacy
hash_sha256_str, which admits only 65536 bytes. Both reference creation and
evidence_read used this legacy helper despite their 16-MiB source contract.
The parent error path then cancelled/drained the active child. The cancelled
child card is therefore cleanup after the local host error, not evidence that
the user cancelled or that its command failed.

`target/evidence-digest-20261109/digest-before.json` and `digest-before.log`
record an independent reproduction: synthetic 65536-byte source returns 0;
106138 bytes returns error 2, executable exit 1. The installed baseline has the
same call path. No live provider call is necessary to reproduce this boundary.

## Native regression

`native-evidence.json` passes evidence_digest, execution_diagnostics and protocol,
six build-and-run steps, on one frozen source inventory.

The evidence regression independently checks known SHA256 values for empty,
65536, 65537, 106138, 1048576 and 16777216-byte sources. One byte above 16 MiB
remains rejected. The old identity helper continues to reject >64 KiB with
code 2; no published hashing behavior was loosened.

An isolated database checks >64-KiB Unicode tool projection, complete authorized
multi-page retrieval, unrelated-session refusal, stale-source digest rejection,
retained original results, injected malformed-source failure attribution and
persisted host_stage/child_task_id request metadata. Diagnostics name Agent #2
and child_tool_projection, and preserve the no-replay boundary.

The app uses existing Sengoo bounded hash/JSON/process interfaces. There is no
native ABI change or new dependency. Interrupted initial compilation attempts
and failed type checks are retained separately and not counted as passing gates.

## Final product and installation

Final executable SHA256:
`02134a38cb7a98ce726619b44299e64ff5e6654dbdbf1e57bdd098f975bb0410`.
`production-evidence.json` passes seven focused suites on that executable:
large child evidence, three-protocol cancel/resume, agent reliability,
Responses continuation, Goal acceptance, fullscreen and command diagnostics.
The new fixture runs a command with 106138 stdout bytes, retains an exact
106537-byte result, reads first/last evidence pages from the child and an
authorized page from the parent, finishes both tasks and restarts without
repeating the command's single file append. SHA256 agrees with Python hashlib.

Candidate build inputs (546 files), compiler, package and isolation-smoke hashes
pass the explicit final gate under candidate-3/. Fixtures use loopback providers
and owned shells/consoles, not user API credentials.

Archive: `target/packages-evidence-digest-20261109-v1/sencode-cli-0.1.0-dev.0-windows-x64.zip`.
SHA256 `c751d1bf9ea5e48ef37ec0b39bc63142205aee47e54ae66cf7cd3a25961ed93d`.
Isolation smoke verifies both aliases, clean PATH startup, Unicode cwd/argv,
command forwarders, checksum/pin rejection and locked-image rollback.
Candidate-3/local-install-evidence.json passes local installation: fifteen payload
files and six alias/forwarder entrypoints match the final executable. PATH was
unchanged, pre-existing user processes were preserved and the prior command-
diagnostics package was checksum-verified for rollback. Installed sen.exe and
sencode.exe match this candidate; running sessions need restart to load it.

The additional broad engine-host run fails at the ordinary-followup-after-Goal
step with context_recovery/code13. The same unchanged fixture fails at the same
step against the installed pre-fix executable SHA256
`2368e751591c63922760a423aa061b73be6d9defa18def2fdd9daf22bd6c8b93`.
Both outputs are retained as `production-with-existing-engine-failure.json`,
its engine-host log, and `engine-baseline.json` / `engine-baseline.log`.
This is a separate existing recovery failure, not counted as a passing suite
or silently skipped. Final gates explicitly retain this qualification and run
the dedicated large-output fixture plus relevant cancel/Goal/recovery suites.
Its exact root cause remains unconfirmed; the completed large-output fix does
not claim to resolve every context-recovery failure.

This verification does not complete the separate agent-evidence feature plan,
qualify a fresh Windows VM or non-Windows runtime, or claim a full compiler
ownership/sanitizer run. OpenSpec strict validation passes 36 CLI items and 75
Sengoo items; compiler mode is source-development and this is an internal candidate.
