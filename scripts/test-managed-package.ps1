#requires -Version 5.1
[CmdletBinding()]
param([string]$Executable = (Join-Path $PSScriptRoot '../target/sencode-sg.exe'), [string[]]$RuntimeDll = @())
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$project = Split-Path $PSScriptRoot -Parent
$root = Join-Path $project ('target/managed-package-fixture-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root | Out-Null
$image = (Resolve-Path -LiteralPath $Executable).Path
$hash = (Get-FileHash -LiteralPath $image -Algorithm SHA256).Hash.ToLowerInvariant()
$license = Join-Path $root 'fixture-license.txt'
'Packaging fixture only. This is not an official account runtime.' | Set-Content -LiteralPath $license -Encoding UTF8
$inputPath = Join-Path $root 'input.json'
$runtime = [ordered]@{engine='codex-app-server';runtime_version='0.144.4';protocol_version='0.144.4';executable='codex-app-server.exe';sha256=$hash;source=$image;license=$license}
function Write-Input($Entries) {
    [ordered]@{schema=1;managedRuntimes=@($Entries)} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $inputPath -Encoding UTF8
}
Write-Input @($runtime)
$package = & (Join-Path $PSScriptRoot 'package.ps1') -Executable $image -RuntimeDll $RuntimeDll -ManagedRuntimeManifest $inputPath -OutputDirectory (Join-Path $root 'valid')
$manifest = Get-Content -LiteralPath (Join-Path $package.package_directory 'package-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (@($manifest.managedRuntimes).Count -ne 1 -or $manifest.managedRuntimes[0].sha256 -cne $hash) { throw 'Pinned runtime manifest missing.' }
$prefix = Join-Path $root 'installed'
$install = & (Join-Path $PSScriptRoot 'install.ps1') -PackageDirectory $package.package_directory -Prefix $prefix -NoPath
$binManifest = Join-Path $install.bin 'package-manifest.json'
if ((Get-FileHash -LiteralPath $binManifest).Hash -cne (Get-FileHash -LiteralPath (Join-Path $prefix 'package-manifest.json')).Hash -or
    (Get-FileHash -LiteralPath (Join-Path $install.bin 'codex-app-server.exe')).Hash.ToLowerInvariant() -cne $hash -or
    -not (Test-Path -LiteralPath (Join-Path $prefix 'codex-app-server.LICENSE.txt'))) { throw 'Runtime, license or image-relative manifest was not installed.' }
$rejections = @()
foreach ($case in @('checksum','version','engine','duplicate')) {
    $entry = [ordered]@{}
    foreach ($key in $runtime.Keys) { $entry[$key] = $runtime[$key] }
    switch ($case) {
        'checksum' { $entry.sha256 = ('0' * 64) }
        'version' { $entry.runtime_version = '0.0.0' }
        'engine' { $entry.engine = 'arbitrary-process' }
    }
    Write-Input $(if ($case -eq 'duplicate') { @($entry,$entry) } else { @($entry) })
    $rejected = $false
    try { & (Join-Path $PSScriptRoot 'package.ps1') -Executable $image -Launcher (Join-Path $project 'target/sencode-launcher.exe') -ManagedRuntimeManifest $inputPath -OutputDirectory (Join-Path $root $case) | Out-Null }
    catch { $rejected = $true }
    if (-not $rejected) { throw "Invalid runtime input accepted: $case" }
    $rejections += $case
}
$payload = Join-Path $package.package_directory 'codex-app-server.exe'
[IO.File]::AppendAllText($payload, 'tampered')
$rejected = $false
try { & (Join-Path $PSScriptRoot 'install.ps1') -PackageDirectory $package.package_directory -Prefix $prefix -NoPath | Out-Null }
catch { $rejected = $true }
if (-not $rejected -or (Get-FileHash -LiteralPath (Join-Path $install.bin 'sen.exe')).Hash.ToLowerInvariant() -cne $hash -or
    (Get-FileHash -LiteralPath (Join-Path $install.bin 'codex-app-server.exe')).Hash.ToLowerInvariant() -cne $hash) { throw 'Tampered package was accepted or changed installed files.' }
$evidence = [ordered]@{schema=1;result='passed';scope='packaging fixtures; no official runtime execution or credentials';runtime_and_notice_installed=$true;image_relative_manifest=$true;invalid_inputs_rejected=$rejections;tampered_update_preserves_install=$true;artifact_root=$root}
$evidence | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $root 'evidence.json') -Encoding UTF8
$evidence
