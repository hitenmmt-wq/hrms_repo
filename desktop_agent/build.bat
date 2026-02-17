@echo off
setlocal

cd /d "%~dp0"
set "TASK_NAME=HRMSDesktopAgent"
set "WAS_RUNNING=0"

echo Preparing build (stopping running agent if needed)...
powershell -NoProfile -Command "$t=Get-ScheduledTask -TaskName '%TASK_NAME%' -ErrorAction SilentlyContinue; if($t -and $t.State -eq 'Running'){ exit 0 } else { exit 1 }"
if not errorlevel 1 (
    set "WAS_RUNNING=1"
    powershell -NoProfile -Command "Stop-ScheduledTask -TaskName '%TASK_NAME%' -ErrorAction SilentlyContinue" >nul 2>nul
)

taskkill /IM HRMSAgent.exe /F >nul 2>nul

echo Installing build dependency...
pip install pyinstaller
if errorlevel 1 goto :build_failed

echo Building HRMSAgent.exe (background/no console)...
pyinstaller --clean --onefile --noconsole --name HRMSAgent --add-data "config.json;." agent.py
if errorlevel 1 goto :build_failed

echo Build complete: dist\HRMSAgent.exe
set "BUILD_EXIT=0"
goto :restore_task

:build_failed
echo ERROR: Build failed.
set "BUILD_EXIT=1"

:restore_task

if "%WAS_RUNNING%"=="1" (
    echo Restarting scheduled task %TASK_NAME%...
    powershell -NoProfile -Command "Start-ScheduledTask -TaskName '%TASK_NAME%' -ErrorAction SilentlyContinue" >nul 2>nul
)

endlocal
exit /b %BUILD_EXIT%
