# Native Sengoo worker example

This source example illustrates protocol `sencode.native-worker/1`; it is not a
complete extension SDK. Worker authors need a matching Sengoo toolchain. Users
of a precompiled worker do not need the compiler. A native worker has the user's
OS access and does not run in a sandbox.

Build from this repository's `windows/sencode-cli` directory, mapping the local
wire helper explicitly. The example only decides whether a supported native
file-edit tool may continue; it cannot invoke tools, grant permission or alter
tool results.

```powershell
$env:SENGOO_MODULE_MAP = 'hook_sdk=' + (Join-Path (Get-Location) 'src/hook_sdk.sg')
sgc build examples/native-hook-worker/main.sg -o examples/native-hook-worker/protected-paths.exe
$manifestPath = Join-Path (Get-Location) 'examples/native-hook-worker/sencode-worker.json'
$manifest = Get-Content examples/native-hook-worker/sencode-worker.example.json -Raw | ConvertFrom-Json
$manifest.sha256 = (Get-FileHash examples/native-hook-worker/protected-paths.exe -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM
sen extensions add $manifestPath
sen extensions inspect protected-paths
sen extensions enable protected-paths
```

The all-zero hash in the checked-in template intentionally cannot authorize an
executable. `add` leaves the worker disabled. Trust review at `enable` does not
approve execution: each matching invocation asks again with the exact JSON it
will disclose. Plan, child and unattended execution refuse the worker. Normal
parent-tool permissions still apply after a `continue` decision.

This example is not filesystem protection: arbitrary commands, other editors
and applications can still modify those paths. Disable it with
`sen extensions disable protected-paths`; remove its registry entry with
`sen extensions remove protected-paths`.
