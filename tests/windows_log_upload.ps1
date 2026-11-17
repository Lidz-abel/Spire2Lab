param([string]$Root, [string]$Sandbox)
$ErrorActionPreference = 'Stop'
$global:SpireLogMockRoot = Join-Path $Sandbox 'remote'
$global:SpireLogMockBadHash = $false
$global:SpireLogMockFailCopy = $false
$LocalFolder = Join-Path $Sandbox 'local'
New-Item -ItemType Directory -Force $LocalFolder | Out-Null
$Source = Join-Path $LocalFolder 'godot.log'
Set-Content -LiteralPath $Source -Value 'synthetic startup log; no game involved'
function Assert-True($Condition, $Message) { if (-not $Condition) { throw $Message } }
function global:ssh {
    $global:LASTEXITCODE = 0
    $Command = [string]$args[-1]
    $Quoted = [regex]::Matches($Command, "'([^']+)'")
    $Destination = Join-Path $global:SpireLogMockRoot $Quoted[-1].Groups[1].Value.TrimStart('/')
    if ($Command.StartsWith('sha256sum')) {
        if ($global:SpireLogMockBadHash) { return ('0' * 64) + '  godot.log' }
        return (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant() + '  godot.log'
    }
    Assert-True (-not (Test-Path -LiteralPath $Destination)) 'Remote capture would overwrite an existing directory'
    New-Item -ItemType Directory -Force $Destination | Out-Null
}
function global:scp {
    $Destination = ([string]$args[-1] -split ':',2)[1].TrimStart('/')
    $Destination = Join-Path $global:SpireLogMockRoot $Destination
    Copy-Item -LiteralPath $args[-2] -Destination $Destination
    $global:LASTEXITCODE = 0
    if ($global:SpireLogMockFailCopy) { $global:LASTEXITCODE = 1 }
}
$Script = Join-Path $Root 'scripts/Upload-Windows-Logs.ps1'
$Options = @{ Server='user@example'; RemoteRoot='/project'; LogPath=$Source }
$Before = (Get-FileHash -LiteralPath $Source).Hash
& $Script @Options | Out-Null
& $Script @Options | Out-Null
$Copies = @(Get-ChildItem -Path $global:SpireLogMockRoot -Recurse -File)
Assert-True ($Copies.Count -eq 2) 'Repeated captures must preserve both server logs'
Assert-True (($Copies | Where-Object { (Get-FileHash -LiteralPath $_.FullName).Hash -ne $Before }).Count -eq 0) 'Uploaded content differs'
Assert-True (@(Get-ChildItem -LiteralPath $LocalFolder -File).Count -eq 1) 'Unexpected extra local log copy'
$global:SpireLogMockBadHash = $true
$Failed = $false
try { & $Script @Options | Out-Null } catch { $Failed = $_.Exception.Message.Contains('Checksum mismatch') }
Assert-True $Failed 'Corrupt remote content must not be reported verified'
Assert-True ((Get-FileHash -LiteralPath $Source).Hash -eq $Before) 'Source changed on verification failure'
$global:SpireLogMockBadHash = $false
$global:SpireLogMockFailCopy = $true
$Failed = $false
try { & $Script @Options | Out-Null } catch { $Failed = $_.Exception.Message.Contains('upload failed') }
Assert-True $Failed 'Transport failure must not be reported successful'
Assert-True ((Get-FileHash -LiteralPath $Source).Hash -eq $Before) 'Source removed on upload failure'
Assert-True (@(Get-ChildItem -Path $global:SpireLogMockRoot -Recurse -File).Count -eq 4) 'Failed evidence should remain on mock server'
'PASS: unique server captures, no local copies, checksum refusal, transfer failure preservation (mocked)'
