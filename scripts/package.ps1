#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Executable,
    [string]$OutputDirectory,
    [string[]]$RuntimeDll = @(),
    [string]$ManagedRuntimeManifest,
    [string]$SearchToolManifest,
    [string]$LicensePath,
    [string]$Launcher
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $Executable) { $Executable = Join-Path $projectRoot 'target/sencode-sg.exe' }
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $projectRoot 'target/packages' }
if (-not $LicensePath) { $LicensePath = Join-Path $projectRoot 'LICENSE' }
if (-not $Launcher) {
    $Launcher = Join-Path $projectRoot 'target/sencode-launcher.exe'
    $launcherSource = Join-Path $PSScriptRoot 'native/command-launcher.c'
    New-Item -ItemType Directory -Force -Path (Split-Path $Launcher -Parent) | Out-Null
    # A small OS-only forwarding binary preserves raw Windows argv in existing
    # shells. It contains no agent/TUI logic and needs no C runtime DLL.
    & clang --target=x86_64-pc-windows-msvc -fuse-ld=lld -O2 -fno-builtin -fno-stack-protector -nostdlib '-Wl,/entry:sencode_command_launcher_entry' '-Wl,/subsystem:console' $launcherSource -lkernel32 -o $Launcher
    if ($LASTEXITCODE -ne 0) { throw 'Could not build the Windows command forwarder.' }
}

