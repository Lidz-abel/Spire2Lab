<# Install the bridge compiled on Linux against this exact game's DLL fingerprint. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.@:\[\]-]+$')][string]$Server,
    [ValidateRange(1,65535)][int]$SshPort = 22,
    [string]$GameDir = ''
)
$ErrorActionPreference = 'Stop'
if ($Server.StartsWith('-')) { throw 'Invalid SSH server.' }
$ReportPath = Join-Path $env:TEMP 'sts2-lab-windows-report.json'
if (-not $GameDir) {
    if (-not (Test-Path $ReportPath)) { throw 'Run Connect-Windows.ps1 first or supply -GameDir.' }
    $GameDir = (Get-Content -Raw $ReportPath | ConvertFrom-Json).game_dir
}
if (Get-Process -Name 'SlayTheSpire2','Slay the Spire 2','sts2' -ErrorAction SilentlyContinue) { throw 'Close Slay the Spire 2 before installing the mod, then rerun this command.' }
$Stage = Join-Path $env:LOCALAPPDATA 'STS2Lab\mod-package'
New-Item -ItemType Directory -Force -Path $Stage | Out-Null
foreach ($Name in @('STS2_MCP.dll','mod_manifest.json','LICENSE.txt','build.json')) {
    & scp -P $SshPort "${Server}:/user/chenzk/sts2-lab/artifacts/windows/mod/$Name" (Join-Path $Stage $Name)
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $Name; the Linux mod build must finish first." }
}
$Build = Get-Content -Raw (Join-Path $Stage 'build.json') | ConvertFrom-Json
$ActualGameHash = (Get-FileHash (Join-Path $GameDir 'data_sts2_windows_x86_64\sts2.dll') -Algorithm SHA256).Hash.ToLower()
if ($ActualGameHash -ne $Build.game_assembly_sha256) { throw 'Game files changed after bridge compilation. Run Connect-Windows.ps1 again; do not install this build.' }
$ActualModHash = (Get-FileHash (Join-Path $Stage 'STS2_MCP.dll') -Algorithm SHA256).Hash.ToLower()
if ($ActualModHash -ne $Build.mod_sha256) { throw 'Downloaded mod checksum mismatch.' }
$ActualManifestHash = (Get-FileHash (Join-Path $Stage 'mod_manifest.json') -Algorithm SHA256).Hash.ToLower()
if ($ActualManifestHash -ne $Build.manifest_sha256) { throw 'Downloaded mod manifest checksum mismatch.' }
$Mods = Join-Path $GameDir 'mods'
New-Item -ItemType Directory -Force -Path $Mods | Out-Null
$Target = Join-Path $Mods 'STS2_MCP'
$Backup = Join-Path $env:LOCALAPPDATA ('STS2Lab\backups\' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
$Existing = Test-Path $Target
if ($Existing) { Copy-Item -Recurse $Target (Join-Path $Backup 'STS2_MCP') }
$LegacyNames = @('STS2_MCP.dll','STS2_MCP.json')
foreach ($Name in $LegacyNames) {
    if (Test-Path (Join-Path $Mods $Name)) { Copy-Item (Join-Path $Mods $Name) (Join-Path $Backup $Name) }
}
try {
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
    foreach ($Name in @('STS2_MCP.dll','mod_manifest.json')) {
        Copy-Item -Force (Join-Path $Stage $Name) (Join-Path $Target $Name)
    }
    foreach ($Name in $LegacyNames) {
        if (Test-Path (Join-Path $Mods $Name)) { Remove-Item (Join-Path $Mods $Name) }
    }
} catch {
    # Restore only the files managed by this installer. Keep other mod content intact.
    foreach ($Name in @('STS2_MCP.dll','mod_manifest.json')) {
        $Saved = Join-Path (Join-Path $Backup 'STS2_MCP') $Name
        if (Test-Path $Saved) { Copy-Item -Force $Saved (Join-Path $Target $Name) }
        elseif (Test-Path (Join-Path $Target $Name)) { Remove-Item (Join-Path $Target $Name) }
    }
    foreach ($Name in $LegacyNames) {
        if (Test-Path (Join-Path $Backup $Name)) { Copy-Item -Force (Join-Path $Backup $Name) (Join-Path $Mods $Name) }
    }
    throw
}
Write-Host "Installed bridge files in: $Target"
Write-Host "Previous files backed up at: $Backup"
Write-Host 'Launch the game through Steam and enable mods if the game asks for consent.'
Write-Host 'Keep Connect-Windows.ps1 running in the other terminal. Do not start an important saved run for reference capture.'
Start-Process 'steam://rungameid/2868840'
