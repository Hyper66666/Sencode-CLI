# Native tool scheduling evidence

Host: Windows x64, 2026-11-05. This record covers the native API engine's
local scheduling slice. No live provider, installed CLI, official runtime,
production database or credential store is used by these checks.

## Behavioral architecture review

The recovered Claude snapshot was read for behavior only; no recovered code was
copied. `StreamingToolExecutor.ts` classifies validated calls, permits safe-read
overlap, stops at non-concurrent barriers and tracks in-flight cancellation.
Its progress and final result handling informed a separate Sengoo state machine.

Sencode's Rust `tool_calls.rs` dispatches approved calls through asynchronous
futures, associates results with source ordinals and serializes calls whose
path arguments match a writer's lock key. Its dispatcher uses raw path strings.
GrokBuild's corresponding dispatcher resolves relative paths, lexical aliases
and existing ancestors before creating file locks. Its lock capability contract
also explains that a missing path key does not establish concurrency safety.

The native CLI retains its stronger workspace-wide canonical-directory FIFO
for writes and commands. It adds bounded contiguous read blocks, conservative
hook fallback and stable result order. This implementation deliberately keeps
explicit write barriers rather than guessing shell or multi-file effects from
path-shaped JSON fields.

## Implemented boundaries

- `tool_schedule.sg`: validates complete inputs, rejects duplicate IDs, limits
  queue length and parallelism, tracks explicit predecessor success, permits
  safe read blocks and preserves exclusive barriers and result ordinals.
- `scheduler.sg`: separates cancellation from cleanup, retains canceled write
  ownership, tracks stable tool leases, retains unreported provider capacity,
  and prevents parent/reap operations from concealing draining descendants.
- `executor_jobs.sg` and the compatible `executor.sg` facade: bounded polling
  jobs, simultaneous stdout/stderr draining, timeout/cancel cleanup and a
  two-stage hardened Git configuration/read job. Direct-child exit alone is
  insufficient for completion. An I/O error keeps cleanup owned until independent
  process-tree liveness checks prove there is no remaining process.
- `controller_tool_batch.sg`: real dispatch integration, durable admission and
  events for built-in Git reads, serial reuse of the existing controller for
  other tools and all configured hooks, source-order history, and cleanup before
  error propagation. File reads remain synchronous and bounded; the loop yields
  between admission groups. They do not use extra state-owner threads.
- `children.sg`: a child is visibly terminal only after scheduler cleanup and
  finish succeed. Captured provider effort is forwarded to child requests.

This slice does not claim a general asynchronous MCP/shell executor or fully
asynchronous child-tool dispatch. Their existing tool/permission contracts stay
in force. If owned cleanup cannot be proven, the job remains live; a cleanup
timeout is not used as permission to hand off a writable workspace.

## Executed checks

Compiler: `D:/Sengoo/target/bounded-request-build/debug/sgc.exe`, SHA-256
`cf52f7a8ea6bdad280844a327beb9452980ee2f723324a3dd6155626f08f093b`.
All binaries are private artifacts in
`windows/sencode-cli/target/workbench-scheduling/` and use source-development
runtime mode. They are not installed/release-qualified artifacts.

| Check | Evidence |
|---|---|
| Scheduler state and resource accounting | `tests-scheduler.exe`: acceptance passed |
| Validated batch, duplicate IDs, read/write barriers, dependencies and cancellation | `tests-tool-schedule.exe`: acceptance passed |
| Real concurrent process reads, both output pipes, grandchild cancellation, FIFO handoff, zero native process handles/resources afterward | `tests-tool-schedule-process.exe`: acceptance passed |
| Existing synchronous executor compatibility | `tests-executor.exe`: exit 0, output/exit-code assertions and zero native process resources |
| New polling job facade: two large pipes, root-exit/live-grandchild distinction, cancel, timeout and no native process leaks | `tests-executor-jobs.exe`: acceptance passed; `test-executor-jobs.log` |
| Actual controller integration with private SQLite/Git workspace: concurrent Git jobs, durable outcomes, ordered history, write/read barrier, replay protection, duplicate rejection and hook fallback | `tests-controller-tool-batch.exe`: acceptance passed; `test-controller-tool-batch.log` |
| Existing child-engine regression with synthetic loopback fragmented streams: four global/two per-connection, capability narrowing, FIFO writes, cancellation, shared budgets, no stream handles/workers left | `tests-children.exe` + `tests/children_fixture.py`: asynchronous children acceptance and real asynchronous child fixture passed; `test-children.log` |

Exact source/binary hashes and the compiler's recorded build input fingerprints
are in `tool-scheduling-identities.json`. Controller fixtures run against
`target/workbench-scheduling/batch-fixture/shared.sqlite3`, never a user's store.
No Linux/macOS, service-call or clean-install claim follows from this evidence.