# Read PE import tables directly: packaging does not depend on dumpbin, clang
# or a particular Visual Studio shell. Both normal and delay imports matter.
function Get-PeImports([string]$Path) {
    $image = [IO.File]::ReadAllBytes($Path)
    function Read-U16([long]$Offset) {
        if ($Offset -lt 0 -or $Offset + 2 -gt $image.Length) { throw "Truncated PE image: $Path" }
        [BitConverter]::ToUInt16($image, [int]$Offset)
    }
    function Read-U32([long]$Offset) {
        if ($Offset -lt 0 -or $Offset + 4 -gt $image.Length) { throw "Truncated PE image: $Path" }
        [BitConverter]::ToUInt32($image, [int]$Offset)
    }
    if ((Read-U16 0) -ne 0x5a4d) { throw "Not a Windows PE executable: $Path" }
    $pe = [long](Read-U32 0x3c)
    if ((Read-U32 $pe) -ne 0x4550 -or (Read-U16 ($pe + 4)) -ne 0x8664) {
        throw "Expected a Windows x64 PE image: $Path"
    }
    $optional = $pe + 24
    $optionalSize = Read-U16 ($pe + 20)
    if ((Read-U16 $optional) -ne 0x20b -or $optionalSize -lt 224) { throw 'Invalid PE32+ optional header.' }
    $sectionCount = Read-U16 ($pe + 6)
    if ($sectionCount -lt 1 -or $sectionCount -gt 96) { throw 'Invalid PE section count.' }
    $sections = @()
    for ($index = 0; $index -lt $sectionCount; $index++) {
        $offset = $optional + $optionalSize + $index * 40
        $sections += [pscustomobject]@{ address = [long](Read-U32 ($offset + 12)); virtual_size = [long](Read-U32 ($offset + 8)); size = [long](Read-U32 ($offset + 16)); raw = [long](Read-U32 ($offset + 20)) }
    }
    function Resolve-Rva([long]$Rva) {
        foreach ($section in $sections) {
            if ($Rva -ge $section.address -and $Rva -lt ($section.address + [Math]::Max($section.virtual_size, $section.size))) {
                $relative = $Rva - $section.address
                if ($relative -ge $section.size -or $section.raw + $relative -ge $image.Length) { throw 'PE import points outside raw section data.' }
                return ($section.raw + $relative)
            }
        }
        throw 'PE import RVA is outside all sections.'
    }
    function Read-ImportName([long]$Rva) {
        $offset = Resolve-Rva $Rva
        $end = $offset
        while ($end -lt $image.Length -and $end - $offset -le 255 -and $image[$end] -ne 0) { $end++ }
        if ($end -ge $image.Length -or $end - $offset -gt 255) { throw 'Unterminated PE import name.' }
        $name = [Text.Encoding]::ASCII.GetString($image, [int]$offset, [int]($end - $offset)).ToLowerInvariant()
        if ($name -cnotmatch '^[a-z0-9][a-z0-9._-]*\.dll$') { throw "Invalid imported DLL name: $name" }
        $name
    }
    $imports = @()
    foreach ($directoryIndex in @(1, 13)) {
        $directory = $optional + 112 + $directoryIndex * 8
        $rva = Read-U32 $directory
        $size = Read-U32 ($directory + 4)
        if ($rva -eq 0 -and $size -eq 0) { continue }
        $stride = if ($directoryIndex -eq 1) { 20 } else { 32 }
        if ($rva -eq 0 -or $size -lt $stride -or $size -gt 1048576) { throw 'Invalid PE import directory.' }
        $terminated = $false
        for ($entry = 0; $entry + $stride -le $size; $entry += $stride) {
            $offset = Resolve-Rva ([long]$rva + $entry)
            $allZero = $true
            for ($field = 0; $field -lt $stride; $field += 4) { if ((Read-U32 ($offset + $field)) -ne 0) { $allZero = $false } }
            if ($allZero) { $terminated = $true; break }
            $nameRva = if ($directoryIndex -eq 1) { Read-U32 ($offset + 12) } else { Read-U32 ($offset + 4) }
            if ($directoryIndex -eq 13 -and ((Read-U32 $offset) -band 1) -ne 1) {
                throw 'VA-based delay imports are unsupported; rebuild with RVA-based delay imports.'
            }
            $imports += Read-ImportName $nameRva
        }
        if (-not $terminated) { throw 'Unterminated PE import descriptor table.' }
    }
    @($imports | Sort-Object -Unique)
}
function Test-WindowsSystemDll([string]$Name) {
    $system = @('advapi32.dll', 'bcrypt.dll', 'bcryptprimitives.dll', 'combase.dll', 'comctl32.dll', 'comdlg32.dll', 'crypt32.dll', 'cryptbase.dll', 'dbghelp.dll', 'dnsapi.dll', 'dwmapi.dll', 'gdi32.dll', 'imm32.dll', 'iphlpapi.dll', 'kernel32.dll', 'kernelbase.dll', 'msvcrt.dll', 'mswsock.dll', 'ncrypt.dll', 'netapi32.dll', 'normaliz.dll', 'ntdll.dll', 'ole32.dll', 'oleaut32.dll', 'powrprof.dll', 'profapi.dll', 'psapi.dll', 'rpcrt4.dll', 'secur32.dll', 'setupapi.dll', 'shell32.dll', 'shlwapi.dll', 'sspicli.dll', 'ucrtbase.dll', 'user32.dll', 'userenv.dll', 'version.dll', 'winhttp.dll', 'wininet.dll', 'winmm.dll', 'wintrust.dll', 'wldap32.dll', 'ws2_32.dll', 'wtsapi32.dll')
    ($Name -in $system -or $Name -match '^(api-ms-win-|ext-ms-win-)[a-z0-9-]+\.dll$')
}
$executablePath = (Resolve-Path -LiteralPath $Executable).Path
$executableHash = (Get-FileHash -LiteralPath $executablePath -Algorithm SHA256).Hash.ToLowerInvariant()
$nativeFiles = [ordered]@{ 'sen.exe' = $executablePath; 'sencode.exe' = $executablePath }
$nativeFiles['sencode-launcher.exe'] = (Resolve-Path -LiteralPath $Launcher).Path
$managedRuntimes = @()
$runtimeNotices = [ordered]@{}
$searchPin = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'ripgrep.lock.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $SearchToolManifest) { $SearchToolManifest = Join-Path $projectRoot ('target/search-tool-' + $searchPin.version + '/search-tool-input.json') }
if (-not (Test-Path -LiteralPath $SearchToolManifest -PathType Leaf)) { throw 'Prepare pinned ripgrep with scripts/prepare-search-tool.ps1, then pass -SearchToolManifest. Packaging is offline.' }
$searchInput = Get-Content -LiteralPath $SearchToolManifest -Raw -Encoding UTF8 | ConvertFrom-Json
if ($searchInput.schema -ne 1 -or $searchInput.name -cne $searchPin.name -or $searchInput.version -cne $searchPin.version -or
    $searchInput.target -cne $searchPin.target -or $searchInput.archive_url -cne $searchPin.archive_url -or $searchInput.archive_sha256 -cne $searchPin.archive_sha256 -or
    @($searchInput.files).Count -ne @($searchPin.files).Count) { throw 'Search tool input does not match the upstream pin.' }
