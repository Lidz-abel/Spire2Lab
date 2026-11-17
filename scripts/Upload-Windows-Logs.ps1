<# Upload one game log directly to private server storage; no extra local log copy. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.@:\[\]-]+$')][string]$Server,
    [Parameter(Mandatory=$true)][ValidatePattern('^/[a-zA-Z0-9_][a-zA-Z0-9_./-]*$')][string]$RemoteRoot,
    [ValidateRange(1,65535)][int]$SshPort = 22,
    [string]$LogPath = ''
)
$ErrorActionPreference = 'Stop'
if ($Server.StartsWith('-') -or ($RemoteRoot -split '/') -contains '..') { throw 'Invalid SSH destination.' }
foreach ($Command in @('ssh','scp')) {
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) { throw "Windows OpenSSH client required: $Command not found." }
}
if (-not $LogPath) { $LogPath = Join-Path $env:APPDATA 'SlayTheSpire2\logs\godot.log' }
$Log = Get-Item -LiteralPath $LogPath
if ($Log.PSIsContainer) { throw 'LogPath must refer to one log file.' }
$Before = (Get-FileHash -LiteralPath $Log.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$Capture = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '-' + [Guid]::NewGuid().ToString('N')
$RemoteDirectory = $RemoteRoot.TrimEnd('/') + '/artifacts/windows/logs/' + $Capture
$RemoteFile = $RemoteDirectory + '/godot.log'
& ssh -T -p $SshPort $Server "umask 077; mkdir -p '$RemoteRoot/artifacts/windows/logs' && mkdir '$RemoteDirectory'"
if ($LASTEXITCODE -ne 0) { throw 'Could not create a unique private server log directory; no local file removed.' }
& scp -P $SshPort $Log.FullName "${Server}:$RemoteFile"
if ($LASTEXITCODE -ne 0) { throw 'Log upload failed; local source and any partial server file retained.' }
$RemoteHashOutput = & ssh -T -p $SshPort $Server "sha256sum '$RemoteFile'"
if ($LASTEXITCODE -ne 0) { throw 'Remote checksum could not be read; do not remove the source.' }
$RemoteHash = (([string]($RemoteHashOutput -join "`n")).Trim() -split '\s+')[0].ToLowerInvariant()
$After = (Get-FileHash -LiteralPath $Log.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
if ($RemoteHash -ne $Before -or $After -ne $Before) {
    throw 'Checksum mismatch or log changed during upload. Evidence retained; close the game and retry into a new capture directory.'
}
[pscustomobject]@{
    Status = 'uploaded_and_sha256_verified'
    ServerPath = $RemoteFile
    SHA256 = $Before
    Bytes = $Log.Length
    ExtraLocalLogCopyCreated = $false
    SourceDeleted = $false
} | Format-List
