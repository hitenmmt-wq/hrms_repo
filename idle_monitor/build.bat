@echo off
echo Building HRMS Idle Detector...

REM Install dependencies
pip install -r requirements.txt

REM Build executable
pyinstaller --onefile --noconsole --name "HRMS_IdleDetector" idle_detector.py

REM Copy config file to dist folder
copy config.json dist\

echo.
echo Build complete! Check the 'dist' folder for HRMS_IdleDetector.exe
echo Don't forget to configure config.json with your employee token!
pause
