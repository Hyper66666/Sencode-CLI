[CmdletBinding()]
param(
    [string] $SengooRoot = '',
    [string] $DesktopRoot = '',
    [string] $Sgc = '',
    [string] $ClangDirectory = '',
    [switch] $RustOnly
)
$ErrorActionPreference = 'Stop'
$cliRoot = Split-Path -Parent $PSScriptRoot
if (!$DesktopRoot) { throw 'Supply -DesktopRoot pointing to the compatible Sencode desktop src-tauri checkout. See integrations/desktop/README.md.' }
$DesktopRoot = (Resolve-Path -LiteralPath $DesktopRoot).Path
if (!$SengooRoot) { $SengooRoot = [IO.Path]::GetFullPath((Join-Path $cliRoot '../Sengoo')) }
if (!$Sgc) { $Sgc = Join-Path $SengooRoot 'target/debug/sgc.exe' }
if (!(Test-Path -LiteralPath $Sgc -PathType Leaf)) { throw "Compiler not found: $Sgc. Supply -Sgc and -SengooRoot." }
$candidate = Join-Path $cliRoot 'target/tests_state.exe'
$savedPath = $env:PATH
$savedMap = $env:SENGOO_MODULE_MAP
$savedCli = $env:SENCODE_SHARED_CLI_TEST
$savedConfig = $env:TAURI_CONFIG
try {
    if ($ClangDirectory) { $env:PATH = $ClangDirectory + [IO.Path]::PathSeparator + $env:PATH }
    $env:SENGOO_MODULE_MAP = 'sgsqlite=' + (Join-Path $SengooRoot 'packages/sgsqlite/src/lib.sg').Replace('\','/') + ';sgllm=' + (Join-Path $SengooRoot 'packages/sgllm/src/lib.sg') + ';sgmcp=' + (Join-Path $SengooRoot 'packages/sgmcp/src/lib.sg') + ';sgschema=' + (Join-Path $SengooRoot 'packages/sgschema/src/lib.sg') + ';sgagent=' + (Join-Path $SengooRoot 'packages/sgagent/src/lib.sg')
    Push-Location $cliRoot
    try {
        & $Sgc --runtime-mode source-development build src/tests_state.sg --force-rebuild -O 0 -o $candidate
        if ($LASTEXITCODE -ne 0) { throw 'Sengoo shared-state helper compilation failed.' }
    } finally { Pop-Location }
    $env:SENCODE_SHARED_CLI_TEST = $candidate
    if ($RustOnly) {
        # Tests do not consume a WebView or packaged node/runtime resources.
        # This override does not constitute a desktop distribution build.
        $env:TAURI_CONFIG = '{"bundle":{"resources":null},"build":{"frontendDist":"http://localhost:1420"}}'
    }
    Push-Location $desktopRoot
    try {
        & cargo test --lib persistence::shared_store::tests:: -- --include-ignored --test-threads=1
        if ($LASTEXITCODE -ne 0) { throw 'Shared-store gate failed (including required native CLI/desktop subprocess test).' }
    } finally { Pop-Location }
} finally {
    $env:PATH = $savedPath
    $env:SENGOO_MODULE_MAP = $savedMap + ';sgllm=' + (Join-Path $SengooRoot 'packages/sgllm/src/lib.sg') + ';sgmcp=' + (Join-Path $SengooRoot 'packages/sgmcp/src/lib.sg') + ';sgschema=' + (Join-Path $SengooRoot 'packages/sgschema/src/lib.sg') + ';sgagent=' + (Join-Path $SengooRoot 'packages/sgagent/src/lib.sg')
    $env:SENCODE_SHARED_CLI_TEST = $savedCli
    $env:TAURI_CONFIG = $savedConfig
}
