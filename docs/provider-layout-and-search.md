# Provider list, conversation layout and search

Conversations start below the header. The empty home remains centered; long
conversations retain their scroll position, fixed composer and blank separator.
The permission footer uses light blue for manual approval, yellow for auto
approval and red for full access. A busy request retains its accepted permission
and model; a separately colored next-turn label shows pending permission changes.
`NO_COLOR` retains labels without semantic colors.

All suppliers saved in sencode-config appear together in `/model`, each followed
by its enabled models. Up/down crosses supplier boundaries and left/right jumps
to the adjacent supplier. Long groups scroll with their selection and keep a
supplier heading. Enter selects a model and opens thinking effort; only completing
both steps changes the next request target. Canceling leaves the target intact.
Reopen `/model` to refresh configuration saved by another client. Discovery alone
does not enable models. `sen models` adds the complete enabled-model metadata
without removing the existing connection identity, name, selected model or URL.

Windows packages include official ripgrep 14.1.1. The application resolves it
beside its own executable and adds that directory only to approved command jobs'
PATH. A fresh terminal, developer tools and a global ripgrep installation are
not needed. Source builds can use an absolute tool PATH outside the workspace.
`sen doctor` reports availability, executable and source; it does not download
anything or contact providers.

Use the default Bash for shell workflows. In explicit PowerShell, prefer
`rg -n -g "*.html" "pattern" .`; it passes bare `*.html` literally.
An ordinary no-match exit remains available to the model for correction.

Prepare the pinned upstream search archive explicitly before offline packaging:

```powershell
./scripts/prepare-search-tool.ps1 -ArchivePath ./ripgrep-14.1.1-x86_64-pc-windows-msvc.zip
./scripts/package.ps1 -Executable ./target/sencode-sg.exe -SearchToolManifest ./target/search-tool-14.1.1/search-tool-input.json
```

Omitting `-ArchivePath` allows the developer preparation step to download the
pinned archive. Packaging and installation never download it. Archive, binary
and license hashes are fixed in `scripts/ripgrep.lock.json`. The standalone
installer checks the upstream binary pin in addition to ordinary payload hashes.
COPYING, MIT and Unlicense notices ship with the package.

Native fixtures cover layout, scrolling, supplier traversal, permission colors
and unchanged no-color rendering. Public catalog and owned real-console fixtures
cover all suppliers, duplicate model identities, live configuration refresh,
two-step target selection and immutable active requests. The search fixture uses
an installed binary, System32-only inherited PATH and actual Bash and PowerShell
jobs, with Unicode files and no-match results. The existing CMD tool adapter has
a separate command-line quoting limitation and is outside this qualification;
use Bash or PowerShell for tool jobs. Installation smoke checks test
both aliases, unchanged PATH, corrupt search payloads and locked-file rollback.
These use disposable state and loopback providers; they do not qualify live API
services or a fresh Windows VM.
