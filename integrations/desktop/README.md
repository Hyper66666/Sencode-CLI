# Desktop shared-state adapter

`shared-state.patch` preserves the CLI-related desktop integration against
Sencode monorepo revision `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`.
It includes the shared SQLite store, session catalog, execution fencing,
projection and related tests. It is an integration artifact, not a separate
desktop application or a requirement for native CLI-only operation.

In a checkout of that baseline, run `git apply --check` on this patch before
applying it. The desktop adapter intentionally retains its original monorepo
paths to `windows/sencode-cli/shared-state`. Place this CLI source in that
location when validating the adapter, or adjust the two SQL include paths for
your checkout. Do not overwrite a modified desktop tree without reviewing the
patch. No migration is applied merely by checking out these sources.

From this repository, integration verification accepts the explicit desktop
source path:

```powershell
./scripts/test-shared-store.ps1 -DesktopRoot ../sencode/windows/sencode-desktop/src-tauri -SengooRoot ../Sengoo -RustOnly
```

The optional managed ACP runtime also remains an external Sencode component:
pass its checkout with `prepare-acp-runtime.ps1 -RuntimeRoot PATH`. The official
Codex runtime uses the checked-in `runtime-manifests/codex.json` release pin.
Neither runtime binary nor account credentials is included in this repository.
