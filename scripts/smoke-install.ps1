#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PackageDirectory,
    [string]$EvidencePath,
    [switch]$Keep
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$packageRoot = (Resolve-Path -LiteralPath $PackageDirectory).Path
$userPathBefore = [Environment]::GetEnvironmentVariable('Path', 'User')
$processPathBefore = $env:Path
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('sencode-install-' + [Guid]::NewGuid().ToString('N'))
$unicodeDirectory = ([string][char]0x5de5) + ([string][char]0x4f5c) + ' project'
$prefix = Join-Path $scratch ('installed % ! CLI ' + $unicodeDirectory)
$workspace = Join-Path $scratch $unicodeDirectory
$bare = Join-Path $scratch 'executables only'
$commands = Join-Path $scratch 'existing user commands'
foreach ($directory in @($scratch, $workspace, $bare, $commands, (Join-Path $scratch 'profile'), (Join-Path $scratch 'local'), (Join-Path $scratch 'roaming'))) {
    New-Item -ItemType Directory -Path $directory | Out-Null
}

# PowerShell 5.1 uses ProcessStartInfo.Arguments. Apply the Windows CRT quoting
# rules ourselves so empty arguments, quotes and trailing slashes survive.
function ConvertTo-WindowsArgument([AllowEmptyString()][string]$Value) {
    if ($Value.IndexOf([char]0) -ge 0) { throw 'NUL is not a valid Windows argument.' }
    $result = [Text.StringBuilder]::new()
    [void]$result.Append('"')
    $slashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') { $slashes++; continue }
        if ($character -eq '"') {
            [void]$result.Append(('\' * ($slashes * 2 + 1)))
        } else { [void]$result.Append(('\' * $slashes)) }
        $slashes = 0
        [void]$result.Append($character)
    }
    [void]$result.Append(('\' * ($slashes * 2)))
    [void]$result.Append('"')
    $result.ToString()
}
function Invoke-InstalledCli([string]$ExecutablePath, [string[]]$Arguments, [int]$ExpectedExit,
    [AllowNull()][string]$InputText = $null, [switch]$CommandLookup) {
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $ExecutablePath
    $start.Arguments = (@($Arguments | ForEach-Object { ConvertTo-WindowsArgument $_ }) -join ' ')
    if ($CommandLookup) {
        # Use a bare alias in CMD with a pre-existing PATH entry. Deliberately
        # omit the new install bin so this cannot pass by refreshed PATH.
        if ($ExecutablePath -notin @('sen', 'sencode')) { throw 'Unexpected lookup alias.' }
        $start.FileName = Join-Path $env:SystemRoot 'System32/cmd.exe'
        $start.Arguments = '/d /s /c "' + $ExecutablePath + ' ' + $start.Arguments + '"'
    }
    $start.WorkingDirectory = $workspace
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.RedirectStandardInput = $true
    $start.StandardOutputEncoding = [Text.Encoding]::UTF8
    $start.StandardErrorEncoding = [Text.Encoding]::UTF8
    $start.EnvironmentVariables.Clear()
    $start.EnvironmentVariables['SystemRoot'] = $env:SystemRoot
    $start.EnvironmentVariables['WINDIR'] = $env:SystemRoot
    $start.EnvironmentVariables['PATH'] = Join-Path $env:SystemRoot 'System32'
    if ($CommandLookup) { $start.EnvironmentVariables['PATH'] += ';' + $commands }
    $start.EnvironmentVariables['COMSPEC'] = Join-Path $env:SystemRoot 'System32/cmd.exe'
    $start.EnvironmentVariables['TEMP'] = $scratch
    $start.EnvironmentVariables['TMP'] = $scratch
    $start.EnvironmentVariables['USERPROFILE'] = Join-Path $scratch 'profile'
    $start.EnvironmentVariables['LOCALAPPDATA'] = Join-Path $scratch 'local'
    $start.EnvironmentVariables['APPDATA'] = Join-Path $scratch 'roaming'
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $start
    try {
        if (-not $process.Start()) { throw 'Unable to start installed CLI.' }
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if ($null -ne $InputText) { $process.StandardInput.Write($InputText) }
        $process.StandardInput.Close()
        if (-not $process.WaitForExit(30000)) { $process.Kill(); throw 'Installed CLI timed out.' }
        $output = $stdout.GetAwaiter().GetResult()
        $errorOutput = $stderr.GetAwaiter().GetResult()
        if ($process.ExitCode -ne $ExpectedExit) {
            throw "Installed command failed: $ExecutablePath $($start.Arguments); exit=$($process.ExitCode), expected=$ExpectedExit; stderr=$errorOutput; stdout=$output"
        }
        [pscustomobject]@{ stdout = $output; stderr = $errorOutput; exit_code = $process.ExitCode }
    } finally { $process.Dispose() }
}
function Remove-SmokeDirectory([string]$Directory) {
    $root = [IO.Path]::GetFullPath($Directory).TrimEnd('\')
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
    if (-not $root.StartsWith($tempRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetFileName($root) -notmatch '^sencode-install-[a-f0-9]{32}$') { throw 'Unsafe smoke cleanup root.' }
    $link = Join-Path $commands '.sencode-cli-bin'
    if (Test-Path -LiteralPath $link) {
        $item = Get-Item -LiteralPath $link
        if ($item.LinkType -ne 'Junction' -or @($item.Target).Count -ne 1 -or
            [IO.Path]::GetFullPath([string](@($item.Target)[0])).TrimEnd('\') -ine (Join-Path $prefix 'bin')) {
            throw 'Unexpected smoke command junction.'
        }
        # Unlink the verified junction itself, never traverse its target.
        [IO.Directory]::Delete($link)
    }
    $inventory = @(Get-ChildItem -LiteralPath $root -Force -Recurse)
    foreach ($entry in $inventory) {
        if (-not $entry.FullName.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase) -or
            ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unsafe smoke cleanup entry.' }
    }
    foreach ($entry in @($inventory | Where-Object { -not $_.PSIsContainer })) { Remove-Item -LiteralPath $entry.FullName -Force }
    foreach ($entry in @($inventory | Where-Object PSIsContainer | Sort-Object { $_.FullName.Length } -Descending)) {
        if (@(Get-ChildItem -LiteralPath $entry.FullName -Force).Count -eq 0) { Remove-Item -LiteralPath $entry.FullName }
    }
    if (@(Get-ChildItem -LiteralPath $root -Force).Count -eq 0) { Remove-Item -LiteralPath $root }
}
$checks = [Collections.Generic.List[object]]::new()
try {
    $installation = & (Join-Path $packageRoot 'install.ps1') -PackageDirectory $packageRoot -Prefix $prefix -NoPath -CommandDirectory $commands
    if ($installation.path_changed) { throw 'Temporary installation unexpectedly changed PATH.' }
    $manifest = Get-Content -LiteralPath (Join-Path $packageRoot 'package-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $unicodeArgument = ([string][char]0x53c2) + ([string][char]0x6570) + ' with spaces'
    $expectedArguments = @($unicodeArgument, 'literal"quote', 'tail\', '', '--looks-like-an-option')
    $referenceHelp = $null
    $referenceVersion = $null
    foreach ($alias in @('sen.exe', 'sencode.exe')) {
        $installed = Join-Path $installation.bin $alias
        if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath (Join-Path $packageRoot $alias) -Algorithm SHA256).Hash) {
            throw "Installed executable changed: $alias"
        }
        $help = Invoke-InstalledCli $installed @('--help') 0
        $version = Invoke-InstalledCli $installed @('--version') 0
        if ($help.stdout -notmatch 'sen' -or $help.stdout -notmatch 'resume' -or $version.stdout -notmatch [regex]::Escape($manifest.version)) {
            throw "Missing product help/version: $alias"
        }
        if ($null -ne $referenceHelp -and ($referenceHelp -cne $help.stdout -or $referenceVersion -cne $version.stdout)) {
            throw 'Installed aliases have different behavior.'
        }
        $referenceHelp = $help.stdout
        $referenceVersion = $version.stdout
        $invalid = Invoke-InstalledCli $installed @('--definitely-unknown-smoke-option') 2
        $probe = Invoke-InstalledCli $installed (@('probe', '--') + $expectedArguments) 0
        $document = $probe.stdout | ConvertFrom-Json
        if ($document.schema -ne 1 -or $document.cwd.TrimEnd('\', '/') -ine $workspace.TrimEnd('\', '/')) { throw "Caller cwd was not preserved: $alias" }
        $actual = @($document.positionals)
        if ($actual.Count -ne $expectedArguments.Count) { throw "Argument count changed: $alias" }
        for ($index = 0; $index -lt $actual.Count; $index++) {
            if ($actual[$index] -cne $expectedArguments[$index]) { throw "Argument $index changed: $alias" }
        }
        $checks.Add([ordered]@{ alias = $alias; sha256 = (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant(); help = $true; version = $true; invalid_exit_2 = $true; unicode_cwd_and_argv = $true })
        $short = [IO.Path]::GetFileNameWithoutExtension($alias)
        # Shell-level quoting remains CMD's responsibility. Exercise a literal
        # quote through the native launcher's raw CreateProcess boundary, and
        # exercise balanced-quoted metacharacters through bare CMD lookup.
        $forwarded = Invoke-InstalledCli (Join-Path $commands $alias) (@('probe', '--') + $expectedArguments) 0
        $forwardedDocument = $forwarded.stdout | ConvertFrom-Json
        for ($index = 0; $index -lt $expectedArguments.Count; $index++) {
            if ($forwardedDocument.positionals[$index] -cne $expectedArguments[$index]) { throw "Native launcher changed argument $index : $short" }
        }
        $lookupArguments = @($unicodeArgument, 'tail\', '', '--looks-like-an-option', 'amp&pipe|caret^', 'bang!value', 'percent%literal', '(parentheses)')
        $lookedUp = Invoke-InstalledCli $short (@('probe', '--') + $lookupArguments) 0 $null -CommandLookup
        $lookupDocument = $lookedUp.stdout | ConvertFrom-Json
        if ($lookupDocument.cwd.TrimEnd('\', '/') -ine $workspace.TrimEnd('\', '/') -or
            @($lookupDocument.positionals).Count -ne $lookupArguments.Count) { throw 'Command lookup changed cwd or argument count.' }
        for ($index = 0; $index -lt $lookupArguments.Count; $index++) {
            if ($lookupDocument.positionals[$index] -cne $lookupArguments[$index]) { throw "Command lookup changed argument $index : $short" }
        }
        $null = Invoke-InstalledCli $short @('--definitely-unknown-smoke-option') 2 $null -CommandLookup
        $checks[$checks.Count - 1]['stale_path_command_lookup'] = $true
        Copy-Item -LiteralPath $installed -Destination (Join-Path $bare $alias)
    }
    # Run just the native files, with no package manifest, scripts or sources
    # adjacent. Explicitly bundled redistributables follow the executables.
    foreach ($dll in @(Get-ChildItem -LiteralPath $installation.bin -Filter '*.dll' -File)) {
        Copy-Item -LiteralPath $dll.FullName -Destination (Join-Path $bare $dll.Name)
    }
    Copy-Item -LiteralPath (Join-Path $installation.bin 'rg.exe') -Destination (Join-Path $bare 'rg.exe')
    foreach ($alias in @('sen.exe', 'sencode.exe')) {
        $null = Invoke-InstalledCli (Join-Path $bare $alias) @('--version') 0
        $null = Invoke-InstalledCli (Join-Path $bare $alias) (@('probe', '--') + $expectedArguments) 0
    }
    foreach ($directory in @($workspace, (Join-Path $scratch 'profile'), (Join-Path $scratch 'local'), (Join-Path $scratch 'roaming'))) {
        if (@(Get-ChildItem -LiteralPath $directory -Force).Count -ne 0) { throw "Read-only probes wrote state: $directory" }
    }
    # Exercise real application initialization from the executable-only folder.
    # This database is synthetic and explicit; no existing account/secret is read.
    $database = Join-Path $scratch 'synthetic-state.db'
    $doctor = Invoke-InstalledCli (Join-Path $bare 'sen.exe') @('doctor', '--database', $database) 0
    $report = $doctor.stdout | ConvertFrom-Json
    if (-not $report.ripgrep.available -or $report.ripgrep.source -cne 'bundled' -or
        $report.ripgrep.executable -ine (Join-Path $bare 'rg.exe')) { throw 'Offline executable-only ripgrep was not found.' }
    if ($report.schema -ne 1 -or $report.engine -ne 'sengoo' -or
        $report.cwd.TrimEnd('\', '/') -ine $workspace.TrimEnd('\', '/') -or
        @($report.connections).Count -ne 0 -or @($report.credentials).Count -ne 0) {
        throw 'Executable-only doctor did not initialize an isolated empty application state.'
    }
    # The no-argument application path uses only the isolated USERPROFILE.
    # /context verifies the fresh conversation through the product's own API,
    # avoiding Python, SQLite tools or direct state-file inspection.
    $session = $null
    foreach ($alias in @('sen.exe', 'sencode.exe')) {
        $application = Join-Path $bare $alias
        $started = Invoke-InstalledCli $application @() 0 "/context`n/quit`n"
        $fresh = $started.stdout | ConvertFrom-Json
        if ($null -eq $fresh.messages -or @($fresh.messages).Count -ne 0) { throw 'Fresh startup did not expose an empty context.' }
        # With no configured connection this headless request fails locally,
        # returning its new empty session identity without contacting a service.
        $unconfigured = Invoke-InstalledCli $application @('-p','installation empty fixture','--output-format','json') 1
        $session = ($unconfigured.stdout | ConvertFrom-Json).session_id
        if (-not $session) { throw 'New session has no identifier.' }
        # Empty sessions intentionally have no public recovery entry. Positive
        # history recovery is qualified separately by the same-candidate public
        # session/archive fixtures, without manufacturing an empty conversation.
        $recent = Invoke-InstalledCli $application @('resume') 1
        $specific = Invoke-InstalledCli $application @('resume', $session) 1
        if ($recent.stderr -notmatch 'Error code: 5' -or $specific.stderr -notmatch 'Error code: 5') { throw 'Empty resume did not report the expected missing-conversation diagnostic.' }
        $entry = $checks | Where-Object { $_.alias -eq $alias } | Select-Object -First 1
        $entry['no_argument_startup'] = $true
        $entry['empty_latest_resume_rejected'] = $true
        $entry['empty_specific_resume_rejected'] = $true
        $short = [IO.Path]::GetFileNameWithoutExtension($alias)
        $lookupStartup = Invoke-InstalledCli $short @() 0 "/context`n/quit`n" -CommandLookup
        $lookupContext = $lookupStartup.stdout | ConvertFrom-Json
        if ($null -eq $lookupContext.messages -or @($lookupContext.messages).Count -ne 0) { throw 'Bare command startup did not expose an empty context.' }
        $lookupLatest = Invoke-InstalledCli $short @('resume') 1 $null -CommandLookup
        $lookupSpecific = Invoke-InstalledCli $short @('resume', $session) 1 $null -CommandLookup
        if ($lookupLatest.stderr -notmatch 'Error code: 5' -or $lookupSpecific.stderr -notmatch 'Error code: 5') { throw 'Bare command empty recovery diagnostic changed.' }
        $entry['stale_path_no_argument_startup'] = $true
        $entry['stale_path_empty_latest_rejected'] = $true
        $entry['stale_path_empty_specific_rejected'] = $true
    }
    # A running native host must survive an atomic upgrade. Its old mapped
    # executable backup may remain busy, which must not report install failure.
    $liveStart = [Diagnostics.ProcessStartInfo]::new()
    $liveStart.FileName = Join-Path $installation.bin 'sen.exe'
    # Reuse this project's existing catalog; a different database would rightly
    # fail the portable-history dual-authority guard before the host is ready.
    $liveDatabase = Join-Path $scratch 'profile/.sencode/local-sessions.sqlite3'
    $liveStart.Arguments = (@('--cwd',$workspace,'--database',$liveDatabase,'--engine-stdio') | ForEach-Object { ConvertTo-WindowsArgument $_ }) -join ' '
    $liveStart.WorkingDirectory = $workspace
    $liveStart.UseShellExecute = $false; $liveStart.CreateNoWindow = $true
    $liveStart.RedirectStandardInput = $true; $liveStart.RedirectStandardOutput = $true; $liveStart.RedirectStandardError = $true
    $liveStart.EnvironmentVariables.Clear()
    foreach ($name in @('SystemRoot','WINDIR')) { $liveStart.EnvironmentVariables[$name] = $env:SystemRoot }
    $liveStart.EnvironmentVariables['PATH'] = Join-Path $env:SystemRoot 'System32'
    foreach ($name in @('TEMP','TMP')) { $liveStart.EnvironmentVariables[$name] = $scratch }
    $liveStart.EnvironmentVariables['USERPROFILE'] = Join-Path $scratch 'profile'
    $liveStart.EnvironmentVariables['LOCALAPPDATA'] = Join-Path $scratch 'local'
    $liveStart.EnvironmentVariables['APPDATA'] = Join-Path $scratch 'roaming'
    $live = [Diagnostics.Process]::new(); $live.StartInfo = $liveStart
    $liveStarted = $false; $deferredDuringRun = @()
    try {
        if (-not $live.Start()) { throw 'Could not start the owned live-upgrade host.' }; $liveStarted = $true
        $liveErrors = $live.StandardError.ReadToEndAsync()
        $readyLine = $live.StandardOutput.ReadLineAsync()
        if (-not $readyLine.Wait(15000)) { throw 'Live-upgrade host did not become ready within 15 seconds.' }
        if ([string]::IsNullOrEmpty($readyLine.Result)) {
            $detail = if ($live.HasExited) { $liveErrors.GetAwaiter().GetResult() } else { 'stdout closed' }
            throw "Live-upgrade host exited before ready: $detail"
        }
        if (($readyLine.Result | ConvertFrom-Json).type -ne 'ready') { throw 'Live-upgrade host sent an unexpected first event.' }
        $upgradedLive = & (Join-Path $packageRoot 'install.ps1') -PackageDirectory $packageRoot -Prefix $prefix -NoPath -CommandDirectory $commands
        $deferredDuringRun = @($upgradedLive.cleanup_deferred)
        if ($live.HasExited) { throw 'Upgrade interrupted a running host.' }
        foreach ($backup in $deferredDuringRun) {
            $absoluteBackup = [IO.Path]::GetFullPath($backup)
            if (-not $absoluteBackup.StartsWith($prefix + '\', [StringComparison]::OrdinalIgnoreCase) -or -not $absoluteBackup.EndsWith('.previous') -or -not (Test-Path -LiteralPath $absoluteBackup -PathType Leaf)) { throw 'Unexpected retained install backup.' }
        }
        $null = Invoke-InstalledCli (Join-Path $installation.bin 'sen.exe') @('--version') 0
        $live.StandardInput.WriteLine('{"type":"shutdown"}'); $live.StandardInput.Close()
        if (-not $live.WaitForExit(10000) -or $live.ExitCode -ne 0) { throw 'Upgraded old host could not exit normally.' }
    } finally {
        if ($liveStarted -and -not $live.HasExited) { $live.Kill(); $live.WaitForExit() }
        $live.Dispose()
    }
    foreach ($backup in $deferredDuringRun) { Remove-Item -LiteralPath $backup -Force }
    # A second install updates owned forwarders, while a foreign command or
    # a modified owned forwarder must fail before publishing the payload.
    $null = & (Join-Path $packageRoot 'install.ps1') -PackageDirectory $packageRoot -Prefix $prefix -NoPath -CommandDirectory $commands
    $collisionCommands = Join-Path $scratch 'foreign commands'
    New-Item -ItemType Directory -Path $collisionCommands | Out-Null
    [IO.File]::WriteAllText((Join-Path $collisionCommands 'sen.cmd'), '@echo foreign', [Text.Encoding]::ASCII)
    $collisionPrefix = Join-Path $scratch 'refused installation'
    $collisionRejected = $false
    try { $null = & (Join-Path $packageRoot 'install.ps1') -PackageDirectory $packageRoot -Prefix $collisionPrefix -NoPath -CommandDirectory $collisionCommands }
    catch { $collisionRejected = $true }
    if (-not $collisionRejected -or (Test-Path -LiteralPath $collisionPrefix)) { throw 'Foreign command collision did not stop before installation.' }
    $shimPath = Join-Path $commands 'sen.exe'
    $originalShim = [IO.File]::ReadAllBytes($shimPath)
    [IO.File]::AppendAllText($shimPath, 'rem changed', [Text.Encoding]::ASCII)
    $tamperRejected = $false
    try { $null = & (Join-Path $packageRoot 'install.ps1') -PackageDirectory $packageRoot -Prefix $prefix -NoPath -CommandDirectory $commands }
    catch { $tamperRejected = $true }
    [IO.File]::WriteAllBytes($shimPath, $originalShim)
    if (-not $tamperRejected) { throw 'Modified command forwarder was overwritten.' }
    $installedHash = (Get-FileHash -LiteralPath (Join-Path $installation.bin 'sen.exe') -Algorithm SHA256).Hash
    # Small malformed packages exercise search-tool checks before any publish.
    # Never mutate the candidate package or the already installed application.
    $badSearch = Join-Path $scratch 'bad-search-package'
    New-Item -ItemType Directory -Path $badSearch | Out-Null
    $badSearchManifest = Get-Content -LiteralPath (Join-Path $packageRoot 'package-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $badSearchManifest.managedRuntimes = @()
    $badSearchManifest.files = @($badSearchManifest.files | Where-Object { $_.name -ceq 'rg.exe' -or $_.name -clike 'ripgrep.*.txt' })
    foreach ($file in $badSearchManifest.files) { Copy-Item -LiteralPath (Join-Path $packageRoot $file.name) -Destination (Join-Path $badSearch $file.name) }
    $badRg = Join-Path $badSearch 'rg.exe'
    [IO.File]::AppendAllText($badRg, 'changed', [Text.Encoding]::ASCII)
    $badSearchManifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $badSearch 'package-manifest.json') -Encoding UTF8
    $searchChecksumRejected = $false
    try { $null = & (Join-Path $packageRoot 'install.ps1') -PackageDirectory $badSearch -Prefix $prefix -NoPath }
    catch { $searchChecksumRejected = $_.Exception.Message -like 'Checksum mismatch: rg.exe.*' }
    if (-not $searchChecksumRejected) { throw 'Modified ripgrep did not fail its payload checksum.' }
    # Changing the ordinary manifest checksum cannot bypass the upstream pin.
    ($badSearchManifest.files | Where-Object name -CEQ 'rg.exe').sha256 = (Get-FileHash -LiteralPath $badRg -Algorithm SHA256).Hash.ToLowerInvariant()
    $badSearchManifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $badSearch 'package-manifest.json') -Encoding UTF8
    $searchPinRejected = $false
    try { $null = & (Join-Path $packageRoot 'install.ps1') -PackageDirectory $badSearch -Prefix $prefix -NoPath }
    catch { $searchPinRejected = $_.Exception.Message -like 'Bundled ripgrep or its notices*' }
    if (-not $searchPinRejected -or (Get-FileHash -LiteralPath (Join-Path $installation.bin 'sen.exe') -Algorithm SHA256).Hash -cne $installedHash) { throw 'Modified search payload bypassed its pin or altered the installed CLI.' }
    $lockedAlias = [IO.File]::Open($shimPath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    $lockedAliasRejected = $false
    try {
        try { $null = & (Join-Path $packageRoot 'install.ps1') -PackageDirectory $packageRoot -Prefix $prefix -NoPath -CommandDirectory $commands }
        catch { $lockedAliasRejected = $true }
    } finally { $lockedAlias.Dispose() }
    if (-not $lockedAliasRejected -or (Get-FileHash -LiteralPath (Join-Path $installation.bin 'sen.exe') -Algorithm SHA256).Hash -cne $installedHash -or
        (Get-FileHash -LiteralPath $shimPath -Algorithm SHA256).Hash -cne (Get-FileHash -LiteralPath (Join-Path $packageRoot 'sencode-launcher.exe') -Algorithm SHA256).Hash) {
        throw 'A locked alias did not preserve the previous installation.'
    }
    $null = Invoke-InstalledCli 'sen' @('--version') 0 $null -CommandLookup
    if ([Environment]::GetEnvironmentVariable('Path', 'User') -cne $userPathBefore -or $env:Path -cne $processPathBefore) {
        throw 'Smoke installation modified the real user or process PATH.'
    }
    $evidence = [ordered]@{ schema = 1; host = 'windows-x64'; verified_utc = [DateTime]::UtcNow.ToString('o'); package_version = $manifest.version; source_revision = $manifest.source_revision; source_dirty = $manifest.source_dirty; checks = @($checks.ToArray()); running_image_upgrade = $true; retained_backups_during_run = $deferredDuringRun.Count; path_unchanged = $true; clean_environment_path = '%SystemRoot%\System32'; command_lookup_path = '%SystemRoot%\System32;existing user commands (install bin absent)'; unicode_and_batch_metacharacter_prefix = $true; owned_forwarder_update = $true; foreign_command_rejected = $collisionRejected; modified_forwarder_rejected = $tamperRejected; ripgrep_checksum_rejected = $searchChecksumRejected; ripgrep_pin_rejected = $searchPinRejected; locked_alias_rollback = $lockedAliasRejected; executable_only_directory = $true; read_only_probes_created_state = $false; isolated_doctor = $true; isolated_default_profile_and_resume = $true; limitation = 'This host still contains development tools and source checkouts. A fresh Windows VM installation and the pre-existing user console environment remain separate qualifications.' }
    $json = $evidence | ConvertTo-Json -Depth 8
    if ($EvidencePath) { $json | Set-Content -LiteralPath ([IO.Path]::GetFullPath($EvidencePath)) -Encoding UTF8 }
    $json
} finally {
    if ($Keep) { Write-Host "Smoke files retained: $scratch" }
    else { Remove-SmokeDirectory $scratch }
}
