# Native hook worker evidence — Windows, 2026-11-04

Host: `DESKTOP-FUAQMFB`, Windows `10.0.26300`, x64. Sencode base HEAD
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a`; Sengoo base HEAD
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`. Both repositories have existing
working changes. Exact owned-source hashes, binary hashes and compiler build
cache provenance are in [source-identities.json](source-identities.json).
These are private isolated fixture artifacts, not a published candidate SHA.

Compiler: `D:/Sengoo/target/bounded-request-build/debug/sgc.exe`, SHA256
`cf52f7a8ea6bdad280844a327beb9452980ee2f723324a3dd6155626f08f093b`.
Builds use `--runtime-mode source-development`, `-O 0`, LLVM/clang 19.1.7 and
the existing `sgsqlite` module map. Provenance explicitly reports
`release_eligible=false`; no release toolchain or installed acceptance is
inferred. The exact runtime build fingerprints are recorded per probe in the
identity JSON. Concurrent sibling work is not asserted to equal every imported
dependency in these probe snapshots.

## Executed checks

All commands below ran from `windows/sencode-cli`. Fixture files, databases and
sentinels were under unique local temporary directories. No real provider,
credential, user worker registry or installed CLI was used. Successful fixture
cleanup inventories and removes individual files, then empty directories.
Failed investigations retain only their owned fixture directory.

| Check | Actual observation |
| --- | --- |
| `target/hooks/tests-hooks-final.exe --database TEMP/shared.sqlite3` | Unicode frames, same-object escaped duplicate keys, nested independent keys, explicit tool subset, deterministic invocation IDs, registry has no execution authority, canonical cwd FIFO. A fenced cleanup marker still prevents takeover after normal turn release. |
| `target/hooks/tests-approval-nonce.exe` | Actual generated opaque nonces, guessed old IDs, wrong request IDs, stale replies and same-request restart replay rejection. |
| `python tests/hook_fixture.py target/hooks/hook-probe.exe target/hooks/hook-worker-fixture.exe` | continue/block; Chinese/emoji byte fragments; explicit unsupported host calls; malformed, oversized, unknown, wrong-ID and duplicate frames; stderr pressure; nonzero exit after a valid result; timeout and owned grandchild termination; changed manifest/executable rejection. |
| `python tests/hook_host_fixture.py target/hooks/hook-host-probe-final.exe target/hooks/hook-probe.exe target/hooks/hook-worker-fixture.exe` | Real pipes and the real controller boundary; 15 cases listed below, plus production management helper reads/trust semantics. |
| `python tests/hook_example_fixture.py target/hooks/protected-paths-example.exe` | Compiled minimal Sengoo helper/example exchanges initialize/ready and returns continue/block correctly. |
| `openspec validate add-cli-native-hook-workers --strict` from `windows/` | Passed. |

The 15 host cases are `approve`, `refuse`, `plan`, `child`, `headless`, `block`,
`after_crash`, `trust_changed`, `cancel`, `running_cancel`, `complete`,
`running`, `hook-prior`, `hook-done`, `invalid`.

They verify fresh per-invocation approvals despite a prequeued old predictable
ID, pinned executable and ancestor replacement denial while approval waits,
revoked trust before spawn, refusal without parent admission, clean worker
cancellation, before/parent/after sequencing without nested write permits,
original outcome durability after an after-hook crash, no replay of parent or
hook admissions, unchanged Goal request/token counters, and cleanup marker
clearing only on certified completion. Management checks prove absent
list/inspect do not create a worker sidecar; registration is disabled; unattended
enable refuses; explicit trust review enables without spawning.

Named logs remain under the ignored `target/hooks/` directory:
`contracts-fixture-final.log`, `nonce-fixture.log`, `transport-fixture-final.log`,
`host-fixture-final.log`, `example-fixture.log`. All named checks exited 0.

## Artifact identities

| Private artifact | SHA256 |
| --- | --- |
| host/controller probe | `06acbebc8d76a4c54b019e62b9369b8811c053ca6e9d6942d4c1a20e984a300a` |
| management/transport probe | `4383a62f2f3c83b9df0dfe5a16c2a39710f55fcf28752eb11c31158a240b9392` |
| hostile fixture worker | `4b98f993941d4c90665016827b5f61004f9ddb8bf44a70c65d5a63776caee4fa` |
| contract/authority test | `a267c71938da8bd7b4c48c9e937a5d689380366296281fd1945ac3137778382f` |
| approval nonce test | `70baef7b0dec47f55423d15064b2aa2b47711695bd4bbf0acaa804a905617043` |
| minimal example | `f2e5c202db8fb1ba15968cc50d79516d88209458805f598206a7614db8fdaf55` |

## Open gates

The public `extensions` parser route, fullscreen/scrolling slash projections,
source-free installed CLI acceptance, and final combined candidate must be
checked separately by integration. The registry helper probe does not establish
those outcomes. No live provider, non-Windows filesystem, cleanup-failure fault
injection, abandoned-handle Drop fault injection, or concurrent multi-worker
write-overlap stress result is claimed here. The SDK remains a minimal local
helper and example; host tools/models, remote hooks and package distribution are
not implemented by this slice.

## Grok Build architecture review

Read local `grok-build/crates/codegen/xai-grok-hooks/src/runner/command.rs`,
`result.rs`, `dispatcher.rs` and `trust.rs`. Useful designs are independent
decision/run-health values, hook/source attribution, a process-group cleanup
guard with joined reaping, and one eligibility rule shared by dispatch and UI
counts. Native schema 1 keeps its approved distinct behavior: an execution
failure pauses continuation; only a pinned exact executable runs; after hooks
cannot replace the parent outcome. It does not import Grok's command-string
shell fallback, failure-open gate policy or output replacement. No recovered
Claude implementation was copied.
