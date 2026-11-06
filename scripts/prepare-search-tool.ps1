#requires -Version 5.1
[CmdletBinding()]
param([string]$ArchivePath, [string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = Split-Path $PSScriptRoot -Parent
$pin = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'ripgrep.lock.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $projectRoot ('target/search-tool-' + $pin.version) }
if (-not $ArchivePath) {
    $ArchivePath = Join-Path $projectRoot ('target/downloads/ripgrep-' + $pin.version + '-windows-x64.zip')
    if (-not (Test-Path -LiteralPath $ArchivePath)) {
        New-Item -ItemType Directory -Path (Split-Path $ArchivePath -Parent) -Force | Out-Null
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $pin.archive_url -OutFile $ArchivePath -UseBasicParsing
    }
}
$archiveItem = Get-Item -LiteralPath $ArchivePath
if ($archiveItem.PSIsContainer -or ($archiveItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
    $archiveItem.Length -gt 33554432 -or
    (Get-FileHash -LiteralPath $archiveItem.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $pin.archive_sha256) {
    throw 'Ripgrep archive differs from its pinned upstream checksum or exceeds bounds.'
}
$outputRoot = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $outputRoot) { throw 'Search tool output already exists. Select a new -OutputDirectory.' }
New-Item -ItemType Directory -Path $outputRoot | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($archiveItem.FullName)
$inputs = @()
try {
    # Extract only exact pinned entries; never materialize arbitrary zip paths.
    foreach ($file in $pin.files) {
        $entries = @($archive.Entries | Where-Object { $_.FullName -ceq ($pin.archive_prefix + $file.entry) })
        if ($entries.Count -ne 1 -or $entries[0].Length -gt 16777216) { throw 'Missing, duplicate or oversized ripgrep archive entry.' }
        $destination = Join-Path $outputRoot $file.name
        [IO.Compression.ZipFileExtensions]::ExtractToFile($entries[0], $destination)
        if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -cne $file.sha256) { throw 'Ripgrep payload differs from the pin.' }
        $inputs += [ordered]@{name=$file.name;source=$destination;sha256=$file.sha256}
    }
} finally { $archive.Dispose() }
$manifest = [ordered]@{schema=1;name=$pin.name;version=$pin.version;target=$pin.target;archive_url=$pin.archive_url;archive_sha256=$pin.archive_sha256;files=$inputs}
$manifestPath = Join-Path $outputRoot 'search-tool-input.json'
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
[pscustomobject]@{manifest=$manifestPath;version=$pin.version;archive_sha256=$pin.archive_sha256;offline_packaging=$true}
