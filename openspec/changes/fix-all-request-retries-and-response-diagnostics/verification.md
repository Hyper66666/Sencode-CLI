# Candidate verification, Windows x64, 2026-11-07

Baseline revisions (existing local work preserved):

- CLI: `b2b85ef2c8f369f2fd69ef8729ab420cc420959a`.
- Sengoo: `86c6f87975646b91c9cf2d7d069ac06ee4243b9b`.

The source-development candidate is `target/response-retry-20261107/candidate-4`.
Its input inventory records source hashes, toolchain hashes and the dirty
baseline. Compiler SHA256:
`6507e0e2eff15fd375054334f4e4ff6bccf540431f5f81bd56625f7f0d616252`.
Executable SHA256:
`312a3e5219c1732d39a33273d9ac2f8fd8d07e212e683201771194abe04c2a83`.

## Native and protocol acceptance

The final compiler passed all 13 selected suites (26 build/run steps) in
`target/response-retry-20261107/native-evidence.json`: executor, state,
request_state, tui_timeline, tui_agents, transport, children, consult,
execution_diagnostics, request_retry, protocol, http and workspace. They include
real local provider streams and process execution, not external API calls.

Adjacent Sengoo verification includes the Windows process/terminal C probe,
14 question-mark compiler tests, 68 Drop-related compiler tests and native
Result/Option JSON document liveness. The ownership sweep separately found
15 passes and one pre-existing explicit field-destructor failure, reproduced
with the old compiler. See the adjacent
`fix-named-try-owned-transfer/verification.md`; this failure is not counted as
a passing language-wide gate.

## Exact executable and installation

The same executable passed all 9 production suites in
`target/response-retry-20261107/production-evidence.json`: request_recovery_host,
cancel_resume_host, responses_tools, engine_host, plan_turn_host,
goal_acceptance_host, model_routing_host, agent_reliability and fullscreen.
The retry host verifies six total attempts for HTTP 400/429/502, post-send
disconnect, partial HTTP 200, malformed SSE/JSON, missing completion, stream
error, connection failure and TLS abort. Two provisional failures followed by
success leave one canonical answer; a preceding side-effect command runs once.
The three-protocol cancellation/recovery fixture passes all 24 checks.

The real Windows console passed 25 checks; four concurrent SSE requests produced
input latency p95 38.8139 ms across 40 samples. The streaming-render fixture's
separate p95 visible-update lag was 78 ms (40 ms provider intervals). These are
local measurements, not remote-provider latency promises.

Isolation install smoke passed for both aliases, Unicode paths, source/tool-free
PATH, locked-alias rollback and ripgrep integrity. Final hash gates passed, then
the existing installer updated `D:/SencodeCLI` and verified all 15 payload files
and 6 direct/bare/forwarder entrypoints. PATH stayed unchanged; no user process
was stopped. Local evidence is in
`target/response-retry-20261107/candidate-4/local-install-evidence.json` and
`final-gates.json`. Two in-use previous-image files remain deferred to the
installer's normal cleanup policy. The previous network/context package is
checksum-verified for rollback. This host has development tools; these checks
do not claim fresh-VM qualification or live-provider availability.

Strict OpenSpec validation passed: 31 CLI items and 73 Sengoo items.

The prepared archive is
`target/packages-response-retry-20261107-v1/sencode-cli-0.1.0-dev.0-windows-x64.zip`,
SHA256 `fbeca11533b190e4bcf43f89f468523bf451d6e283dece571ba70b47f1dc9bfb`.

## Diagnostic conclusions and compatibility

The screenshot's HTTP 200 obscured error 10 in the old diagnostic. That record
does not identify the original provider parsing/transport failure. New closed
stage/category fields make future failures distinguishable without storing
raw error bodies, URLs or credentials. Ordinary shell exit codes remain tool
results for model correction. Model retries do not rerun those tools.

An exact executable retry test independently exposed named Result payload
cleanup in the compiler. A standalone reproducer failed before the compiler fix
and passed afterwards; the candidate uses the fixed compiler. Windows executable
path and cmd command-tail quotation fixes also live in Sengoo, without ABI
changes. CLI protocol/state additions are additive; no user project, credential
or Git identity was modified during diagnosis.
