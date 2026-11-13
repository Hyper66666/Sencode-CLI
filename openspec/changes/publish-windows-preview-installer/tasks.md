# Implementation and publication

- [x] Verify the frozen candidate ZIP, payloads and source identities (15 payloads; both 274-source reports match).
- [x] Add the pinned download/offline installer and public install instructions.
- [x] Verify PowerShell 5.1 install, Unicode prefix, offline input preservation and bad-hash rejection (`target/release-20261113/bootstrap-tests.json`, Windows x64).
- [x] Rerun the package install/upgrade/rollback smoke against the unchanged archive (`target/release-20261113/install-smoke-ps7.json`, Windows x64).
- [x] Pass affected and all strict OpenSpec validation (39/39).
- [x] Publish assets, checksums and provenance to `v0.1.0-preview.20261113` (GitHub release 443922314); unauthenticated asset downloads and the downloaded bootstrap's full online installation passed under PowerShell 5.1 (`target/release-20261113/public-install-evidence.json`).
