param([string]$Destination)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
& node (Join-Path $PSScriptRoot 'notices.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Dependency notice generation failed' }
if (-not $Destination) { $Destination = Join-Path $projectRoot 'target/portable/sencode-config' }
$Destination = [IO.Path]::GetFullPath($Destination)
$marker = Join-Path $Destination '.sencode-config-package'
if ((Test-Path -LiteralPath $Destination) -and (Get-ChildItem -LiteralPath $Destination -Force | Select-Object -First 1) -and -not (Test-Path -LiteralPath $marker)) {
    throw "Refusing to overwrite an unowned directory: $Destination"
}
New-Item -ItemType Directory -Path (Join-Path $Destination 'resources') -Force | Out-Null
$pairs = @(
    @('src-tauri/target/release/sencode-config.exe', 'sencode-config.exe'),
    @('src-tauri/resources/sencode-config-bridge.exe', 'resources/sencode-config-bridge.exe'),
    @('src-tauri/resources/vcruntime140.dll', 'resources/vcruntime140.dll'),
    @('README.md', 'README.md'),
    @('verification.md', 'verification.md'),
    @('target/THIRD-PARTY-NOTICES.txt', 'THIRD-PARTY-NOTICES.txt'),
    @('../LICENSE', 'LICENSE')
)
foreach ($pair in $pairs) { Copy-Item -LiteralPath (Join-Path $projectRoot $pair[0]) -Destination (Join-Path $Destination $pair[1]) }
Set-Content -LiteralPath $marker -Value 'sencode-config portable v0.1.0' -Encoding utf8
$hashes = foreach ($pair in $pairs) { $file = Join-Path $Destination $pair[1]; [ordered]@{ path = $pair[1]; sha256 = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() } }
$hashes | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Destination 'checksums.json') -Encoding utf8
$archive = Join-Path (Split-Path $Destination) 'sencode-config-0.1.0-windows-x64.zip'
Compress-Archive -LiteralPath $Destination -DestinationPath $archive -Force
Write-Output $Destination
Write-Output $archive
