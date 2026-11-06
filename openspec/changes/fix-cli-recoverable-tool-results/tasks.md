# Tasks

- [x] Preserve the minimal status-7 controller reproduction before the fix.
- [x] Implement explicit recoverable result and unknown-outcome classification.
- [x] Align serial and parallel safe-read publication and call-ID deduplication.
- [x] Run the dedicated native recovery and existing batch regressions in isolated directories.
- [x] Record host, source/compiler/binary hashes and validation evidence.
- [x] Validate this change strictly from windows/ and record existing global validation failures.
- [x] Link final-main provider/terminal integration evidence after the integration owner builds the candidate.

Final main SHA256 `5b34aaf31a90a964b2b4bc3334f61277d4bd40deed92a711fe28a37d6c52d973`:
`sencode-cli/target/tool-reliability-r2-20261105-opt/agent-reliability.json`
passes 7 public/real-console checks, including read-error correction,
completed-call deduplication, read/patch/Bash-test/continue, history restoration
and clean terminal exit. `integration.json` passes all 6 existing public/host
suites; `fullscreen.json` passes 24 real-console checks. These use isolated
loopback services and fixture credentials, not a real provider or user state.
