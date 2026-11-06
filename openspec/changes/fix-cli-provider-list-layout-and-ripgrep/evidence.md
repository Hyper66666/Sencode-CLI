# Windows candidate evidence

Host: `DESKTOP-FUAQMFB`, Windows x64, 2026-11-05.

Source baselines (existing local changes preserved):

- Sencode: `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`
- Sengoo: `d46b3f6cd8d6e770734f98edc57aa67cb931e26a`
- Compiler SHA256: `cf52f7a8ea6bdad280844a327beb9452980ee2f723324a3dd6155626f08f093b`

The final optimized candidate is
`sencode-cli/target/provider-layout-search-20261105/candidate-3/`.
Its `build-inputs.json` records each compiled source and tool identity.
`build-result.json` confirms inputs did not change during compilation; they were
checked again after local installation. This is an unsigned development build
using the source-development runtime, not a public release qualification.

- Application SHA256, both aliases:
  `cfd9df0ce8a9af1ca66936a0abaf0843c8e2f28fb8bb8c1566911bcdbc9862d2`
- Package ZIP SHA256:
  `cab3659d705a09f1ef9ce6a5fb77b446f54bd2be53dbf2fa0368bff733290aec`
- Package: `target/packages-provider-layout-search-final-20261105/sencode-cli-0.1.0-dev.0-windows-x64.zip`
- Ripgrep 14.1.1 binary SHA256:
  `f162b54de2adfc72d78adb1dbada2dedda111ae0a5e2f6e9500f4f909664c5d2`

Passed checks:

| Layer | Receipt | Result |
| --- | --- | --- |
| Native Sengoo | `../native/evidence.json` | 6 suites: TUI, permission modes, executor, model selection, diagnostics, reading experience |
| Public model catalog | `models-public.json` | 9 checks, including all suppliers, 37 models, duplicate ids, Unicode, legacy fallback and refresh |
| Real Windows console | `workbench-controls.json` | 19 checks, including light blue manual, yellow auto, red full, current/next spans and request immutability |
| Real full-screen CLI | `fullscreen-console.json` | 25 checks, including top origin, grouped suppliers, refresh, duplicate-model routing, streaming, cancellation and image input |
| Reading and diff | `reading-console.json` | 14 checks at 80/120/160 columns |
| Tool loop and resume | `agent-reliability.json` | 7 checks, including a real read/patch/Bash-test workflow and completed-call dedup |
| Installed search | `search-tool.json` | 8 checks with System32-only inherited PATH, Bash/PowerShell, Unicode and no-match results |
| Installation | `installation-smoke.json` | Both aliases, stale PATH forwarders, executable-only startup, upstream search pin, corrupt payload rejection and locked-file rollback |
| Upgrade/rollback | `rollback-evidence.json` | Previous → candidate → previous, both aliases and native forwarders |
| Local installation | `local-install-evidence.json`, `local-installed-search.json` | Updated `D:/SencodeCLI`, verified bare commands/WindowsApps forwarders and reran 8 installed search checks |

The four-stream input workload measured 40 samples, p95 `40.8402 ms`, maximum
`47.8891 ms`. This measures this host's owned native console and loopback streams.
Captured console-cell previews are `conversation-preview.png`, `models-preview.png`
and `permissions-preview.png`; these are evidence renderings, not design mockups.

The affected OpenSpec change validates strictly. Whole-repository validation has
37 passes and the same 3 pre-existing failures: `add-fusion-selection`,
`add-git-workspace-management`, `add-grok-desktop-backend`.

Tests use disposable SQLite stores, temporary fixture credentials and loopback
providers. No real paid API call, fresh Windows VM, other platform or published
release is claimed. Existing CMD command-line quoting is outside this search
qualification; the supported and tested tool paths here are default Bash and
explicit PowerShell. Ordinary nonzero exits continue back to the model. No new
native application logic was added; UI, catalog and child-environment changes
are Sengoo and use its existing process, filesystem and executable-path APIs.
