# Tasks

- [x] Capture a native isolated 1105-row reproduction before changing the query.
- [x] Implement complete/count/range/tail APIs, bounded recent projection and total/offset metadata.
- [x] Restore canonical checkpoint plus complete tail with stable byte/count admission.
- [x] Trigger compaction at 850 messages and persist the absolute SQL watermark.
- [x] Pass dedicated native state and context regressions, including loopback summary and exact budgets.
- [x] Re-run the existing native state and recoverable-controller regressions.
- [x] Record source/compiler/binary hashes and strict OpenSpec validation.
- [x] Link final UI/executable integration evidence from the integration owner.

Final Windows x64 optimized main SHA256:
`5b34aaf31a90a964b2b4bc3334f61277d4bd40deed92a711fe28a37d6c52d973`.
`sencode-cli/target/tool-reliability-r2-20261105-opt/long-history-public.json`
passes 12 checks: plain/native newest-history restore, correct 1008-row count,
bounded-window disclosure, terminal restoration and project-root rename with
stable session/project identity and complete local archive. The same candidate
passes 7 agent reliability checks, 24 fullscreen checks and 6 public/host
regression suites. `native.json` covers the persistent history-window label and
the context view. `build-inputs.json` and `build-result.json` record frozen
production inputs and compiler identity. No real provider or user state used.
