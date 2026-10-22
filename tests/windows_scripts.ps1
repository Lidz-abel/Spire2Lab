<# Synthetic onboarding/installer checks. All SSH, SCP and Steam operations are mocked.
   Runs on PowerShell 7 on Linux or Windows; does not establish Windows compatibility. #>
param([string]$Root, [string]$Sandbox)
$ErrorActionPreference = 'Stop'
$env:TEMP = Join-Path $Sandbox 'temp'
$env:LOCALAPPDATA = Join-Path $Sandbox 'local'
$GameDir = Join-Path $Sandbox 'steamapps/common/Slay the Spire 2'
$DataDir = Join-Path $GameDir 'data_sts2_windows_x86_64'
$FakeRemote = Join-Path $Sandbox 'remote'
$global:SpireTestRemote = $FakeRemote
$global:SpireTestGameDir = $GameDir
foreach ($Directory in @($env:TEMP,$env:LOCALAPPDATA,$DataDir,$FakeRemote)) {
    New-Item -ItemType Directory -Force -Path $Directory | Out-Null
}
foreach ($Name in @('sts2.dll','GodotSharp.dll','0Harmony.dll')) {
    Set-Content -Path (Join-Path $DataDir $Name) -Value "synthetic reference $Name"
}
Set-Content -Path (Join-Path $Sandbox 'steamapps/appmanifest_2868840.acf') -Value '"buildid" "123456"'
$global:SpireTestCalls = [System.Collections.Generic.List[object]]::new()
$global:SpireTestSetupExit = 0
$global:SpireTestFailNextCopy = $false

function Assert-True($Condition, $Message) {
    if (-not $Condition) { throw $Message }
}
function Assert-Throws([scriptblock]$Action, [string]$MessagePart = '') {
    $Failed = $false
    try { & $Action } catch {
        $Failed = $true
        if ($MessagePart) {
            Assert-True ($_.Exception.Message.Contains($MessagePart)) "Wrong error: $($_.Exception.Message)"
        }
    }
    Assert-True $Failed 'Expected operation to fail.'
}
function global:ssh {
    $global:SpireTestCalls.Add(@{tool='ssh'; arguments=@($args)})
    $global:LASTEXITCODE = $global:SpireTestSetupExit
}
function global:scp {
    $global:SpireTestCalls.Add(@{tool='scp'; arguments=@($args)})
    $Source = [string]$args[-2]
    $Destination = [string]$args[-1]
    if ($Source.StartsWith('tester@host:')) {
        $Name = $Source.Split('/')[-1]
        Microsoft.PowerShell.Management\Copy-Item (Join-Path $global:SpireTestRemote $Name) $Destination -Force
    }
    $global:LASTEXITCODE = 0
}
function global:Get-Process { return $null }
function global:Start-Process { $global:SpireTestCalls.Add(@{tool='start'; arguments=@($args)}) }
function global:Copy-Item {
    param([string]$Path, [string]$Destination, [switch]$Recurse, [switch]$Force)
    if ($global:SpireTestFailNextCopy -and $Destination -eq (Join-Path $global:SpireTestGameDir 'mods/STS2_MCP/mod_manifest.json')) {
        $global:SpireTestFailNextCopy = $false
        throw 'Synthetic disk failure after first file was copied'
    }
    Microsoft.PowerShell.Management\Copy-Item @PSBoundParameters
}

$Connect = Join-Path $Root 'scripts/Connect-Windows.ps1'
$Install = Join-Path $Root 'scripts/Install-Windows-Mod.ps1'
$Options = @{Server='tester@host'; RemoteRoot='/srv/relocated/Spire2Lab'; SshPort=2222; GameDir=$GameDir}
& $Connect @Options
$Report = Get-Content -Raw (Join-Path $env:TEMP 'sts2-lab-windows-report.json') | ConvertFrom-Json
Assert-True ($Report.steam_build_id -eq '123456') 'Steam build missing from report'
Assert-True ($Report.assemblies.'sts2.dll'.sha256 -eq (Get-FileHash (Join-Path $DataDir 'sts2.dll')).Hash.ToLower()) 'Wrong reference hash'
Assert-True ($global:SpireTestCalls.Count -eq 6) 'Wrong number of connection operations'
Assert-True ($global:SpireTestCalls[0].arguments[-1].Contains("test -f '/srv/relocated/Spire2Lab/pyproject.toml'")) 'Remote checkout not checked'
$global:SpireTestCalls[0].arguments[-1] | Set-Content -Encoding UTF8 (Join-Path $Sandbox 'remote-check.txt')
foreach ($Call in @($global:SpireTestCalls | Where-Object tool -eq 'scp')) {
    Assert-True ($Call.arguments[-1].StartsWith('tester@host:/srv/relocated/Spire2Lab/artifacts/windows/')) 'Upload ignored RemoteRoot'
    Assert-True ($Call.arguments[1] -eq 2222) 'Upload ignored port'
}
Assert-True ($global:SpireTestCalls[-1].arguments -contains '127.0.0.1:18526:127.0.0.1:15526') 'Reverse tunnel must stay loopback only'

