# Local Windows evidence

Host: Windows x64, 2026-11-05. Sencode base HEAD:
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a`; Sengoo base HEAD:
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`. Both working trees contain ongoing
development. The evidence records file hashes and does not claim a release SHA.

The pre-repair native binary seeds 1105 isolated rows, reads only 1000 and
fails its completeness assertion. See `target/long-history-before.log` and
`target/long-history-before-build.log`.

The following native checks pass against the frozen production sources:

- `target/long-history-state.log`: complete 1105-row history and newest row,
  metadata, absolute range/tail, latest 512-window, smaller newest rich window,
  full/tail node admission, single-row byte admission and zero retained bounded
  JSON documents/reservation.
- `target/long-history-context.log`: checkpoint watermark beyond 1000,
  complete assistant/tool pair, new tail and reopen, orphan/future watermark
  rejection, count/byte failclosed admission, unchanged budget reads, 1900-row
  public history plus 900 tiny newer rows auto-compacted through a real
  loopback EngineRequest, absolute watermark 1900, request count 37 to 38 and
  reported token count 123456 to 123557, exact reduced-context restart.
- `target/state-long-history.log`: existing native shared-store acceptance,
  including version rejection, shared authority and fenced recovery.
- `target/controller-recovery-long-history.log`: existing native recoverable
  tool regression in ordinary Git and missing-Git environments.
- `target/long-history-malformed.log`: the existing native state inspector
  reads a deliberately corrupted disposable database and retains JSON status
  10. The fixture deliberately bypasses that temporary database's `json_valid`
  CHECK; normal writes remain guarded. Only the exact runtime node-limit
  diagnostic is normalized to resource status 13.
- `target/long-history-openspec.log`: this change validates strictly.

Production source SHA256:

```text
state.sg      5e8377aac5293f334a88cb7576cbe9401f7ff6157a357d302271abb5cc28b86d
controller.sg 2dfcf75fae6021dcdeca6fc77c68f7b879b584a69557d652c551d17612e63a1b
```

Native fixture binary SHA256:

```text
test-long-history-state.exe   fdd3d79a11389eeb7b4d8cc668755cbb09fb6484ec12a3774907321caa86f356
test-long-history-context.exe 33a766b570ca369f7cf616d22eeab406beb0836475d147bd2d399342efe1a407
```

Commands:

```text
python tests/long_history_fixture.py target/test-long-history-state.exe target/test-long-history-context.exe
python tests/long_history_fixture.py target/test-state-long-history.exe
python tests/controller_recovery_fixture.py target/test-controller-recovery-long-history.exe
openspec validate fix-cli-long-history-recovery --strict --no-interactive
```

The complete local source/compiler/binary/log hash manifest is
`D:/sencode/windows/sencode-cli/target/long-history-evidence.json`. No real API,
user key, provider configuration or user project was used. The unique
generated loopback fixture credential was removed; disposable data was cleaned
with individual file removals and empty-directory removals.

Final UI/main executable validation belongs to the integration owner and is
not inferred from these native tests. Other hosts, cold installation and real
provider qualification are not claimed by this change. The old uncheckpointed
oversized-session boundary is documented in `docs/long-history-recovery.md`.
