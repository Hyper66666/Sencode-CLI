param(
    [string]$SengooRoot = $env:SENGOO_ROOT,
    [ValidateSet('Debug', 'Release')][string]$Configuration = 'Debug',
    [switch]$UpdateLock
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $SengooRoot) {
    $SengooRoot = Join-Path (Split-Path $projectRoot -Parent) 'Sengoo'
}
$SengooRoot = (Resolve-Path -LiteralPath $SengooRoot).Path
$compiler = Join-Path $SengooRoot 'target/debug/sgc.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Build Sengoo sgc before building Sencode CLI.' }
$env:SENGOO_STDLIB = Join-Path $SengooRoot 'tools/stdlib'
$env:SENGOO_RUNTIME = Join-Path $SengooRoot 'tools/stdlib/runtime.c'
$outputDirectory = Join-Path $projectRoot 'target'
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
Push-Location $projectRoot
try {
    $packageManager = Join-Path $SengooRoot 'target/debug/sgpm.exe'
    if (-not (Test-Path -LiteralPath $packageManager)) { throw 'Build Sengoo sgpm before building Sencode CLI.' }
    $env:SGPM_SGC = $compiler
    if ($UpdateLock -or -not (Test-Path -LiteralPath (Join-Path $projectRoot 'Sengoo.lock'))) {
        & $packageManager update --runtime-mode source-development
        if ($LASTEXITCODE -ne 0) { throw 'Sencode dependency lock resolution failed.' }
    }
    $buildArguments = @('build', '--runtime-mode', 'source-development', '--locked')
    if ($Configuration -eq 'Release') { $buildArguments += '--release' }
    & $packageManager @buildArguments
    if ($LASTEXITCODE -eq 0) {
        $profile = if ($Configuration -eq 'Release') { 'release' } else { 'debug' }
        Copy-Item -LiteralPath (Join-Path $outputDirectory "$profile/sencode_sg.exe") -Destination (Join-Path $outputDirectory 'sencode-sg.exe')
    }
    if ($LASTEXITCODE -ne 0) { throw "Sencode compilation failed ($LASTEXITCODE)." }
} finally { Pop-Location }
