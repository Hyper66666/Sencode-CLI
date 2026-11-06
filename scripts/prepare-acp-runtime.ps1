#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$RuntimeRoot = (Join-Path $PSScriptRoot '../../sencode/windows/sencode-runtime'),
    [string]$Executable,
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '../target/managed-sencode-0.2.102')
)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$runtime = (Resolve-Path -LiteralPath $RuntimeRoot).Path
if (-not $Executable) { $Executable = Join-Path $runtime 'target/debug/sencode-agent.exe' }
$pinPath = Join-Path $project 'runtime-manifests/sencode-runtime.json'
$pin = Get-Content -LiteralPath $pinPath -Raw | ConvertFrom-Json
if ($pin.sourceVersion -cne '0.2.102' -or $pin.binaryName -cne 'sencode-agent.exe') { throw 'Unexpected desktop ACP source pin.' }
$image = Get-Item -LiteralPath $Executable
if ($image.PSIsContainer -or ($image.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'ACP input must be a regular executable.' }
$reported = (& $image.FullName --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $reported -notmatch '^sencode 0\.2\.102 \([a-f0-9]+\)$') { throw "ACP version does not match the desktop source pin: $reported" }
$directory = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $directory | Out-Null
$output = Join-Path $directory 'sencode-agent.exe'
Copy-Item -LiteralPath $image.FullName -Destination $output -Force
$hash = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant()
$license = Join-Path $directory 'upstream-license.txt'
Copy-Item -LiteralPath (Join-Path $runtime 'LICENSE') -Destination $license -Force
$revision = (& git -C $runtime rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $revision -notmatch '^[a-f0-9]{40}$') { throw 'Cannot capture runtime source revision.' }
$dirty = @(& git -C $runtime status --porcelain=v1 --untracked-files=normal)
$provenance = [ordered]@{
    schema=1;engine='sencode-acp';runtime_version='0.2.102';protocol_version='1'
    source_revision=$revision;working_tree_dirty=($dirty.Count -gt 0)
    build_kind='local source build; not the historical published binary'
    executable_sha256=$hash;executable_size=(Get-Item -LiteralPath $output).Length
    cargo_lock_sha256=(Get-FileHash -LiteralPath (Join-Path $runtime 'Cargo.lock') -Algorithm SHA256).Hash.ToLowerInvariant()
    desktop_pin_sha256=(Get-FileHash -LiteralPath $pinPath -Algorithm SHA256).Hash.ToLowerInvariant()
    build_environment=[ordered]@{SENCODE_VERSION='0.2.102';profile='debug';features=@('desktop-embedded');linker='rust-lld';debug_info='none at final link';stack_bytes=16777216}
    qualification='version and local source provenance only; initialize and live account calls are separate gates'
}
$provenance | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $directory 'provenance.json') -Encoding UTF8
$input = [ordered]@{schema=1;managedRuntimes=@([ordered]@{engine='sencode-acp';runtime_version='0.2.102';protocol_version='1';executable='sencode-agent.exe';sha256=$hash;source=$output;license=$license})}
$inputPath = Join-Path $directory 'packaging-input.json'
$input | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $inputPath -Encoding UTF8
[pscustomobject]@{packaging_input=$inputPath;executable=$output;sha256=$hash}
