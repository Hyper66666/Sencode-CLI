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
script argument alone does not relocate this manifest dependency.

CLI-related desktop changes are preserved in
`integrations/desktop/shared-state.patch`. The patch was reverse-checked against
the original working tree. Native API CLI operation does not require Tauri or
the desktop source. Managed account engines require separately prepared pinned
runtimes and their own capability qualification.

Publication checks on Windows x64: 24 strict CLI OpenSpec validations, 4
configuration profile tests, and Unicode table integrity plus 1,155 compiler
library tests in the matching Sengoo checkout. Additional CLI smoke results
are recorded by the source-publication acceptance invocation under `target/`.
Fixture, live provider and clean installation evidence remain distinct; this
publication does not establish fresh cross-platform or live-service coverage.

Generated binaries, developer caches, credentials, project histories and
reference source trees are excluded. Runtime pins and source tests are included.
