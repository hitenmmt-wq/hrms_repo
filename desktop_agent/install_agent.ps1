param(
    [Parameter(Mandatory = $true)]
    [string]$Email,
    [Parameter(Mandatory = $true)]
    [string]$Password,
    [string]$TaskName = "HRMSDesktopAgent",
    [string]$DeviceName = "",
    [string]$ServerUrl = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $scriptDir "config.json"
$installTaskScript = Join-Path $scriptDir "install_autostart.ps1"

if (-not (Test-Path $configPath)) {
    throw "config.json not found in $scriptDir"
}

if (-not (Test-Path $installTaskScript)) {
    throw "install_autostart.ps1 not found in $scriptDir"
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json

if ($ServerUrl) {
    $config.server_url = $ServerUrl
}

if (-not $config.server_url) {
    throw "server_url is missing in config.json. Provide -ServerUrl or set it in config.json."
}

if ($DeviceName) {
    $config.device_name = $DeviceName
}

$trackingToken = [string]$config.tracking_token
$needsRegister = (-not $trackingToken) -or ($trackingToken -eq "PUT-DEVICE-TOKEN-HERE")

if ($needsRegister) {
    $server = ([string]$config.server_url).TrimEnd("/")
    $loginUrl = "$server/superadmin/auth/login/"
    $registerUrl = "$server/superadmin/device/register/"

    Write-Host "Registering device with HRMS API..."

    $loginBody = @{
        email    = $Email
        password = $Password
    } | ConvertTo-Json

    $loginResp = Invoke-RestMethod -Method Post -Uri $loginUrl -ContentType "application/json" -Body $loginBody
    $accessToken = $loginResp.access
    if (-not $accessToken) {
        throw "Login response missing access token."
    }

    $headers = @{ Authorization = "Bearer $accessToken" }
    $registerBody = @{}
    if ($config.device_name) {
        $registerBody.device_name = [string]$config.device_name
    }
    $registerJson = $registerBody | ConvertTo-Json

    $regResp = Invoke-RestMethod -Method Post -Uri $registerUrl -Headers $headers -ContentType "application/json" -Body $registerJson
    if (-not $regResp.tracking_token) {
        throw "Register response missing tracking_token."
    }

    $config.tracking_token = [string]$regResp.tracking_token
    $config | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $configPath
    Write-Host "Device registered and tracking_token stored in config.json"
}
else {
    Write-Host "tracking_token already present. Skipping registration."
}

& $installTaskScript -TaskName $TaskName
Write-Host "Agent installation completed."
