# Shared SDK integration evidence

Final Windows development candidate: `target/agent-sdk-20261109/candidate-6`.
Compiler SHA256 is
`9b1055c5a5cb7f09c016228a44f7427b7519b6a92e69cad5993004831c3aa1e5`;
the installed/tested executable is
`0288b51b0626aca61b7d2e4b50ad08b767278eae55b6d62270a0764eb35ce7c2`.
Build inputs remained unchanged. Nine native suites and eleven product suites
pass with this compiler/binary, including full engine-host recovery, five retries,
live steering, cancellation, Goal, Responses and 25 fullscreen console checks.
The unchanged original TUI native suite also passes five repeated runs after
the compiler repaired borrowed temporary owners crossing a branch join.

`final-gates.json` pins those reports, the twelve SDK/consumer/benchmark reports,
package archive and source hashes. `install-smoke.json` passes isolated upgrade,
rollback, stale-PATH entrypoints and Unicode argv. `local-install-evidence.json`
confirms the tested binary installed into `D:/SencodeCLI`, all fifteen payload
files and six entrypoints verified, rollback retained and PATH unchanged.
Shared Provider/MCP plus policy, scheduler, tool contracts, questions and retry
adapters all consume the common Sengoo packages. No live paid provider,
fresh-VM or other-platform qualification is implied.

The earlier candidate-4 evidence below retains its original identities and is
superseded for current installation by candidate-6. Candidate-5 was withheld
after expanded native TUI regression revealed the conditional-lifetime bug.

Host DESKTOP-FUAQMFB, Windows x64, 2026-11-09. CLI baseline
c603b84022bb3afeec4f3fb217dd016abd48f028, Sengoo baseline
ea803f1913f9d08f6393d412b0eb4b1de3055b3e plus the SDK/language changes.

The CLI protocol modules now import sgllm. MCP is a host-policy adapter around
sgmcp's client. Manifests/lockfiles include sgllm, sgmcp and transitive sgschema;
test source guards cover the SDK source graph in addition to CLI/stdlib files.

## Candidate identity

Candidate-4: `target/agent-sdk-20261109/candidate-4/sencode-sg.exe`, SHA256
416bacd3b2a2c5c400053b75255b4e0da0b040cc8b3161db375d10e34077c875.
`build-result.json` confirms all pinned compiler/runtime/CLI/SDK inputs unchanged.
Compiler source rebuilt after Rust formatting, SHA256
6b40efa12c374adbc48dd7f543ddc83820e00140fa87689b3cb3a35479039c7a.
Earlier candidates 1–3 were deliberately rejected by source guards as fixes
landed; their preflight runs are not final release proof.

## Executed checks

- `target/agent-sdk-20261109/native-evidence.json`: five native/fixture suites
  pass: protocol/SSE, HTTP, stdio MCP, controller recovery and context compaction.
- The full engine-host test, previously failing after Goal → ordinary followup,
  passes on the frozen candidate in the current integration run. It also passed
  a separately identified preflight. Do not infer the old error's exact internal
  cause merely from the newly passing result.
- Dedicated SDK tests record three protocol/network failures, 160 MCP progress
  events with bounded notifications, cancellation, timeout, process cleanup,
  NUL control rejection, opaque NUL identity/payload preservation and resource
  counters. Source identities are in each package EVIDENCE.md.
- Sengoo `target/agent-preview-locked-consumer.json`: exact-version offline
  registry resolve/check/build outside both checkouts, then copied native image
  runs after the entire source/registry directory is removed and PATH is reduced
  to System32. This is independent consumption, not a CLI-relative import.
- `candidate-4/install-smoke.json`: isolated alias install/upgrade/rollback,
  Unicode paths, no-argument startup, empty resume rejection and PATH preservation.
- Strict OpenSpec validation: 38 CLI / 86 Sengoo items at this checkpoint.

`target/agent-sdk-20261109/production-evidence.json` finishes with all eleven
suites passed against candidate-4, including full engine-host, steering,
network/context recovery, cancel/resume, tools, Goal, evidence, permissions and
25 fullscreen checks. `candidate-4/final-gates.json` checks original source
identities, package and smoke evidence. This successful subset does not include
the later newly failing owning-string/legacy-buffer resource regressions.
No installed-user program change is claimed from the isolated install smoke;
the prior installed program remains while these additional fixes are validated.

Informational startup measurement: 30 fresh `--version` processes with a warm
OS filesystem cache give p50 30.8649 ms, p95 34.8254 ms and maximum peak working
set 8,036,352 bytes. The forced O2 build runs 10:53:40–10:58:27 UTC with existing
frontend/runtime caches. `target/agent-sdk-20261109/performance-baseline.json`
records the workload; neither result claims interactive startup or cold build.

## Remaining boundaries

An additional schema enum repeated-resource test revealed an owned String.eq
argument cleanup issue; an sgagent resume test revealed a discarded String
producer path. Those are being reduced independently. They are not hidden by
raising runtime limits or declaring every ownership composition supported.
Candidate-4's executed gates only establish the listed scenarios. A subsequent
candidate is required if a shared SDK/compiler fix changes its pinned inputs.

The old nested explicit-field destructor marker831 and Option<JsonDoc>? typing
limit are separately retained. Generic pollable server stdout, full sgagent
embedding/SQLite host integration, realworld projects, live providers and other
platforms remain program tasks. No all-repository/fresh-VM qualification is claimed.
