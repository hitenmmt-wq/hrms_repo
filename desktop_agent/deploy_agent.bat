@echo off
setlocal

cd /d "%~dp0"

set "REG_EMAIL=%~1"
set "REG_PASSWORD=%~2"

if not defined REG_EMAIL set "REG_EMAIL=%HRMS_EMAIL%"
if not defined REG_PASSWORD set "REG_PASSWORD=%HRMS_PASSWORD%"

echo [1/4] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    exit /b 1
)

echo [2/4] Checking device registration...
python -c "import json,sys; c=json.load(open('config.json','r',encoding='utf-8')); t=(c.get('tracking_token') or '').strip(); sys.exit(0 if (t and t!='PUT-DEVICE-TOKEN-HERE') else 1)"
if errorlevel 1 (
    echo tracking_token missing. Starting device registration...
    if defined REG_EMAIL if defined REG_PASSWORD (
        echo Using non-interactive registration.
        python register_device.py --email "%REG_EMAIL%" --password "%REG_PASSWORD%" --non-interactive
    ) else (
        echo Credentials not provided. Falling back to interactive registration prompt.
        python register_device.py
    )
    if errorlevel 1 (
        echo ERROR: Device registration failed.
        exit /b 1
    )
) else (
    echo tracking_token already configured. Skipping registration.
)

echo [3/4] Building background executable...
call build.bat
if errorlevel 1 (
    echo ERROR: Build failed.
    exit /b 1
)

echo [4/4] Installing startup task...
powershell -ExecutionPolicy Bypass -File ".\install_autostart.ps1"
if errorlevel 1 (
    echo ERROR: Auto-start task installation failed.
    exit /b 1
)

echo.
echo Deployment completed successfully.
echo The HRMS activity agent will run in background at user login.
exit /b 0
