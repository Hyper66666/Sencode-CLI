# Workbench candidate verification

This document records the final local Windows candidate for the workbench
refinements. It is a source-development candidate, not a public release
claim. The candidate was built from the frozen Sencode checkout at
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a` with Sengoo
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a` and compiler
`cf52f7a8ea6bdad280844a327beb9452980ee2f723324a3dd6155626f08f093b`.

The executable is `target/workbench/sencode-sg.exe` with SHA-256
`9c7e5db964d859ffb9dd92dc7e026a2cf0cc42c0a997f5a33ab03221d4e60a99`.
It was built with the source-development runtime, so the artifact remains
marked `release_eligible=false` until the release toolchain is used.

## Evidence

- `target/workbench/public-final-evidence.json` — CLI, management and
  project-local history acceptance.
- `target/workbench/fullscreen-final.json` — 16 real-console checks,
  including Chinese/emoji input, model and effort selection, streaming,
  approvals, numbered diffs, recovery, and terminal restoration.
- `target/workbench/ui-native-final-evidence.json` — native Markdown, input,
  diff and workspace checks.
- `target/context-refinement/evidence.json` — context compaction and request
  recovery evidence.
- `target/context-refinement/request-recovery-final.log` and
  `target/context-refinement/engine-final.log` — restart, cancellation,
  budget and replay fixtures.
- `openspec/changes/add-cli-workbench-refinements/tool-scheduling-evidence.md`
  — read batching, write barriers, durable ledger and quiescent cancellation.

The production fullscreen measurement used four loopback SSE streams and 40
input samples. Input-to-visible p95 was **47.802 ms**, below the 50 ms gate;
the maximum sample was 50.896 ms. This is a local Windows console measurement
and does not claim latency for remote providers or other terminal hosts.

The compact-session CLI fixture now records the intended short-history quality
rejection: when there is no safe tail capable of meeting the 20% reduction
postcondition, `/compact` leaves the paused Goal and cumulative request budget
unchanged. Successful compaction, summary quality rejection and restart
recovery are covered by the dedicated context-refinement fixtures.

The candidate passed the external CLI flow, management side-effect checks,
project-root rename and `-c`/`-r` history recovery.

The packaged directory is
`target/packages-workbench-20261105-final/sencode-cli-0.1.0-dev.0-windows-x64`
and its archive SHA-256 is
`e74308d063d185c5e763f9660b39424264bd48e809ca6582cf0285275d021f26`.
`target/workbench/install-smoke-final.json` verifies both aliases in an
isolated profile and a PATH containing only `%SystemRoot%\\System32`. The
candidate was then installed to `D:\SencodeCLI`; PowerShell resolves both
`sen` and `sencode` to the installed aliases, and each reports
`0.1.0-dev.0`. The installed command help retains `resume`, `-c` and `-r`.

The source tree was dirty during this internal candidate build. No commit or
push was made, and no user project, credential, or real provider endpoint was
used by the fixtures.
