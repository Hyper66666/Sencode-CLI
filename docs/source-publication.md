# Standalone source publication

This repository snapshots the current `windows/sencode-cli` and
`windows/sencode-config` working trees from the Sencode monorepo. The monorepo
baseline was `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`; most CLI work was
uncommitted there. This is a source snapshot, not an extraction of prior Git
commit history. Existing verification documents retain their original paths
and hashes as historical evidence.

Required Sengoo source revision:
`86c6f87975646b91c9cf2d7d069ac06ee4243b9b`.

The standalone adaptation changes repository-relative build, package, test and
runtime-pin paths, regenerates `Sengoo.lock` with sgpm, and adds repository
instructions and artifact exclusions. Agent and TUI `.sg` sources are preserved.
The adjacent `../Sengoo` path dependency is intentional. A custom `SengooRoot`
script argument alone does not relocate this manifest dependency. Two source
files also have their final blank line normalized; their behavior is unchanged.

CLI-related desktop changes are preserved in
`integrations/desktop/shared-state.patch`. The patch was reverse-checked against
the original working tree. Native API CLI operation does not require Tauri or
the desktop source. Managed account engines require separately prepared pinned
runtimes and their own capability qualification.

Publication checks on Windows x64: 24 strict CLI OpenSpec validations, 4
configuration profile tests, and Unicode table integrity plus 1,155 compiler
library tests in the matching Sengoo checkout.

The standalone test runner also passed `session_policy_wait` (27 checks) and
`engine_host` against the existing installed candidate, SHA-256
`23e8635ba2b25b9f16f63db723c51056b09f178b4ba274d50c33b4c631c98d4c`,
with compiler SHA-256
`cf52f7a8ea6bdad280844a327beb9452980ee2f723324a3dd6155626f08f093b`.
These loopback/console fixtures cover remembered permissions, startup races,
child capacity waits, grouped speaker headings, streaming, execution policy,
cancel, restart and durable replay refusal. The CLI source revision tested was
`2ce7ac42ff9a5264bdab1e5b2a10d1ed7049779a`. This reused the previously built
candidate; it was not a fresh standalone build. Machine-specific runner evidence
is retained locally at `target/source-publication-acceptance.json`.
Fixture, live provider and clean installation evidence remain distinct; this
publication does not establish fresh cross-platform or live-service coverage.

Generated binaries, developer caches, credentials, project histories and
reference source trees are excluded. Runtime pins and source tests are included.

## Commit identity correction

The publication commits were recreated with the repository owner as author
and committer. Sengoo source trees are byte-identical; CLI changes are limited
to documentation revision links and this provenance note. Recorded historical
verification SHAs above identify the commits actually tested before correction.

- Sengoo baseline `d46b3f6cd8d6e770734f98edc57aa67cb931e26a` maps to `08e4a3616127b4c5d1ae8a20a8f830127a9f54a4`.
- Sengoo candidate `e25a23e8eb7431afce022be426ecb523bfec16cf` maps to `86c6f87975646b91c9cf2d7d069ac06ee4243b9b`.
- CLI source snapshot `2ce7ac42ff9a5264bdab1e5b2a10d1ed7049779a` maps to `26ca67daa77899c1ad36268991b35b12dc8d43a1`.
