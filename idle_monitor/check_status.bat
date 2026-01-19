@echo off
echo Checking HRMS Idle Detector Status...
echo.

tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *idle_detector*" 2>NUL | find /I "python.exe" >NUL

if %ERRORLEVEL% EQU 0 (
    echo ✅ HRMS Idle Detector is RUNNING
    echo.
    tasklist /FI "IMAGENAME eq python.exe" /V | findstr /I "idle_detector"
) else (
    echo ❌ HRMS Idle Detector is NOT RUNNING
    echo.
    echo To start it, run: python idle_detector.py
)

echo.
pause
