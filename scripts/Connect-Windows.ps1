<#
Run on the Windows PC that owns the Steam installation.
Reads build information and copies three reference DLLs to the user's Linux server,
then opens loopback-only SSH tunnels. Does not change saves or install a game mod.
Example: .\Connect-Windows.ps1 -Server chenzk@my-server -SshPort 22
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.@:\[\]-]+$')][string]$Server,
    [ValidateRange(1,65535)][int]$SshPort = 22,
    [string]$GameDir = '',
    [switch]$SkipAssemblyCopy
)
$ErrorActionPreference = 'Stop'
if ($Server.StartsWith('-')) { throw 'Server must be an SSH hostname or user@hostname.' }
$RemoteRoot = '/user/chenzk/sts2-lab'
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
Write-Host "Steam build: $BuildId; sending reference hashes to your server."
& ssh -p $SshPort $Server "mkdir -p $RemoteRoot/artifacts/windows/assemblies"
if ($LASTEXITCODE -ne 0) { throw 'SSH setup failed.' }
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
Write-Host 'Press Ctrl+C to close the tunnel. Game saves have not been changed.'
& ssh -N -p $SshPort -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L '127.0.0.1:8765:127.0.0.1:8765' -R '127.0.0.1:18526:127.0.0.1:15526' $Server
if ($LASTEXITCODE -ne 0) { throw 'SSH tunnel ended with an error; inspect the SSH message above.' }
