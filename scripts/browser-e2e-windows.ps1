param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('GetVersion', 'Cleanup')]
    [string]$Action,

    [string]$ProfilePath,
    [string]$DebugPort,
    [string]$CdpUrl,
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

if ($Action -eq 'GetVersion') {
    if (-not $CdpUrl -or -not $OutputPath) {
        throw 'GetVersion requires CdpUrl and OutputPath.'
    }

    $response = Invoke-RestMethod -Uri $CdpUrl -TimeoutSec 5
    $json = $response | ConvertTo-Json
    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($OutputPath, $json, $utf8WithoutBom)
    exit 0
}

if (-not $ProfilePath) {
    throw 'Cleanup requires ProfilePath.'
}

$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
$resolvedProfile = [System.IO.Path]::GetFullPath($ProfilePath).TrimEnd('\')
$profileParent = [System.IO.Path]::GetDirectoryName($resolvedProfile).TrimEnd('\')
$profileLeaf = [System.IO.Path]::GetFileName($resolvedProfile)

if ($profileParent -ne $tempRoot -or $profileLeaf -notlike 'agentcore-e2e.*') {
    throw "Refusing to clean unexpected profile path: $resolvedProfile"
}

function Get-OwnedChromeProcess {
    @(Get-CimInstance Win32_Process -Filter "Name = 'chrome.exe'" | Where-Object {
        $_.Name -eq 'chrome.exe' -and
        $_.CommandLine -and
        $_.CommandLine.IndexOf($resolvedProfile, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
    })
}

$owned = @(Get-OwnedChromeProcess)
$ownedIds = @($owned | ForEach-Object { [int]$_.ProcessId })
$rootProcesses = @($owned | Where-Object {
    $_.CommandLine -notmatch '--type='
})
foreach ($process in $rootProcesses) {
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    & taskkill.exe /PID $process.ProcessId /T /F 2> $null | Out-Null
    $ErrorActionPreference = $previousErrorAction
}

for ($attempt = 0; $attempt -lt 10; $attempt++) {
    $remainingIds = @($ownedIds | Where-Object {
        Get-Process -Id $_ -ErrorAction SilentlyContinue
    })
    if ($remainingIds.Count -eq 0) {
        break
    }
    foreach ($ownedProcessId in $remainingIds) {
        Stop-Process -Id $ownedProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 250
}

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if (-not (Test-Path -LiteralPath $resolvedProfile)) {
        break
    }
    Remove-Item -LiteralPath $resolvedProfile -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 250
}

$remaining = @($ownedIds | Where-Object {
    Get-Process -Id $_ -ErrorAction SilentlyContinue
})
$listeners = @()
if ($DebugPort) {
    for ($attempt = 0; $attempt -lt 10; $attempt++) {
        $listeners = @(Get-NetTCPConnection -State Listen -LocalPort ([int]$DebugPort) -ErrorAction SilentlyContinue)
        if ($listeners.Count -eq 0) {
            break
        }
        Start-Sleep -Milliseconds 250
    }
}

[pscustomobject]@{
    chrome_stopped = ($remaining.Count -eq 0)
    profile_removed = (-not (Test-Path -LiteralPath $resolvedProfile))
    debug_port_released = ($listeners.Count -eq 0)
    debug_port = $DebugPort
} | ConvertTo-Json -Compress
