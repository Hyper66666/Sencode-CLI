#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$PackageDirectory = $PSScriptRoot,
    [string]$Prefix = $(if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'SencodeCLI' } else { '' }),
    [switch]$NoPath,
    [string]$CommandDirectory
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) {
    throw 'This package requires Windows x64.'
}
if (-not $Prefix) { throw 'Specify -Prefix when LOCALAPPDATA is unavailable.' }
$packageRoot = (Resolve-Path -LiteralPath $PackageDirectory).Path
$installRoot = [IO.Path]::GetFullPath($Prefix).TrimEnd('\', '/')
if ($installRoot -eq [IO.Path]::GetPathRoot($installRoot).TrimEnd('\', '/')) {
    throw 'An installation prefix cannot be a drive root.'
}
$bin = Join-Path $installRoot 'bin'
$markerPath = Join-Path $installRoot '.sencode-cli-install.json'
$installedManifestPath = Join-Path $installRoot 'package-manifest.json'
$manifestPath = Join-Path $packageRoot 'package-manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema -ne 1 -or $manifest.product -ne 'sencode-cli' -or $manifest.target -ne 'windows-x64') {
    throw 'Unsupported Sencode CLI package manifest.'
}
$payload = @($manifest.files)
$managedNames = @{}
$searchNames = @{}
if ($manifest.PSObject.Properties.Name -contains 'nativeTools' -and @($manifest.nativeTools).Count -gt 0) {
    $tools = @($manifest.nativeTools)
    $tool = $tools[0]
    $notices = @{
        'ripgrep.COPYING.txt' = 'dfe7d0a6134a17d3de7409762e08dc02133303912875cab40a74ba07a390f85a'
        'ripgrep.LICENSE-MIT.txt' = '970813655a1bf777d2ead189cef71ab73ab92ce04dc864027d61a45de03e6728'
        'ripgrep.UNLICENSE.txt' = '640514163b17f977adc997cb16f51871122cfb0555ebad1a3f01e167b7ba8857'
    }
    if ($tools.Count -ne 1 -or $tool.name -cne 'ripgrep' -or $tool.version -cne '14.1.1' -or $tool.target -cne 'windows-x64' -or
        $tool.executable -cne 'rg.exe' -or $tool.sha256 -cne 'f162b54de2adfc72d78adb1dbada2dedda111ae0a5e2f6e9500f4f909664c5d2' -or
        $tool.archive_url -cne 'https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-pc-windows-msvc.zip' -or
        $tool.archive_sha256 -cne 'd0f534024c42afd6cb4d38907c25cd2b249b79bbe6cc1dbee8e3e37c2b6e25a1' -or
        @($tool.licenses).Count -ne $notices.Count) { throw 'Unpinned bundled search tool.' }
    $searchNames['rg.exe'] = $tool.sha256
    foreach ($notice in $tool.licenses) {
        if (-not $notices.ContainsKey($notice.name) -or $notice.sha256 -cne $notices[$notice.name] -or $searchNames.ContainsKey($notice.name)) { throw 'Unpinned or duplicate ripgrep notice.' }
        $searchNames[$notice.name] = $notice.sha256
    }
}
if ($manifest.PSObject.Properties.Name -contains 'managedRuntimes') {
    $seenEngines = @{}
    foreach ($runtime in @($manifest.managedRuntimes)) {
        $spec = switch -CaseSensitive ($runtime.engine) {
            'codex-app-server' { @{version='0.144.4'; protocol='0.144.4'; executable='codex-app-server.exe'} }
            'sencode-acp' { @{version='0.2.102'; protocol='1'; executable='sencode-agent.exe'} }
            default { throw 'Unsupported managed runtime engine.' }
        }
        $noticeName = $runtime.engine + '.LICENSE.txt'
        if ($seenEngines.ContainsKey($runtime.engine) -or $runtime.runtime_version -cne $spec.version -or
            $runtime.protocol_version -cne $spec.protocol -or $runtime.executable -cne $spec.executable -or
            $runtime.license -cne $noticeName -or $runtime.sha256 -cnotmatch '^[a-f0-9]{64}$') {
            throw 'Unpinned or duplicate managed runtime.'
        }
        $seenEngines[$runtime.engine] = $true
        $managedNames[$spec.executable] = $runtime.sha256
        $managedNames[$noticeName] = ''
    }
}
$names = @{}
foreach ($file in $payload) {
    if ($file.name -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$' -or $names.ContainsKey($file.name)) {
        throw 'Package filenames must be unique plain filenames.'
    }
    if ($file.name -notin @('sen.exe', 'sencode.exe', 'sencode-launcher.exe', 'install.ps1', 'installation.md', 'LICENSE.txt') -and
        -not $managedNames.ContainsKey($file.name) -and
        -not $searchNames.ContainsKey($file.name) -and
        $file.name -cnotmatch '^[a-z0-9][a-z0-9._-]*\.dll$') { throw "Unexpected CLI payload file: $($file.name)" }
    if ($file.sha256 -cnotmatch '^[a-f0-9]{64}$') { throw "Invalid checksum for $($file.name)." }
    $names[$file.name] = $file.sha256
    $source = Join-Path $packageRoot $file.name
    $item = Get-Item -LiteralPath $source
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Package payload is not an ordinary file: $($file.name)."
    }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -cne $file.sha256) {
        throw "Checksum mismatch: $($file.name). Download or rebuild the package again."
    }
}
foreach ($name in $managedNames.Keys) {
    if (-not $names.ContainsKey($name) -or ($managedNames[$name] -and $names[$name] -cne $managedNames[$name])) {
        throw 'Managed runtime or its license is missing or has a mismatched checksum.'
    }
}
foreach ($name in $searchNames.Keys) {
    if (-not $names.ContainsKey($name) -or $names[$name] -cne $searchNames[$name]) { throw 'Bundled ripgrep or its notices are missing or have a mismatched checksum.' }
}
if (-not $names.ContainsKey('sen.exe') -or -not $names.ContainsKey('sencode.exe') -or
    $names['sen.exe'] -cne $names['sencode.exe']) { throw 'The two CLI aliases must be identical executables.' }
