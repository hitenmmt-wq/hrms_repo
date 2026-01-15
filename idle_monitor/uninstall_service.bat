@echo off
echo Uninstalling HRMS Idle Detector Service...

REM Stop the service
sc stop "HRMS_IdleDetector"

REM Delete the service
sc delete "HRMS_IdleDetector"

echo.
echo ✅ Service uninstalled successfully!
pause
