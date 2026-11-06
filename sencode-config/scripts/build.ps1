param(
    [string]$Compiler = 'sgc',
    [string]$SengooRoot = $env:SENGOO_ROOT,
    [string]$Clang = $env:SENGOO_CLANG
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $SengooRoot) { $SengooRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot '../../Sengoo')) }
if ($Clang) { $env:SENGOO_CLANG = $Clang; $env:PATH = (Split-Path $Clang) + ';' + $env:PATH }
$env:SENGOO_MODULE_MAP = 'sgsqlite=' + (Join-Path $SengooRoot 'packages/sgsqlite/src/lib.sg')
$env:SENCODE_SENGOO_ROOT = $SengooRoot
$bridgeOutput = Join-Path $projectRoot 'src-tauri/resources/sencode-config-bridge.exe'
New-Item -ItemType Directory -Path (Split-Path $bridgeOutput) -Force | Out-Null
Push-Location (Split-Path $projectRoot -Parent)
try {
    & $Compiler --runtime-mode source-development build src/config_bridge.sg -O 2 -o $bridgeOutput
    if ($LASTEXITCODE -ne 0) { throw 'Sengoo bridge build failed' }
} finally { Pop-Location }
$vcRuntime = Join-Path $env:WINDIR 'System32/vcruntime140.dll'
if (-not (Test-Path -LiteralPath $vcRuntime)) { throw 'vcruntime140.dll not found; install the Microsoft C++ runtime' }
Copy-Item -LiteralPath $vcRuntime -Destination (Join-Path $projectRoot 'src-tauri/resources/vcruntime140.dll')
Push-Location $projectRoot
try {
    & npm.cmd run package
    if ($LASTEXITCODE -ne 0) { throw 'Windows app build failed' }
    & (Join-Path $PSScriptRoot 'package.ps1')
} finally { Pop-Location }
