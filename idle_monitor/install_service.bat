@echo off
echo Installing HRMS Idle Detector as Windows Service...

REM Create service directory
mkdir "C:\HRMS_Service" 2>nul

REM Copy files
copy "HRMS_IdleDetector.exe" "C:\HRMS_Service\"
copy "config.json" "C:\HRMS_Service\"

REM Install as Windows service using sc command
sc create "HRMS_IdleDetector" binPath= "C:\HRMS_Service\HRMS_IdleDetector.exe" start= auto DisplayName= "HRMS Idle Detector Service"

REM Start the service
sc start "HRMS_IdleDetector"

echo.
echo ✅ Service installed successfully!
echo Service will start automatically on boot.
echo.
echo To uninstall: run uninstall_service.bat
pause
