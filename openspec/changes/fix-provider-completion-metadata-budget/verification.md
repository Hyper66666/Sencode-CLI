# Windows x64 verification, 2026-11-07

Host: `DESKTOP-FUAQMFB`. Baseline SHAs, existing changes preserved:

- CLI: `b2b85ef2c8f369f2fd69ef8729ab420cc420959a`.
- Sengoo: `86c6f87975646b91c9cf2d7d069ac06ee4243b9b`.
- Compiler SHA256: `6507e0e2eff15fd375054334f4e4ff6bccf540431f5f81bd56625f7f0d616252`.

## Reproduction and diagnosis

Read-only historical attempt evidence showed six HTTP 200 responses failing in
`provider_event`; the original event bytes were not retained, so the historical
coarse message alone cannot identify a field or establish all past failures.
A new live request to the same model/connection with accepted history reproduced
the problem: a 4129-node, 96136-byte terminal event failed under the old parser.
Removing only optional `usage.attribution` made the old parser succeed. A
second live comparison on the final candidate returned 4135 nodes / 96262 bytes:
the old parser failed with 10, repaired parser passed, and the final CLI made
one request without a protocol retry. The isolated CLI then correctly stopped
at command permission. No returned command was authorized or executed. This is
live parser evidence, not a claimed completed live coding task.

Raw response text, credentials and hidden reasoning were processed only in
memory; saved evidence contains closed diagnostics, lengths and structural
metadata. Source user history/configuration were opened read-only and unmodified.
Evidence: `target/provider-event-20261107/live-comparison-summary.json`,
`legacy-rich-completion-evidence.json` and `independent-json-evidence.json`.

## Executable acceptance

The source-development candidate is
`target/provider-event-20261107/candidate/sencode-sg.exe`, SHA256:
`a83be9e85899c447b4c8609b3504edcc4584e26f925425f561800aaf25a64214`.
Input hashes and compiler identity were frozen and verified across build/test.

- Four native suites / eight steps passed: protocol, transport, request_retry,
  execution_diagnostics, including fragmented three-protocol streams, node-rich
  completion, invalid JSON, explicit limit exhaustion and transient cleanup.
- Five final-executable suites passed: responses_tools, request_recovery_host,
  cancel_resume_host, agent_reliability, fullscreen. Rich metadata produced no
  additional requests across tool continuation and restart. Three tools executed
  exactly once, malformed items never authorized writes, all-error five retries
  and compaction/budget persistence remained intact.
- All 24 three-protocol cancel/recovery checks and 25 real Windows terminal
  checks passed. Four active streams yielded input p95 42.6493 ms / 40 samples.
- The adjacent independent Sengoo native regression passed twenty JSON
  round trips with legacy compatibility, explicit overflow, malformed input
  and exact document/reservation cleanup. No compiler/runtime change was needed.

Evidence: `target/provider-event-20261107/native-evidence.json`,
`production-evidence.json`, and
`target/acceptance/20261107-235114-146-ced75e14/`.

## Distribution and local installation

Archive: `target/packages-provider-event-20261107-v1/sencode-cli-0.1.0-dev.0-windows-x64.zip`.
SHA256: `29afbc7b07686edc89a655a616003c45f8f987cb1037f9e4f0f6db40552cae40`.
Isolated installation smoke passed clean PATH, both aliases, Unicode paths,
source/tool-free PATH, ripgrep integrity and locked-alias rollback. Final gates
also require the live parser comparison and independent JSON regression.

Installed to `D:/SencodeCLI`, verified all 15 payload files and six direct,
bare-command and forwarder entrypoints against the same candidate. PATH stayed
unchanged, no pre-existing user process was stopped, and the previous
response-retry package was checksum-verified for rollback. Evidence:
`candidate/install-smoke.json`, `final-gates.json`,
`local-install-evidence.json`. Running old sessions retain their original image;
new launches use the repaired executable. This is an internal development
candidate, not fresh-VM qualification or a published release.

## Reference comparison

The supplied Claude Code 2.1.88 SDK stream uses `JSON.parse(sse.data)` with no
application node-count ceiling on this path. The supplied Grok Build
`SOURCE_REV` 559751fdcec02d413e4c57c8832ab275e4f44980 uses
`serde_json::from_str`; no node-count ceiling is configured, while its pinned
serde_json 1.0.149 defaults to 128 recursion levels. These are response-path
findings, not claims of unlimited process memory. Sencode's explicit event
admission is 1 MiB / 65536 nodes / depth 64, separate from the unchanged legacy
JSON defaults. OpenSpec strict validation passed: CLI 32 items, Sengoo 74.
