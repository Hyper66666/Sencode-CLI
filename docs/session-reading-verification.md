# Session and reading candidate, 2026-11-05

The Windows x64 optimized internal candidate is installed as `sen` and `sencode`
in `D:/SencodeCLI/bin`, with the existing WindowsApps forwarders updated.
Its SHA256 is
`2934bc150d70f964693701e085343f72324794e42d2e6bdf72011ef56566236f`.
`target/session-reading-20261105/final/summary.json` records full repository
baseline SHAs, compiler identity, 284 unchanged production inputs and hashed
evidence reports. The worktrees retain their existing uncommitted changes.

The final executable passed session entrypoints (14), project history (6), reading
console (14), full terminal interaction (24), model/permission controls (16),
agent reliability (7) and long-history recovery (12). Six UI native suites,
provider activity and fenced turn-metric suites passed. Provider, executor and
diagnostic native regressions also passed. Desktop session projection was checked
with unit tests; a packaged desktop handoff was not exercised.

Responses task continuation passed 11 public-host checks, and existing tool
continuation passed 8. These include phased intermediate answers without fake
user messages, persistence, shared request budgets, child continuation,
cancellation, command-error recovery and complete keep-alive response framing.
Five public-host suites cover those two protocols, host execution, request
recovery and managed adapters. Services and account runtimes were synthetic
fixtures; no paid API or real account credential was used.

Actual owned hidden Windows consoles verified 80, 120 and 160 columns. With four
concurrent loopback SSE streams, 40 input samples had p95 42.05 ms; the separate
stream-render measurement had p95 78 ms. These figures describe this host and
test conditions. The diff console preview reconstructs captured console cells
and attributes rather than a mock interface.

The package includes the required native redistributable and pinned managed
runtime components. Isolated installation exercised an executable-only folder,
PATH without development tools, bare aliases with stale PATH, Unicode argument
forwarding, rejected foreign/tampered aliases and a locked-file rollback. A
separate isolated test installed the previous candidate, upgraded and rolled back
to the previous hash. Empty conversations intentionally cannot be resumed;
positive history recovery is verified separately through the public application.

The affected OpenSpec change passes strict validation and Sengoo has 69/69 items
passing. Global Sencode validation has 36 passing and three existing unrelated
failures: `add-fusion-selection`, `add-git-workspace-management` and
`add-grok-desktop-backend`. Reports preserve those failures.

Remaining qualification: live service calls, real managed account use, fresh
Windows VM, other platforms and packaged desktop handoff. The exact historical
screenshot interruption has not been identified; reproduced output-decoding loss
and the classified failure paths were repaired without asserting that they were
the sole cause. Unknown legacy child ownership is preserved. A full-module
compiler forward-order issue has an isolated A/B record and a source-ordering
workaround; the compiler itself was not changed for that issue.
