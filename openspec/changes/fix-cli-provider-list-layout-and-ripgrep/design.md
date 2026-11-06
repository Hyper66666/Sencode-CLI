# Design

Remove short-transcript leading padding while keeping the centered empty home,
viewport history anchor, bottom composer and reserved blank composer separator.
Permission labels use semantic spans: manual light blue, auto yellow, full red. Captured
active permission and a pending next-turn permission get independent spans.

Use all saved connection catalogs, without requiring a connection switch to list
models. Replace paired columns with sequential supplier headings and model rows.
Up/down traverses model rows across suppliers; headings are not selectable.
Left/right remains a supplier shortcut. Filter by supplier or model. Scroll the
menu with the selection and retain a supplier heading for long groups. Enter
still opens effort selection before accepting a complete target. Reopen the
catalog from SQLite so edits made by sencode-config are visible. `sen models`
returns the same public enabled-model metadata, with legacy saved-model fallback.

Ship ripgrep 14.1.1 from its official release. Preparation explicitly downloads
the pinned archive, verifies the pinned archive and executable hashes, and
produces offline packaging inputs. Package/install verify payload checksums and
retain COPYING/MIT/Unlicense notices. Commands prepend the sibling tool directory
only to their own environment when rg.exe is present; the process and system PATH
are unchanged. All existing shell, permission, cancellation and output contracts
remain in force. Missing rg stays an explicit doctor diagnostic in source builds.

Fixtures use isolated databases, random test credentials and loopback services.
Installed command tests run with a System32-only inherited PATH, including Bash,
PowerShell, no matches, Unicode paths and the command shape from the screenshot.
No real configuration or secret is needed.
