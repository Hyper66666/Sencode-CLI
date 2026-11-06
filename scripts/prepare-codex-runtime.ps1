#requires -Version 5.1
[CmdletBinding()]
param([string]$OutputDirectory = (Join-Path $PSScriptRoot '../target/managed-codex-0.144.4'))
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$project = Split-Path $PSScriptRoot -Parent
$pinPath = Join-Path $project 'runtime-manifests/codex.json'
$pin = Get-Content -LiteralPath $pinPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($pin.runtimeId -cne 'codex-app-server' -or $pin.version -cne '0.144.4' -or
    $pin.releaseTag -cne 'rust-v0.144.4' -or $pin.asset.sha256 -cnotmatch '^[a-f0-9]{64}$' -or
    $pin.asset.url -cne 'https://github.com/openai/codex/releases/download/rust-v0.144.4/codex-app-server-x86_64-pc-windows-msvc.exe.zip' -or
    $pin.asset.archiveEntry -cne 'codex-app-server-x86_64-pc-windows-msvc.exe') { throw 'Desktop Codex pin differs from the supported adapter contract.' }
$root = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $root | Out-Null
$archive = Join-Path $root 'upstream.zip'
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri $pin.asset.url -OutFile $archive -TimeoutSec 180 -MaximumRedirection 5
}
$item = Get-Item -LiteralPath $archive
if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
    $item.Length -ne $pin.asset.archiveSize -or $item.Length -gt $pin.asset.maximumArchiveSize -or
    (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $pin.asset.sha256) { throw 'Codex archive size/checksum does not match the desktop pin.' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($archive)
$executable = Join-Path $root 'codex-app-server.exe'
try {
    $entries = @($zip.Entries | Where-Object { $_.FullName -ceq $pin.asset.archiveEntry })
    if ($entries.Count -ne 1 -or $entries[0].Length -gt 536870912 -or $entries[0].Length -lt 1) { throw 'Pinned Codex archive entry missing, duplicated or too large.' }
    if (-not (Test-Path -LiteralPath $executable)) { [IO.Compression.ZipFileExtensions]::ExtractToFile($entries[0], $executable, $false) }
    $source = $entries[0].Open()
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $entryHash = ([BitConverter]::ToString($sha.ComputeHash($source))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose(); $source.Dispose() }
    if ((Get-FileHash -LiteralPath $executable -Algorithm SHA256).Hash.ToLowerInvariant() -cne $entryHash) { throw 'Extracted Codex executable differs from the pinned archive.' }
} finally { $zip.Dispose() }
$notice = Join-Path $root 'upstream-license.txt'
if (-not (Test-Path -LiteralPath $notice)) {
    $licenseUrl = 'https://raw.githubusercontent.com/openai/codex/rust-v0.144.4/LICENSE'
    $license = (Invoke-WebRequest -Uri $licenseUrl -TimeoutSec 30 -MaximumRedirection 2).Content
    if ($license.Length -gt 1048576 -or $license -notmatch 'Apache License') { throw 'Unexpected upstream license response.' }
    [IO.File]::WriteAllText($notice, "Source: $licenseUrl`r`nArchive: $($pin.asset.url)`r`nArchive SHA-256: $($pin.asset.sha256)`r`n`r`n$license", [Text.UTF8Encoding]::new($false))
}
$runtimeInput = [ordered]@{schema=1;managedRuntimes=@([ordered]@{engine='codex-app-server';runtime_version='0.144.4';protocol_version='0.144.4';executable='codex-app-server.exe';sha256=$entryHash;source=$executable;license=$notice})}
$inputPath = Join-Path $root 'packaging-input.json'
$runtimeInput | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $inputPath -Encoding UTF8
[ordered]@{schema=1;archive_sha256=$pin.asset.sha256;executable_sha256=$entryHash;desktop_pin_sha256=(Get-FileHash -LiteralPath $pinPath).Hash.ToLowerInvariant();license_sha256=(Get-FileHash -LiteralPath $notice).Hash.ToLowerInvariant();qualified='download/hash only; runtime execution and live account access are separate'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'provenance.json') -Encoding UTF8
[pscustomobject]@{packaging_input=$inputPath;executable=$executable;sha256=$entryHash}