# Only an empty prefix or a previous installation owned by this installer may
# be updated. In particular, the desktop/runtime installation is never reused.
foreach ($directory in @($installRoot, $bin)) {
    if (Test-Path -LiteralPath $directory) {
        $item = Get-Item -LiteralPath $directory
        if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Installation directory is not an ordinary directory: $directory"
        }
    }
}
foreach ($metadata in @($markerPath, $installedManifestPath)) {
    if (Test-Path -LiteralPath $metadata) {
        $item = Get-Item -LiteralPath $metadata
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Installation metadata is not an ordinary file: $metadata" }
    }
}
if (Test-Path -LiteralPath $markerPath) {
    $previous = Get-Content -LiteralPath $markerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($previous.schema -ne 1 -or $previous.product -ne 'sencode-cli') { throw 'Foreign installation marker.' }
} elseif ((Test-Path -LiteralPath $installRoot) -and @(Get-ChildItem -LiteralPath $installRoot -Force).Count) {
    throw 'The prefix is nonempty and is not an owned Sencode CLI installation. Select a separate -Prefix.'
}

# Existing consoles retain the PATH they inherited at startup. Install small
# native forwarders into the standard, already-discoverable user command
# directory as well as registering bin for future consoles. The junction
# always points at this installation's one real bin directory. Forwarders keep
# the raw Unicode argument tail intact without passing through another shell.
$explicitCommandDirectory = -not [string]::IsNullOrWhiteSpace($CommandDirectory)
if (-not $explicitCommandDirectory -and -not $NoPath -and $env:LOCALAPPDATA) {
    $CommandDirectory = Join-Path $env:LOCALAPPDATA 'Microsoft/WindowsApps'
    if (-not (Test-Path -LiteralPath $CommandDirectory)) {
        Write-Warning 'The standard user command directory is unavailable. New terminals will use the registered user PATH.'
        $CommandDirectory = ''
    }
}
$commandRoot = ''
$commandLink = ''
$commandMarkerPath = ''
if ($CommandDirectory) {
    if (-not $names.ContainsKey('sencode-launcher.exe')) { throw 'This package does not contain the native command launcher.' }
    $commandRoot = [IO.Path]::GetFullPath($CommandDirectory).TrimEnd('\', '/')
    $commandItem = Get-Item -LiteralPath $commandRoot
    if (-not $commandItem.PSIsContainer -or ($commandItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'The command directory must be an existing ordinary directory.'
    }
    if ($commandRoot -ieq $installRoot -or $commandRoot.StartsWith($installRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'The command directory must be separate from the installation prefix.'
    }
    $commandLink = Join-Path $commandRoot '.sencode-cli-bin'
    $commandMarkerPath = Join-Path $commandRoot '.sencode-cli-command-shims.json'
    $ownedCommands = $null
    if (Test-Path -LiteralPath $commandMarkerPath) {
        $item = Get-Item -LiteralPath $commandMarkerPath
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unsafe command ownership marker.' }
        $ownedCommands = Get-Content -LiteralPath $commandMarkerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($ownedCommands.schema -ne 1 -or $ownedCommands.product -ne 'sencode-cli-command-shims' -or
            $ownedCommands.install_root -ine $installRoot -or $ownedCommands.target -ine $bin) {
            throw 'The command aliases belong to a different installation. Keep its prefix or remove its owned aliases first.'
        }
    }
    if (Test-Path -LiteralPath $commandLink) {
        $item = Get-Item -LiteralPath $commandLink
        if ($null -eq $ownedCommands -or -not $item.PSIsContainer -or $item.LinkType -ne 'Junction' -or
            @($item.Target).Count -ne 1 -or [IO.Path]::GetFullPath([string](@($item.Target)[0])).TrimEnd('\', '/') -ine $bin) {
            throw 'Refusing to replace an unowned command junction.'
        }
    } elseif ($null -ne $ownedCommands) { throw 'The owned command junction is missing; repair or remove the owned aliases first.' }
    foreach ($alias in @('sen', 'sencode')) {
        $filename = $alias + '.exe'
        foreach ($extension in @('.exe', '.com', '.bat', '.cmd', '.ps1')) {
            $candidate = Join-Path $commandRoot ($alias + $extension)
            if (-not (Test-Path -LiteralPath $candidate)) { continue }
            $item = Get-Item -LiteralPath $candidate
            $record = @()
            if ($null -ne $ownedCommands) { $record = @($ownedCommands.files | Where-Object { $_.name -ceq $filename }) }
            if ($extension -ne '.exe' -or $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
                $record.Count -ne 1 -or (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant() -cne $record[0].sha256) {
                throw "Refusing to overwrite an existing command: $candidate"
            }
        }
    }
    $currentlyDiscoverable = @($env:Path -split ';' | Where-Object {
        $_ -and [Environment]::ExpandEnvironmentVariables($_).TrimEnd('\', '/') -ieq $commandRoot
    }).Count -gt 0
    if (-not $currentlyDiscoverable -and -not $explicitCommandDirectory) {
        Write-Warning 'The standard user command directory is absent from this process PATH. Newly opened terminals will discover the registered bin directory.'
    }
}

function Remove-InstallStage([string]$Directory, [string[]]$RetainBusyBackup = @()) {
    if (-not (Test-Path -LiteralPath $Directory)) { return }
    $root = [IO.Path]::GetFullPath($Directory).TrimEnd('\')
    $inventory = @(Get-ChildItem -LiteralPath $root -Force -Recurse)
    foreach ($entry in $inventory) {
        if (-not $entry.FullName.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase) -or
            ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unsafe installation staging path.' }
    }
    foreach ($entry in @($inventory | Where-Object { -not $_.PSIsContainer })) {
        try { Remove-Item -LiteralPath $entry.FullName -Force }
        catch {
            $nativeError = $_.Exception.HResult -band 0xffff
            if ($entry.FullName -notin $RetainBusyBackup -or $nativeError -notin @(5,32,33)) { throw }
            # A committed atomic replacement may leave a running image mapped
            # at its owned backup path. Preserve it without stopping sessions.
            $entry.FullName
        }
    }
    foreach ($entry in @($inventory | Where-Object PSIsContainer | Sort-Object { $_.FullName.Length } -Descending)) {
        if (@(Get-ChildItem -LiteralPath $entry.FullName -Force).Count -eq 0) { Remove-Item -LiteralPath $entry.FullName }
    }
    if (@(Get-ChildItem -LiteralPath $root -Force).Count -eq 0) { Remove-Item -LiteralPath $root }
}

New-Item -ItemType Directory -Path $bin -Force | Out-Null
$stage = Join-Path $installRoot ('.install-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null
$operations = [Collections.Generic.List[object]]::new()
$preserveStage = $false
$published = $false
$cleanupPending = @()
$commandStage = ''
$createdCommandLink = $false
function Publish-InstallFile([string]$Staged, [string]$Destination, [string]$BackupName, [string]$BackupDirectory = $stage) {
    $backup = $null
    if (Test-Path -LiteralPath $Destination) {
        $backup = Join-Path $BackupDirectory $BackupName
        [IO.File]::Replace($Staged, $Destination, $backup)
    } else { [IO.File]::Move($Staged, $Destination) }
    # A failed atomic replace leaves the destination unchanged. Record only
    # completed mutations so rollback never tries to rewrite the locked file.
    $operations.Add([pscustomobject]@{ destination = $Destination; backup = $backup })
}
try {
    foreach ($file in $payload) {
        $destination = Join-Path $(if (($file.name -like '*.exe' -and $file.name -ne 'sencode-launcher.exe') -or $file.name -like '*.dll') { $bin } else { $installRoot }) $file.name
        if (Test-Path -LiteralPath $destination) {
            $existing = Get-Item -LiteralPath $destination
            if ($existing.PSIsContainer -or ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Refusing to replace non-file payload: $destination"
            }
        }
        $staged = Join-Path $stage $file.name
        Copy-Item -LiteralPath (Join-Path $packageRoot $file.name) -Destination $staged
        if ((Get-FileHash -LiteralPath $staged -Algorithm SHA256).Hash.ToLowerInvariant() -cne $file.sha256) {
            throw "Staged checksum mismatch: $($file.name)."
        }
        Publish-InstallFile $staged $destination ($file.name + '.previous')
    }
    # Keep package provenance beside the installed application, never in a
    # legacy runtime directory or inside the user's state database.
    $manifestDestination = $installedManifestPath
    $stagedManifest = Join-Path $stage 'manifest.next'
    Copy-Item -LiteralPath $manifestPath -Destination $stagedManifest
    Publish-InstallFile $stagedManifest $manifestDestination 'manifest.previous'
    # The execution host resolves its trusted runtime manifest relative to its
    # own image, including when launched through either global alias.
    $stagedBinManifest = Join-Path $stage 'bin-manifest.next'
    Copy-Item -LiteralPath $manifestPath -Destination $stagedBinManifest
    Publish-InstallFile $stagedBinManifest (Join-Path $bin 'package-manifest.json') 'bin-manifest.previous'
    $marker = [ordered]@{ schema = 1; product = 'sencode-cli'; version = $manifest.version; executable_sha256 = $names['sen.exe'] }
    $stagedMarker = Join-Path $stage 'marker.next'
    $marker | ConvertTo-Json | Set-Content -LiteralPath $stagedMarker -Encoding UTF8
    Publish-InstallFile $stagedMarker $markerPath 'marker.previous'
    if ($commandRoot) {
        $commandStage = Join-Path $commandRoot ('.sencode-cli-install-' + [Guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $commandStage | Out-Null
        if (-not (Test-Path -LiteralPath $commandLink)) {
            New-Item -ItemType Junction -Path $commandLink -Target $bin | Out-Null
            $createdCommandLink = $true
        }
        $commandFiles = [Collections.Generic.List[object]]::new()
        foreach ($filename in @('sen.exe', 'sencode.exe')) {
            $staged = Join-Path $commandStage $filename
            Copy-Item -LiteralPath (Join-Path $packageRoot 'sencode-launcher.exe') -Destination $staged
            if ((Get-FileHash -LiteralPath $staged -Algorithm SHA256).Hash.ToLowerInvariant() -cne $names['sencode-launcher.exe']) {
                throw 'Staged command launcher checksum mismatch.'
            }
            $commandFiles.Add([ordered]@{ name = $filename; sha256 = (Get-FileHash -LiteralPath $staged -Algorithm SHA256).Hash.ToLowerInvariant() })
            Publish-InstallFile $staged (Join-Path $commandRoot $filename) ($filename + '.previous') $commandStage
        }
        $commandMarker = [ordered]@{ schema = 1; product = 'sencode-cli-command-shims'; install_root = $installRoot; target = $bin; files = @($commandFiles.ToArray()) }
        $staged = Join-Path $commandStage 'commands.next'
        $commandMarker | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $staged -Encoding UTF8
        Publish-InstallFile $staged $commandMarkerPath 'commands.previous' $commandStage
    }
    $published = $true
} catch {
    $failure = $_
    $rollbackFailures = [Collections.Generic.List[string]]::new()
    for ($index = $operations.Count - 1; $index -ge 0; $index--) {
        $operation = $operations[$index]
        try {
            if ($operation.backup) { Copy-Item -LiteralPath $operation.backup -Destination $operation.destination -Force }
            elseif (Test-Path -LiteralPath $operation.destination) { Remove-Item -LiteralPath $operation.destination -Force }
        } catch { $rollbackFailures.Add($_.Exception.Message) }
    }
    if ($createdCommandLink) {
        try {
            $item = Get-Item -LiteralPath $commandLink
            if ($item.LinkType -ne 'Junction' -or [IO.Path]::GetFullPath([string](@($item.Target)[0])).TrimEnd('\', '/') -ine $bin) {
                throw 'The command junction changed during rollback.'
            }
            # Nonrecursive Directory.Delete removes this verified junction,
            # without enumerating or deleting any target contents.
            [IO.Directory]::Delete($commandLink)
        } catch { $rollbackFailures.Add($_.Exception.Message) }
    }
    if ($rollbackFailures.Count -gt 0) {
        $preserveStage = $true
        throw "Installation failed: $($failure.Exception.Message). Rollback needs recovery from $stage : $($rollbackFailures -join '; ')"
    }
    throw $failure
} finally {
    if (-not $preserveStage) {
        $retain = if ($published) { @($operations | Where-Object backup | ForEach-Object backup) } else { @() }
        $cleanupPending += @(Remove-InstallStage $stage -RetainBusyBackup $retain)
        if ($commandStage) { $cleanupPending += @(Remove-InstallStage $commandStage -RetainBusyBackup $retain) }
    }
}

$pathChanged = $false
if (-not $NoPath) {
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $components = @($userPath -split ';' | Where-Object { $_ })
    $present = @($components | Where-Object { [Environment]::ExpandEnvironmentVariables($_).TrimEnd('\') -ieq $bin }).Count -gt 0
    if (-not $present) {
        [Environment]::SetEnvironmentVariable('Path', (($components + $bin) -join ';'), 'User')
        $pathChanged = $true
        if (-not ('SencodeCliInstallerEnvironment' -as [type])) {
            Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class SencodeCliInstallerEnvironment {
    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern IntPtr SendMessageTimeoutW(IntPtr window, uint message,
        UIntPtr parameter, string text, uint flags, uint timeout, out UIntPtr result);
}
'@
        }
        $broadcastResult = [UIntPtr]::Zero
        [void][SencodeCliInstallerEnvironment]::SendMessageTimeoutW([IntPtr]0xffff, 0x1a,
            [UIntPtr]::Zero, 'Environment', 2, 2000, [ref]$broadcastResult)
    }
    if (@($env:Path -split ';' | Where-Object { $_.TrimEnd('\') -ieq $bin }).Count -eq 0) { $env:Path += ';' + $bin }
}
if ($cleanupPending.Count -gt 0) { Write-Warning 'Update installed. Running sessions retain their old program backups until they exit.' }
[pscustomobject]@{ prefix = $installRoot; bin = $bin; version = $manifest.version; path_changed = $pathChanged; aliases = @('sen.exe', 'sencode.exe'); command_directory = $commandRoot; command_aliases = $(if ($commandRoot) { @('sen.exe', 'sencode.exe') } else { @() }); cleanup_deferred = @($cleanupPending) }
