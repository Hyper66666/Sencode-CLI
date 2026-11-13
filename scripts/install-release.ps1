#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Prefix,
    [switch]$NoPath,
    [string]$CommandDirectory,
    [string]$ArchivePath
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) {
    throw 'Sencode CLI requires Windows x64.'
}
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Archive/Microsoft.PowerShell.Archive.psd1') -ErrorAction Stop

$tag = 'v0.1.0-preview.20261113'
$archiveName = 'sencode-cli-0.1.0-dev.0-windows-x64.zip'
$expectedHash = '19439583db8395e108d5301954d7fc17d02cc2d9d530dbc02c662eb93e920b8a'
$url = 'https://github.com/Hyper66666/Sencode-CLI/releases/download/' + $tag + '/' + $archiveName
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('sencode-download-' + [Guid]::NewGuid().ToString('N'))
$tlsBefore = [Net.ServicePointManager]::SecurityProtocol
New-Item -ItemType Directory -Path $scratch | Out-Null
try {
    if ($ArchivePath) {
        $archive = (Resolve-Path -LiteralPath $ArchivePath).Path
    } else {
        $archive = Join-Path $scratch $archiveName
        [Net.ServicePointManager]::SecurityProtocol = $tlsBefore -bor [Net.SecurityProtocolType]::Tls12
        Write-Host ('Downloading Sencode CLI ' + $tag + ' (Windows x64)...')
        Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing -TimeoutSec 600
    }
    $actualHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -cne $expectedHash) {
        throw 'Archive SHA-256 mismatch. Nothing was installed; download the release again.'
    }
    $extracted = Join-Path $scratch 'package'
    Expand-Archive -LiteralPath $archive -DestinationPath $extracted
    $installer = Join-Path $extracted 'install.ps1'
    if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) { throw 'Release installer is missing.' }
    $options = @{ PackageDirectory = $extracted; NoPath = $NoPath }
    if ($Prefix) { $options['Prefix'] = $Prefix }
    if ($CommandDirectory) { $options['CommandDirectory'] = $CommandDirectory }
    & $installer @options
    if (-not $?) { throw 'Sencode CLI installation failed.' }
    Write-Host 'Sencode CLI installed. Run sen from a project directory to start.'
} finally {
    [Net.ServicePointManager]::SecurityProtocol = $tlsBefore
    # Only remove files created inside this invocation's unique scratch path.
    # Inventory first, reject links, then remove files and empty directories.
    try {
        $items = @(Get-ChildItem -LiteralPath $scratch -Force -Recurse)
        foreach ($item in $items) {
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'Unexpected link in installer scratch directory; retained for inspection.'
            }
        }
        foreach ($item in @($items | Where-Object { -not $_.PSIsContainer })) {
            Remove-Item -LiteralPath $item.FullName -ErrorAction Stop
        }
        foreach ($item in @($items | Where-Object { $_.PSIsContainer } | Sort-Object { $_.FullName.Length } -Descending)) {
            [IO.Directory]::Delete($item.FullName, $false)
        }
        [IO.Directory]::Delete($scratch, $false)
    } catch {
        Write-Warning ('Temporary download files retained at ' + $scratch + ': ' + $_.Exception.Message)
    }
}
