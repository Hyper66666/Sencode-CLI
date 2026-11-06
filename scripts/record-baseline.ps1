#requires -Version 5.1
[CmdletBinding()]
param([string]$SengooRoot = 'D:/Sengoo', [string]$OutputPath)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$repositoryRoot = $projectRoot
if (-not $OutputPath) { $OutputPath = Join-Path $projectRoot 'target/fullscreen-baseline.json' }
$record = [ordered]@{schema=1; recorded_at=[DateTime]::UtcNow.ToString('o'); host=$env:COMPUTERNAME; reference='Claude Code reconstructed 2.1.88'; parity='Claude Code public local 2.1.318'; repositories=@()}
foreach ($entry in @(@{name='sengoo';root=$SengooRoot;prefix='^(compiler|runtime|tools|packages|openspec|docs)/'},@{name='sencode-cli';root=$repositoryRoot;prefix='^(src|scripts|tests|docs|shared-state|sencode-config|openspec|integrations)/'})) {
    $root = (Resolve-Path -LiteralPath $entry.root).Path
    $revision = (& git -C $root rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve repository revision.' }
    $status = @(& git -C $root status --porcelain=v1)
    $files = @(& git -C $root ls-files --cached --others --exclude-standard)
    $sources = @()
    foreach ($relative in ($files | Sort-Object -Unique)) {
        if ($relative -notmatch $entry.prefix -or $relative -match '(^|/)(target|node_modules|artifacts|dist|build|__pycache__)/') { continue }
        if ([IO.Path]::GetExtension($relative) -notin @('.sg','.rs','.c','.h','.toml','.json','.md','.yaml','.ps1','.py')) { continue }
        $path = Join-Path $root $relative
        if (Test-Path -LiteralPath $path -PathType Leaf) { $sources += [ordered]@{path=$relative;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()} }
    }
    $record.repositories += [ordered]@{name=$entry.name;root=$root;revision=$revision;status=$status;sources=$sources}
}
$parent = Split-Path $OutputPath -Parent
New-Item -ItemType Directory -Force -Path $parent | Out-Null
$record | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Host "Recorded baseline: $OutputPath"
