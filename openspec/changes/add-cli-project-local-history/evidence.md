# Project-local history evidence

Baselines (both dirty): Sencode
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a`, Sengoo
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`. Host:
`DESKTOP-FUAQMFB`, Windows x64, 2026-11-04.

## Frozen native checks

`sencode-cli/target/acceptance-project-history-native-frozen2.json` passed using
compiler SHA256 `cf52f7a8ea6bdad280844a327beb9452980ee2f723324a3dd6155626f08f093b`.
The pre-integration independently built private probe also passed all 60 checks:
`target/worktree-tui/project-history-evidence.json` and
`project-history-build-evidence.json`.

| Input | SHA256 |
| --- | --- |
| `src/project_history.sg` | `7c557471d6d0f22b4bc8c720ee5f619744bc9c80722122ae0cb555682d153fa9` |
| `src/project_history_probe.sg` | `36fba919cb845a84dc2a8c19cad3a4dbefd364e31527391a0421f46f00c1fe5e` |
| `tests/project_history_fixture.py` | `d323714c6a7f569d18d6982aa37e7436c1910bcc42cf6977c8531d9760886975` |

Coverage includes legacy capture, Unicode root rename, stable identities,
scoped live writes, rollback, cross-project moves/deletes, missing/newer row
preservation, explicit sanitized import, paused Goal budgets, active/unknown
execution refusal, malformed schema/data, duplicate and escaped JSON role
fields, and append-only private ignore patterns. Fixtures use only owned
temporary databases/directories. No user catalog or live account was touched.

The first full-main candidate exposed the generated local `.gitignore` itself
as an untracked Git path. The final source adds `/.gitignore` to its own private
patterns, with a dedicated native assertion. The final 60-check native suite
and real-main worktree console preserve Git status/index. The earlier failed
product report remains in `target/acceptance-project-history-product-frozen.json`;
it is not counted as passing final acceptance.

## Specification validation

`openspec validate add-cli-project-local-history --strict` passed.
The all-change run reports 28 passes and 3 existing unrelated failures:
`add-fusion-selection`, `add-git-workspace-management`, and
`add-grok-desktop-backend`. Full output is preserved in
`sencode-cli/target/project-history-candidate/openspec-all.log`.

## Combined and installed acceptance

Final application SHA256:
`5d0cbfca542738bb1b68a4f24c247b63b5a589190fcd53b95758c309ed31260c`.
Package archive SHA256:
`5508c48c963efe523bd9449b08576e9b9ae8c73a56d06528e17a683964bc12e1`.
Package: `target/packages-project-history-candidate2-20261104/`.

- `target/acceptance-project-history-product-frozen2.json`: all 10 product
  groups passed against that application. Includes public resume/import,
  management, external coding/Plan/Goal, streaming execution, request recovery,
  14 fullscreen console checks, background Agent, worktree CLI and console,
  and 14 terminal-pane console checks. Four simultaneous SSE streams retain
  input-visible p95 below 50 ms on this host.
- `target/acceptance-project-history-managed-frozen.json`: both managed engine
  adapters passed using local protocol fixture executables, without account login.
- `target/acceptance-project-history-installed-frozen.json`: installed public
  management and project-history flows passed.
- `target/project-history-candidate2/install-smoke.json`: payload checksums,
  aliases, isolated/no-tool PATH, Unicode, resume, tamper rejection and locked
  alias rollback passed.
- `target/project-history-candidate2/installed-bare-streaming-history2.json`:
  isolated installed CMD `sen`/`sencode`, real loopback streaming, immediate local
  messages/history/usage, root rename, `-c`, `resume ID` and `-r ID` passed.
- `target/project-history-candidate2/user-bare-streaming-history.json`: the same
  10 checks passed through the existing WindowsApps forwarders after updating
  the owned `D:/SencodeCLI` and `%LOCALAPPDATA%/SencodeCLI` installations.
  No real user database, connection configuration or account was changed.

The streaming helper and its SHA256 are recorded in each report:
`target/project-history-candidate/verify_streaming_history.py`. All service
requests in this evidence use owned loopback fixtures and random temporary
credential entries, which are removed afterward.

## Remaining gates

Continuous desktop-only local mirroring,
power-loss atomicity across attached WAL databases, fresh Windows VM, live
authenticated services and independent trials are not qualified by the native
fixtures.
