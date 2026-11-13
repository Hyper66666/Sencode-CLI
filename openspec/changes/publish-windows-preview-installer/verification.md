# Published Windows preview

- Release: https://github.com/Hyper66666/Sencode-CLI/releases/tag/v0.1.0-preview.20261113
- GitHub release ID: `443922314`; published prerelease, five uploaded assets.
- Tag/source checkpoint: `667452acabaef9a97bd79bb9b7fee4052a2704ab`.
- SDK integration checkpoint: `6495536` (included in the release checkpoint).
- Host: Windows x64, DESKTOP-FUAQMFB, 2026-11-13 Asia/Shanghai.
- Final online installation completed at `2026-11-13T07:17:47.105170+00:00`.

Published assets: the original 166,459,760-byte ZIP, its `.sha256`,
`install-sencode.ps1`, `SHA256SUMS` and `release-evidence.json`. GitHub's upload
digests matched every local asset. The ZIP SHA-256 remains
`19439583db8395e108d5301954d7fc17d02cc2d9d530dbc02c662eb93e920b8a`.
Bootstrap SHA-256:
`6cbf9be89962e526cab871cfda9b1285f67bc12cda2821d9c4463f6def8871ea`.

All 274 source records in each historical native/product report were rehashed
unchanged. The original candidate's nine native and eleven product suites remain
historical evidence for those same bytes, not a newly rebuilt application.

Current checks:

- PowerShell 5.1: fresh Unicode-prefix offline install, owned update, original
  archive preservation and bad-hash rejection before installation all passed.
- PowerShell 7: full existing package installation/upgrade/rollback smoke passed,
  including stale-PATH commands, locked alias rollback and unchanged user PATH.
- All 39 strict OpenSpec items passed.
- Public installer, checksums and release evidence downloaded without GitHub
  credentials and matched local bytes. The public ZIP returned HTTP 200 with
  the expected content length.
- The downloaded bootstrap then downloaded the ZIP from the public release,
  verified its embedded hash and installed to a new Unicode prefix using Windows
  PowerShell 5.1. Both installed aliases returned the expected version and exact
  application hash `0288b51b0626aca61b7d2e4b50ad08b767278eae55b6d62270a0764eb35ce7c2`.

Local terminal reports are under `target/release-20261113/`: `bootstrap-tests.json`,
`install-smoke-ps7.json`, `public-install-evidence.json` and the published asset
copies. The full legacy smoke's PowerShell 5.1 invocation exited -1 without a
terminal report; it is not counted as passing. Separate PowerShell 5.1 bootstrap
installation and update checks, and the full PowerShell 7 smoke, passed.

The unauthenticated GitHub API hit the shared network's rate limit; publication
metadata uses the authenticated publish receipt. The actual public asset and
bootstrap download tests used no credentials. This does not establish fresh-VM,
other-platform, signed-binary or paid-live-provider qualification.
