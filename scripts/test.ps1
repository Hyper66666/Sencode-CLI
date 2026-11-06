#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$SengooRoot = $env:SENGOO_ROOT,
    [string]$Python = $env:SENCODE_TEST_PYTHON,
    [switch]$NativeOnly,
    [ValidateSet('core','protocol','http','workspace','executor','scheduler','terminal','views','transport','consult','children','mcp','cli','tui','commands','tui_input','tui_markdown','edit_diff','tool_schedule','model_selection','fullscreen','state','sessions','checkpoint','references','diagnostics','engine','engine_control','managed','engine_host','managed_host','request_retry','context_compaction','request_recovery_host','pty_session','tui_keys','tui_reading','tui_keymap_file','tui_editor','pty_vt','terminal_pane','terminal_pane_console','jobs','background','worktree','worktree_cli','media_transport','provider_media','management','project_history','project_history_public','worktree_tui_console','responses_tools','questions','local_prompts','tui_pending','clipboard_attachment','image_request','connection_capability','tui_timeline','controller_recovery','agent_reliability','long_history_public','long_history_state','long_history_context','tui_modes','tui_agents','permissions','effort_default','workbench_controls','provider_activity','execution_diagnostics','turn_metrics','session_catalog','reading_experience','reading_console','responses_end_turn','session_public','tui_scroll','session_target','scroll_target','session_permissions','session_policy_wait','tui_turns')]
    [string[]]$Cases,
    [string]$EvidencePath,
    [ValidateSet('Debug','Release')][string]$Configuration = 'Debug',
    [switch]$UseBuiltCli,
    [string]$CliExecutable,
    [string]$CompilerExecutable,
    [switch]$UpdateLock
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $SengooRoot) {
    $SengooRoot = Join-Path (Split-Path $projectRoot -Parent) 'Sengoo'
}
$SengooRoot = (Resolve-Path -LiteralPath $SengooRoot).Path
$compiler = Join-Path $SengooRoot 'target/debug/sgc.exe'
if ($CompilerExecutable) { $compiler = (Resolve-Path -LiteralPath $CompilerExecutable).Path }
$nativeCases = @('core','protocol','http','workspace','executor','scheduler','terminal','views','commands','tui_input','tui_markdown','edit_diff','tool_schedule','model_selection','engine','managed','request_retry','context_compaction','tui_keys','tui_reading','tui_editor','pty_vt','provider_media','questions','local_prompts','tui_pending','clipboard_attachment','connection_capability','tui_timeline','tui_modes','tui_agents','provider_activity','execution_diagnostics','reading_experience','tui_scroll','tui_turns')
$integrationCases = @('transport','consult','children','mcp','cli','tui','fullscreen','state','sessions','checkpoint','references','diagnostics','engine_control','engine_host','managed_host','request_recovery_host','pty_session','tui_keymap_file','terminal_pane','terminal_pane_console','jobs','background','worktree','worktree_cli','media_transport','management','project_history','project_history_public','worktree_tui_console','responses_tools','image_request','controller_recovery','agent_reliability','long_history_public','long_history_state','long_history_context','permissions','effort_default','workbench_controls','turn_metrics','session_catalog','reading_console','responses_end_turn','session_public','session_target','scroll_target','session_permissions','session_policy_wait')
if (-not $Cases) { $Cases = if ($NativeOnly) { $nativeCases } else { $nativeCases + $integrationCases } }
if ($NativeOnly -and @($Cases | Where-Object { $_ -in $integrationCases }).Count) { throw '-NativeOnly cannot include an integration case.' }
if (@($Cases | Where-Object { $_ -in $integrationCases }).Count) {
    if (-not $Python -or -not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        throw 'Full acceptance requires an explicit working Python executable: -Python C:/path/to/python.exe (or SENCODE_TEST_PYTHON). Use -NativeOnly for the named native subset.'
    }
    $Python = (Resolve-Path -LiteralPath $Python).Path
    if ($Python -match '[\\/]Microsoft[\\/]WindowsApps[\\/]') { throw 'WindowsApps Python aliases are not an interpreter; provide the real executable.' }
}
$env:SENGOO_STDLIB = Join-Path $SengooRoot 'tools/stdlib'
$env:SENGOO_RUNTIME = Join-Path $SengooRoot 'tools/stdlib/runtime.c'
$env:SENGOO_MODULE_MAP = 'sgsqlite=' + (Join-Path $SengooRoot 'packages/sgsqlite/src/lib.sg')
$logRoot = Join-Path $projectRoot ('target/acceptance/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
if (-not $EvidencePath) { $EvidencePath = Join-Path $logRoot 'evidence.json' }
$evidence = [ordered]@{
    schema = 1; started_at = [DateTime]::UtcNow.ToString('o'); host = $env:COMPUTERNAME
    platform = 'windows-x64'; scope = @($Cases); result = 'running'
    compiler_sha256 = (Get-FileHash -LiteralPath $compiler -Algorithm SHA256).Hash.ToLowerInvariant()
    revisions = [ordered]@{}; sources = @(); steps = @()
    foundation_sources = @()
}
foreach ($repository in @(@{name='sengoo';path=$SengooRoot},@{name='sencode';path=$projectRoot})) {
    $revision = (& git -C $repository.path rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot record the repository baseline.' }
    $evidence.revisions[$repository.name] = $revision
}
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $projectRoot 'src'),(Join-Path $projectRoot 'tests'),(Join-Path $projectRoot 'scripts') -File -Recurse | Where-Object { $_.Extension -in @('.sg','.py','.ps1','.c') }) {
    $evidence.sources += [ordered]@{path=$file.FullName.Substring($projectRoot.Length + 1);sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $SengooRoot 'tools/stdlib') -File | Where-Object { $_.Extension -in @('.sg','.c','.h') }) {
    $evidence.foundation_sources += [ordered]@{path=$file.FullName;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
function Invoke-AcceptanceStep {
    param([string]$Name,[string]$Command,[string[]]$Arguments)
    $log = Join-Path $logRoot ($Name + '.log')
    $started = [DateTime]::UtcNow
    & $Command @Arguments 2>&1 | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
    $evidence.steps += [ordered]@{name=$Name;exit_code=$code;seconds=([DateTime]::UtcNow-$started).TotalSeconds;log=$log;status=if($code -eq 0){'passed'}else{'failed'}}
    if ($code -ne 0) { throw "$Name failed with exit code $code; inspect $log" }
}
Push-Location $projectRoot
try {
    $builtCliPath = Join-Path $projectRoot 'target/sencode-sg.exe'
    $builtCli = [bool]$UseBuiltCli
    if ($CliExecutable) { $builtCliPath = (Resolve-Path -LiteralPath $CliExecutable).Path; $builtCli = $true }
    if ($builtCli -and -not (Test-Path -LiteralPath $builtCliPath -PathType Leaf)) { throw 'Built CLI executable does not exist.' }
    foreach ($case in $Cases) {
        if ($case -in @('cli','tui','fullscreen','engine_host','managed_host','request_recovery_host','terminal_pane_console','background','worktree_cli','management','project_history_public','worktree_tui_console','responses_tools','agent_reliability','long_history_public','workbench_controls','reading_console','responses_end_turn','session_public','scroll_target','session_policy_wait')) {
            if (-not $builtCli) { & ./scripts/build.ps1 -SengooRoot $SengooRoot -Configuration $Configuration -UpdateLock:$UpdateLock; $builtCli = $true }
            $candidateHash = (Get-FileHash -LiteralPath $builtCliPath -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($evidence.Contains('cli_sha256') -and $evidence.cli_sha256 -ne $candidateHash) { throw 'CLI changed during acceptance; rerun against one candidate.' }
            $evidence['cli_sha256'] = $candidateHash
            if ($case -eq 'cli') { Invoke-AcceptanceStep 'cli-external' $Python @('tests/cli_fixture.py',$builtCliPath) }
            elseif ($case -eq 'fullscreen') { Invoke-AcceptanceStep 'fullscreen-console' $Python @('tests/fullscreen_console_fixture.py',$builtCliPath,'--production','--evidence',(Join-Path $logRoot 'fullscreen.json')) }
            elseif ($case -eq 'terminal_pane_console') { Invoke-AcceptanceStep 'terminal-pane-console' $Python @('tests/terminal_pane_console_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'terminal-pane.json')) }
            elseif ($case -eq 'background') { Invoke-AcceptanceStep 'background-public' $Python @('tests/background_public_fixture.py',$builtCliPath) }
            elseif ($case -eq 'worktree_cli') { Invoke-AcceptanceStep 'worktree-cli-public' $Python @('tests/worktree_cli_fixture.py',$builtCliPath) }
            elseif ($case -eq 'management') { Invoke-AcceptanceStep 'management-public' $Python @('tests/management_fixture.py',$builtCliPath) }
            elseif ($case -eq 'project_history_public') { Invoke-AcceptanceStep 'project-history-public' $Python @('tests/project_history_public_fixture.py',$builtCliPath) }
            elseif ($case -eq 'worktree_tui_console') { Invoke-AcceptanceStep 'worktree-tui-console' $Python @('tests/worktree_tui_console_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'worktree-tui.json')) }
            elseif ($case -eq 'session_policy_wait') { Invoke-AcceptanceStep 'session-policy-wait' $Python @('tests/session_policy_wait_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'session-policy-wait.json')) }
            elseif ($case -eq 'engine_host') { Invoke-AcceptanceStep 'engine-host' $Python @('tests/engine_fixture.py',$builtCliPath) }
            elseif ($case -eq 'request_recovery_host') { Invoke-AcceptanceStep 'request-recovery-host' $Python @('tests/request_recovery_fixture.py',$builtCliPath) }
            elseif ($case -eq 'responses_tools') { Invoke-AcceptanceStep 'responses-tool-continuation' $Python @('tests/responses_tool_continuation_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'responses-tools.json')) }
            elseif ($case -eq 'agent_reliability') { Invoke-AcceptanceStep 'agent-reliability' $Python @('tests/agent_reliability_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'agent-reliability.json')) }
            elseif ($case -eq 'long_history_public') { Invoke-AcceptanceStep 'long-history-public' $Python @('tests/long_history_public_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'long-history-public.json')) }
            elseif ($case -eq 'workbench_controls') { Invoke-AcceptanceStep 'workbench-controls' $Python @('tests/workbench_controls_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'workbench-controls.json')) }
            elseif ($case -eq 'reading_console') { Invoke-AcceptanceStep 'reading-console' $Python @('tests/reading_experience_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'reading-console.json')) }
            elseif ($case -eq 'responses_end_turn') { Invoke-AcceptanceStep 'responses-end-turn' $Python @('tests/responses_end_turn_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'responses-end-turn.json')) }
            elseif ($case -eq 'scroll_target') { Invoke-AcceptanceStep 'scroll-target-public' $Python @('tests/scroll_target_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'scroll-target.json')) }
            elseif ($case -eq 'session_public') { Invoke-AcceptanceStep 'session-public' $Python @('tests/session_public_fixture.py',$builtCliPath,'--evidence',(Join-Path $logRoot 'session-public.json')) }
            elseif ($case -eq 'managed_host') {
                Invoke-AcceptanceStep 'managed-fixture-build' $compiler @('--runtime-mode','source-development','build','src/managed_fixture.sg','--force-rebuild','-O','0','-o','target/managed_fixture.exe')
                Invoke-AcceptanceStep 'managed-host' $Python @('tests/managed_fixture.py',$builtCliPath,'target/managed_fixture.exe')
            }
            else { Invoke-AcceptanceStep 'tui-console' $Python @('tests/tui_console_fixture.py',$builtCliPath,'--scrolling') }
            $evidence['cli_sha256'] = (Get-FileHash -LiteralPath $builtCliPath -Algorithm SHA256).Hash.ToLowerInvariant()
            continue
        }
        $source = if ($case -eq 'session_catalog') { 'src/session_catalog_probe.sg' } elseif ($case -eq 'project_history') { 'src/project_history_probe.sg' } else { "src/tests_$case.sg" }
        $binary = "target/tests_$case.exe"
        Invoke-AcceptanceStep "$case-build" $compiler @('--runtime-mode','source-development','build',$source,'--force-rebuild','-O','0','-o',$binary)
        if ($case -eq 'references') {
            $referenceRoot = Join-Path $logRoot 'reference-workspace'
            New-Item -ItemType Directory -Path $referenceRoot | Out-Null
            Invoke-AcceptanceStep 'references-native' (Join-Path $projectRoot $binary) @('--cwd',$referenceRoot)
        } elseif ($case -in @('state','sessions','checkpoint','diagnostics','engine_control','terminal_pane','jobs','local_prompts','connection_capability','effort_default','turn_metrics','session_target','session_permissions')) {
            Invoke-AcceptanceStep "$case-native" (Join-Path $projectRoot $binary) @('--database',(Join-Path $logRoot "$case.sqlite"))
        } elseif ($case -in $nativeCases) {
            Invoke-AcceptanceStep "$case-native" (Join-Path $projectRoot $binary) @()
        } elseif ($case -eq 'pty_session') {
            Invoke-AcceptanceStep 'pty-session' $Python @('tests/pty_session_fixture.py',$binary)
        } elseif ($case -eq 'worktree') {
            Invoke-AcceptanceStep 'worktree' $Python @('tests/worktree_fixture.py',$binary)
        } elseif ($case -eq 'session_catalog') {
            Invoke-AcceptanceStep 'session-catalog' $Python @('tests/session_catalog_fixture.py',$binary,'--evidence',(Join-Path $logRoot 'session-catalog.json'))
        } elseif ($case -eq 'project_history') {
            Invoke-AcceptanceStep 'project-history' $Python @('tests/project_history_fixture.py',$binary)
        } elseif ($case -in @('long_history_state','long_history_context')) {
            Invoke-AcceptanceStep "$case-fixture" $Python @('tests/long_history_fixture.py',$binary)
        } elseif ($case -eq 'permissions') {
            Invoke-AcceptanceStep 'permissions-fixture' $Python @('tests/permissions_fixture.py',$binary,'--evidence',(Join-Path $logRoot 'permissions.json'))
        } elseif ($case -eq 'tui_keymap_file') {
            Invoke-AcceptanceStep 'tui-keymap-file' $Python @('tests/keymap_fixture.py',$binary,'--evidence',(Join-Path $logRoot 'keymap.json'))
        } elseif ($case -eq 'mcp') {
            Invoke-AcceptanceStep 'mcp-stdio' (Join-Path $projectRoot $binary) @($Python,(Join-Path $projectRoot 'tests/mcp_fixture.py'))
        } else {
            $fixture = if ($case -eq 'transport') { 'provider_fixture.py' } else { "${case}_fixture.py" }
            Invoke-AcceptanceStep "$case-fixture" $Python @("tests/$fixture",$binary)
        }
    }
    $currentCompiler = (Get-FileHash -LiteralPath $compiler -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($currentCompiler -ne $evidence.compiler_sha256) { throw 'Compiler changed during acceptance; rerun against one candidate.' }
    if ($evidence.Contains('cli_sha256') -and (Get-FileHash -LiteralPath $builtCliPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $evidence.cli_sha256) { throw 'CLI changed during acceptance; rerun against one candidate.' }
    foreach ($source in $evidence.sources) {
        $currentSource = (Get-FileHash -LiteralPath (Join-Path $projectRoot $source.path) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($currentSource -ne $source.sha256) { throw ('Source changed during acceptance: ' + $source.path + '; rerun against one candidate.') }
    }
    foreach ($source in $evidence.foundation_sources) {
        if ((Get-FileHash -LiteralPath $source.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $source.sha256) { throw ('Sengoo foundation changed during acceptance: ' + $source.path) }
    }
    $evidence.result = 'passed'
} catch {
    $evidence.result = 'failed'
    $evidence['error'] = $_.Exception.Message
    throw
} finally {
    Pop-Location
    $evidence['finished_at'] = [DateTime]::UtcNow.ToString('o')
    $parentDirectory = Split-Path $EvidencePath -Parent
    if ($parentDirectory) { New-Item -ItemType Directory -Force -Path $parentDirectory | Out-Null }
    $evidence | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
    Write-Host "Acceptance evidence: $EvidencePath"
}
