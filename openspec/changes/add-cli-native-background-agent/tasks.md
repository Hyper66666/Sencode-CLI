# Native background Agent gates

- [x] Compile job protocol/store/host/client against the generic detached launch API.
- [x] Verify launcher exit, real IPC attach, Unicode streaming and durable cursor logs.
- [x] Verify controller/observer boundaries, stale epochs and approval loss without writes.
- [x] Verify detached interaction refusal and Goal disconnect pause with preserved counters.
- [x] Verify real tool cancellation, owned cleanup and idempotent stop.
- [x] Verify bootstrap expiry, crash/no-replay, malformed frames, identity mismatch and retention.
- [x] Record candidate/source/compiler SHA256, repository SHA, host and exact fixture commands.
- [ ] Connect root-owned CLI/TUI entry points and rerun installed source-free acceptance.
  Public main and installed WindowsApps routing pass `background_public_fixture.py`
  on `9853763c...`; see `target/acceptance-workbench-installed-frozen.json`.
  The explicit CLI entry points are delivered. A fullscreen background-job panel
  and a development-tools-free Windows VM remain unverified, so this combined
  gate is intentionally open.

Only actual named checks may complete these gates. The fixture is synthetic
provider evidence and does not claim a live account or public release.

Named checks and candidate identities are recorded in `evidence.md`; detailed
per-source SHA256 records live in ignored `sencode-cli/target/background/evidence.json`.
