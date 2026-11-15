<#
Run on the Windows PC that owns the Steam installation.
Reads build information and copies three reference DLLs to the user's Linux server,
then opens loopback-only SSH tunnels. Does not change saves or install a game mod.
Example: .\Connect-Windows.ps1 -Server user@server -RemoteRoot /srv/Spire2Lab -SshPort 22
Use -GameBridgePort to match the port in the installed mod's STS2_MCP.conf.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.@:\[\]-]+$')][string]$Server,
    [Parameter(Mandatory=$true)][ValidatePattern('^/[a-zA-Z0-9_][a-zA-Z0-9_./-]*$')][string]$RemoteRoot,
    [ValidateRange(1,65535)][int]$SshPort = 22,
    [ValidateRange(1,65535)][int]$GameBridgePort = 15526,
    [string]$GameDir = '',
    [switch]$SkipAssemblyCopy
)
$ErrorActionPreference = 'Stop'
if ($Server.StartsWith('-')) { throw 'Server must be an SSH hostname or user@hostname.' }
if ($GameBridgePort -eq 8765) { throw 'GameBridgePort 8765 conflicts with the local dashboard tunnel. Choose another game bridge port.' }
$RemoteRoot = $RemoteRoot.TrimEnd('/')
foreach ($Tool in @('ssh','scp')) { if (-not (Get-Command $Tool -ErrorAction SilentlyContinue)) { throw "Windows OpenSSH client is required: $Tool was not found." } }

if (-not $GameDir) {
    $SteamRoots = @()
    foreach ($RegistryPath in @('HKCU:\Software\Valve\Steam','HKLM:\SOFTWARE\WOW6432Node\Valve\Steam')) {
        if (Test-Path $RegistryPath) {
            $Props = Get-ItemProperty $RegistryPath
            if ($Props.SteamPath) { $SteamRoots += $Props.SteamPath }
            if ($Props.InstallPath) { $SteamRoots += $Props.InstallPath }
        }
    }
    $SteamRoots += "${env:ProgramFiles(x86)}\Steam"
    $Libraries = @($SteamRoots)
    foreach ($Root in $SteamRoots) {
        $Vdf = Join-Path $Root 'steamapps\libraryfolders.vdf'
        if (Test-Path $Vdf) {
            $Text = Get-Content -Raw $Vdf
            foreach ($Match in [regex]::Matches($Text, '"path"\s+"([^"]+)"')) {
                $Libraries += $Match.Groups[1].Value.Replace('\\','\')
            }
        }
    }
    foreach ($Library in ($Libraries | Select-Object -Unique)) {
        $Candidate = Join-Path $Library 'steamapps\common\Slay the Spire 2'
        if (Test-Path (Join-Path $Candidate 'data_sts2_windows_x86_64\sts2.dll')) { $GameDir = $Candidate; break }
    }
}
if (-not $GameDir) { throw 'Game installation was not found. Run again with -GameDir "D:\SteamLibrary\steamapps\common\Slay the Spire 2".' }
$DataDir = Join-Path $GameDir 'data_sts2_windows_x86_64'
$Files = @('sts2.dll','GodotSharp.dll','0Harmony.dll')
$Hashes = @{}
foreach ($Name in $Files) {
    $Path = Join-Path $DataDir $Name
    if (-not (Test-Path $Path)) { throw "Required game reference is missing: $Path" }
    $Item = Get-Item $Path
    $Hashes[$Name] = @{ sha256=(Get-FileHash $Path -Algorithm SHA256).Hash.ToLower(); bytes=$Item.Length; file_version=$Item.VersionInfo.FileVersion; product_version=$Item.VersionInfo.ProductVersion }
}
$SteamApps = Split-Path (Split-Path $GameDir -Parent) -Parent
$ManifestPath = Join-Path $SteamApps 'appmanifest_2868840.acf'
$BuildId = $null
$BetaKey = $null
if (Test-Path $ManifestPath) {
    $Manifest = Get-Content -Raw $ManifestPath
    $Match = [regex]::Match($Manifest, '"buildid"\s+"([^"]+)"')
    if ($Match.Success) { $BuildId = $Match.Groups[1].Value }
    $Match = [regex]::Match($Manifest, '"BetaKey"\s+"([^"]+)"')
    if ($Match.Success) { $BetaKey = $Match.Groups[1].Value }
}
$Report = @{ captured_at=[DateTime]::UtcNow.ToString('o'); game_dir=$GameDir; steam_app_id='2868840'; steam_build_id=$BuildId; beta_key=$BetaKey; assemblies=$Hashes; target_game_version='0.107.1'; version_match='requires_verification' }
$ReportFile = Join-Path $env:TEMP 'sts2-lab-windows-report.json'
$Report | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $ReportFile
Write-Host "Game installation: $GameDir"
Write-Host "Steam build: $BuildId; local version report: $ReportFile"
Write-Host 'Checking SSH access and the remote checkout before uploading files.'
$RemoteCheck = "if ! test -f '$RemoteRoot/pyproject.toml' || ! test -f '$RemoteRoot/scripts/build_bridge.py'; then echo 'Spire2Lab checkout files are missing.' >&2; exit 20; fi; if ! mkdir -p '$RemoteRoot/artifacts/windows/assemblies'; then echo 'Spire2Lab reference directory could not be created.' >&2; exit 21; fi"
& ssh -T -p $SshPort $Server $RemoteCheck
$SetupExit = $LASTEXITCODE
if ($SetupExit -eq 255) {
    throw "SSH failed (exit 255); no files were uploaded. The local report is preserved at $ReportFile. Diagnose the connection with: ssh -vvv -E spire2lab-ssh.log -T -p $SshPort $Server 'echo SPIRE2LAB_SSH_OK'"
}
if ($SetupExit -eq 20) {
    throw "Remote checkout files are missing (exit 20). Check -RemoteRoot '$RemoteRoot'; it must contain pyproject.toml and scripts/build_bridge.py. No files were uploaded."
}
if ($SetupExit -eq 21) {
    throw "Remote reference directory could not be created (exit 21). Check write access under '$RemoteRoot/artifacts/windows'. No files were uploaded."
}
if ($SetupExit -ne 0) {
    throw "Remote preflight failed (exit $SetupExit). Inspect the SSH output above; no files were uploaded. Local report: $ReportFile"
}
Write-Host 'Remote checkout ready; uploading version evidence.'
& scp -P $SshPort $ReportFile "${Server}:$RemoteRoot/artifacts/windows/report.json"
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic upload failed.' }
if (-not $SkipAssemblyCopy) {
    foreach ($Name in $Files) {
        & scp -P $SshPort (Join-Path $DataDir $Name) "${Server}:$RemoteRoot/artifacts/windows/assemblies/$Name"
        if ($LASTEXITCODE -ne 0) { throw "Reference upload failed: $Name" }
    }
}
Write-Host ''
Write-Host 'Keep this window open. Dashboard: http://127.0.0.1:8765'
Write-Host 'The game bridge will be available on the server at 127.0.0.1:18526 after the mod is installed.'
Write-Host "Forwarding to Windows 127.0.0.1:$GameBridgePort. The port in STS2_MCP.conf must match; this script does not change it."
Write-Host 'Press Ctrl+C to close the tunnel. Game saves have not been changed.'
& ssh -N -p $SshPort -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L '127.0.0.1:8765:127.0.0.1:8765' -R "127.0.0.1:18526:127.0.0.1:$GameBridgePort" $Server
if ($LASTEXITCODE -ne 0) { throw 'SSH tunnel ended with an error; inspect the SSH message above.' }