foreach ($Failure in @(
    @{code=255; message='SSH failed (exit 255)'},
    @{code=20; message='Remote checkout files are missing (exit 20)'},
    @{code=21; message='Remote reference directory could not be created (exit 21)'},
    @{code=1; message='Remote preflight failed (exit 1)'}
)) {
    $global:SpireTestCalls.Clear()
    $global:SpireTestSetupExit = $Failure.code
    Assert-Throws { & $Connect @Options } $Failure.message
    Assert-True ($global:SpireTestCalls.Count -eq 1) 'Failed preflight must not upload or open a tunnel'
    Assert-True (Test-Path (Join-Path $env:TEMP 'sts2-lab-windows-report.json')) 'SSH failure lost the local report'
}
$global:SpireTestSetupExit = 0
$global:SpireTestCalls.Clear()
$Bad = $Options.Clone()
$Bad.RemoteRoot = '/srv/repo;unexpected-command'
Assert-Throws { & $Connect @Bad }
Assert-True ($global:SpireTestCalls.Count -eq 0) 'Invalid path reached SSH'

$Target = Join-Path $GameDir 'mods/STS2_MCP'
New-Item -ItemType Directory -Force -Path $Target | Out-Null
Set-Content (Join-Path $Target 'STS2_MCP.dll') 'previous mod'
foreach ($Name in @('STS2_MCP.dll','mod_manifest.json','LICENSE.txt')) {
    Set-Content (Join-Path $FakeRemote $Name) "synthetic package $Name"
}
$Build = @{
    game_assembly_sha256='incorrect-game-hash'
    mod_sha256=(Get-FileHash (Join-Path $FakeRemote 'STS2_MCP.dll')).Hash.ToLower()
    manifest_sha256=(Get-FileHash (Join-Path $FakeRemote 'mod_manifest.json')).Hash.ToLower()
}
$Build | ConvertTo-Json | Set-Content (Join-Path $FakeRemote 'build.json')
Assert-Throws { & $Install @Options }
Assert-True ((Get-Content (Join-Path $Target 'STS2_MCP.dll')) -eq 'previous mod') 'Hash rejection modified installed mod'
Assert-True (@($global:SpireTestCalls | Where-Object tool -eq 'start').Count -eq 0) 'Hash rejection launched game'
$Build.game_assembly_sha256 = $Report.assemblies.'sts2.dll'.sha256
$Build | ConvertTo-Json | Set-Content (Join-Path $FakeRemote 'build.json')
& $Install @Options
foreach ($Name in @('STS2_MCP.dll','mod_manifest.json','LICENSE.txt','build.json')) {
    Assert-True ((Get-FileHash (Join-Path $Target $Name)).Hash -eq (Get-FileHash (Join-Path $FakeRemote $Name)).Hash) "Installation lost $Name"
}
Assert-True (@($global:SpireTestCalls | Where-Object tool -eq 'start').Count -eq 1) 'Successful installation did not launch Steam'
foreach ($Call in @($global:SpireTestCalls | Where-Object { $_.tool -eq 'scp' -and $_.arguments[-2].StartsWith('tester@host:') })) {
    Assert-True ($Call.arguments[-2].StartsWith('tester@host:/srv/relocated/Spire2Lab/artifacts/windows/mod/')) 'Download ignored RemoteRoot'
}

$Before = @{}
foreach ($Name in @('STS2_MCP.dll','mod_manifest.json','LICENSE.txt','build.json')) {
    $Before[$Name] = (Get-FileHash (Join-Path $Target $Name)).Hash
}
Set-Content (Join-Path $FakeRemote 'STS2_MCP.dll') 'changed package'
$Build.mod_sha256 = (Get-FileHash (Join-Path $FakeRemote 'STS2_MCP.dll')).Hash.ToLower()
$Build | ConvertTo-Json | Set-Content (Join-Path $FakeRemote 'build.json')
$global:SpireTestFailNextCopy = $true
Assert-Throws { & $Install @Options }
foreach ($Name in $Before.Keys) {
    Assert-True ((Get-FileHash (Join-Path $Target $Name)).Hash -eq $Before[$Name]) "Rollback did not restore $Name"
}
Assert-True (@($global:SpireTestCalls | Where-Object tool -eq 'start').Count -eq 1) 'Failed installation launched Steam'
Write-Output 'PASS: relocated checkout, SSH failure classification and local report retention, unsafe path, hash refusal, install provenance, rollback'
