param(
    [string]$TaskName = "HRMSDesktopAgent",
    [switch]$UsePython
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootExePath = Join-Path $scriptDir "HRMSAgent.exe"
$distExePath = Join-Path $scriptDir "dist\HRMSAgent.exe"
$agentPath = Join-Path $scriptDir "agent.py"

$action = $null

if (Test-Path $rootExePath) {
    $exePath = $rootExePath
}
elseif (Test-Path $distExePath) {
    $exePath = $distExePath
}
else {
    $exePath = $null
}

if ((-not $UsePython) -and $exePath) {
    $action = New-ScheduledTaskAction -Execute $exePath -WorkingDirectory $scriptDir
    Write-Host "Using executable: $exePath"
}
else {
    if (-not (Test-Path $agentPath)) {
        throw "agent.py not found in $scriptDir and executable not found. Cannot install startup."
    }

    $pythonwCmd = Get-Command pythonw -ErrorAction SilentlyContinue
    if (-not $pythonwCmd) {
        throw "pythonw.exe not found. Install Python or provide HRMSAgent.exe."
    }

    $pythonwPath = $pythonwCmd.Source
    $argument = "`"$agentPath`""
    $action = New-ScheduledTaskAction -Execute $pythonwPath -Argument $argument -WorkingDirectory $scriptDir
    Write-Host "Using pythonw: $pythonwPath"
}

$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -Hidden

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Runs HRMS desktop activity agent in background on user login" `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName

Write-Host "Scheduled task '$TaskName' installed and started."