foreach ($expected in $searchPin.files) {
    $matches = @($searchInput.files | Where-Object { $_.name -ceq $expected.name -and $_.sha256 -ceq $expected.sha256 })
    if ($matches.Count -ne 1) { throw 'Missing, duplicate or unpinned search tool file.' }
    $item = Get-Item -LiteralPath $matches[0].source
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -gt 16777216 -or
        (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected.sha256) { throw 'Search tool payload differs from its pin.' }
    if ($expected.name -ceq 'rg.exe') { $nativeFiles[$expected.name] = $item.FullName }
    else { $runtimeNotices[$expected.name] = $item.FullName }
}
$nativeTools = @([ordered]@{name='ripgrep';version=$searchPin.version;target=$searchPin.target;executable='rg.exe';sha256=$searchPin.files[0].sha256;archive_url=$searchPin.archive_url;archive_sha256=$searchPin.archive_sha256;licenses=@($searchPin.files | Where-Object { $_.name -cne 'rg.exe' } | ForEach-Object { [ordered]@{name=$_.name;sha256=$_.sha256} })})
if ($ManagedRuntimeManifest) {
    $runtimeInput = Get-Content -LiteralPath $ManagedRuntimeManifest -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($runtimeInput.schema -ne 1) { throw 'Unsupported managed runtime input schema.' }
    $seenEngines = @{}
    foreach ($runtime in @($runtimeInput.managedRuntimes)) {
        $spec = switch -CaseSensitive ($runtime.engine) {
            'codex-app-server' { @{version='0.144.4'; protocol='0.144.4'; executable='codex-app-server.exe'} }
            'sencode-acp' { @{version='0.2.102'; protocol='1'; executable='sencode-agent.exe'} }
            default { throw 'Unsupported managed runtime engine.' }
        }
        if ($seenEngines.ContainsKey($runtime.engine) -or $runtime.runtime_version -cne $spec.version -or
            $runtime.protocol_version -cne $spec.protocol -or $runtime.executable -cne $spec.executable -or
            $runtime.sha256 -cnotmatch '^[a-f0-9]{64}$') { throw 'Managed runtime version, filename or checksum is not pinned.' }
        $seenEngines[$runtime.engine] = $true
        $source = Get-Item -LiteralPath $runtime.source
        $notice = Get-Item -LiteralPath $runtime.license
        foreach ($item in @($source, $notice)) {
            if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Managed runtime inputs must be ordinary files.' }
        }
        if ($source.Length -gt 536870912 -or $notice.Length -gt 1048576 -or
            (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $runtime.sha256) {
            throw 'Managed runtime input exceeds bounds or differs from its pinned checksum.'
        }
        $nativeFiles[$spec.executable] = $source.FullName
        $noticeName = $runtime.engine + '.LICENSE.txt'
        $runtimeNotices[$noticeName] = $notice.FullName
        $managedRuntimes += [ordered]@{engine=$runtime.engine;runtime_version=$spec.version;protocol_version=$spec.protocol;executable=$spec.executable;sha256=$runtime.sha256;license=$noticeName}
    }
}
foreach ($dll in $RuntimeDll) {
    $path = (Resolve-Path -LiteralPath $dll).Path
    $name = [IO.Path]::GetFileName($path).ToLowerInvariant()
    if ($name -cnotmatch '^[a-z0-9][a-z0-9._-]*\.dll$' -or $nativeFiles.Contains($name) -or (Test-WindowsSystemDll $name)) {
        throw "Invalid, duplicate or Windows-owned runtime DLL: $name"
    }
    $nativeFiles[$name] = $path
}
$dependencyEvidence = @()
$needed = @{}
foreach ($name in $nativeFiles.Keys) {
    $item = Get-Item -LiteralPath $nativeFiles[$name]
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Not an ordinary native file: $name" }
    $imports = @(Get-PeImports $nativeFiles[$name])
    if ($name -eq 'sencode-launcher.exe' -and @($imports | Where-Object { $_ -ine 'kernel32.dll' }).Count -gt 0) {
        throw 'The command forwarder must import only Kernel32; its command directory has no application runtime DLLs.'
    }
    foreach ($dependency in $imports) {
        if (-not (Test-WindowsSystemDll $dependency)) {
            if (-not $nativeFiles.Contains($dependency)) {
                throw "Unbundled dependency $dependency imported by $name. Build with a static runtime or pass the redistributable DLL with -RuntimeDll."
            }
            $needed[$dependency] = $true
        }
    }
    $dependencyEvidence += [ordered]@{ file = $name; imports = @($imports) }
}
foreach ($name in $nativeFiles.Keys) {
    if ($name -like '*.dll' -and -not $needed.ContainsKey($name)) { throw "Unused runtime DLL supplied: $name" }
}
$manifestSource = Get-Content -LiteralPath (Join-Path $projectRoot 'Sengoo.toml') -Raw -Encoding UTF8
if ($manifestSource -notmatch '(?m)^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+(?:[A-Za-z0-9.+-]*)?)"\s*$') { throw 'Cannot determine the CLI package version.' }
$version = $Matches[1]
$sourceRevision = 'unavailable'
$dirty = $true
if (Get-Command git -ErrorAction SilentlyContinue) {
    $revision = & git -C $projectRoot rev-parse HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $revision -match '^[a-f0-9]{40}$') {
        $sourceRevision = $revision
        $status = & git -C $projectRoot status --porcelain --untracked-files=normal 2>$null
        $dirty = $LASTEXITCODE -ne 0 -or @($status).Count -ne 0
    }
}
$outputRoot = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
$name = "sencode-cli-$version-windows-x64"
$packageRoot = Join-Path $outputRoot $name
$archive = Join-Path $outputRoot ($name + '.zip')
if ((Test-Path -LiteralPath $packageRoot) -or (Test-Path -LiteralPath $archive)) { throw 'Output already exists. Select a new -OutputDirectory.' }
New-Item -ItemType Directory -Path $packageRoot | Out-Null
foreach ($file in $nativeFiles.Keys) { Copy-Item -LiteralPath $nativeFiles[$file] -Destination (Join-Path $packageRoot $file) }
foreach ($file in $runtimeNotices.Keys) { Copy-Item -LiteralPath $runtimeNotices[$file] -Destination (Join-Path $packageRoot $file) }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'install.ps1') -Destination (Join-Path $packageRoot 'install.ps1')
Copy-Item -LiteralPath (Join-Path $projectRoot 'docs/installation.md') -Destination (Join-Path $packageRoot 'installation.md')
Copy-Item -LiteralPath (Resolve-Path -LiteralPath $LicensePath).Path -Destination (Join-Path $packageRoot 'LICENSE.txt')
$files = @(Get-ChildItem -LiteralPath $packageRoot -File | Sort-Object Name | ForEach-Object {
    [ordered]@{ name = $_.Name; bytes = $_.Length; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
})
foreach ($alias in @('sen.exe', 'sencode.exe')) {
    if (@($files | Where-Object { $_.name -eq $alias -and $_.sha256 -ceq $executableHash }).Count -ne 1) {
        throw 'The source executable changed during packaging. Finish rebuilding and select a new output directory.'
    }
}
$manifest = [ordered]@{ schema = 1; product = 'sencode-cli'; version = $version; target = 'windows-x64'; source_revision = $sourceRevision; source_dirty = $dirty; created_utc = [DateTime]::UtcNow.ToString('o'); files = $files; native_dependencies = $dependencyEvidence; managedRuntimes = $managedRuntimes; nativeTools = $nativeTools }
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $packageRoot 'package-manifest.json') -Encoding UTF8
$checksumLines = @(Get-ChildItem -LiteralPath $packageRoot -File | Sort-Object Name | ForEach-Object {
    (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() + '  ' + $_.Name
})
$checksumLines | Set-Content -LiteralPath (Join-Path $packageRoot 'SHA256SUMS') -Encoding ASCII
Compress-Archive -LiteralPath @(Get-ChildItem -LiteralPath $packageRoot -File | Select-Object -ExpandProperty FullName) -DestinationPath $archive -CompressionLevel Optimal
$archiveHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
($archiveHash + '  ' + [IO.Path]::GetFileName($archive)) | Set-Content -LiteralPath ($archive + '.sha256') -Encoding ASCII
[pscustomobject]@{ package_directory = $packageRoot; archive = $archive; sha256 = $archiveHash; source_revision = $sourceRevision; source_dirty = $dirty }
