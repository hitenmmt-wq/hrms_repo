@echo off
setlocal

cd /d "%~dp0"

set "RELEASE_DIR=%~dp0release"
set "PKG_DIR=%RELEASE_DIR%\HRMSAgent_Package"
set "ZIP_PATH=%RELEASE_DIR%\HRMSAgent_Package.zip"

echo [1/4] Building executable...
call build.bat
if errorlevel 1 (
    echo ERROR: Build failed.
    exit /b 1
)

echo [2/4] Preparing release folder...
if exist "%PKG_DIR%" rmdir /s /q "%PKG_DIR%"
if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"
mkdir "%PKG_DIR%"

echo [3/4] Copying package files...
copy /y "dist\HRMSAgent.exe" "%PKG_DIR%\HRMSAgent.exe" >nul
copy /y "agent.py" "%PKG_DIR%\agent.py" >nul
copy /y "register_device.py" "%PKG_DIR%\register_device.py" >nul
copy /y "test_agent.py" "%PKG_DIR%\test_agent.py" >nul
copy /y "test_ubuntu.sh" "%PKG_DIR%\test_ubuntu.sh" >nul
copy /y "check_status.sh" "%PKG_DIR%\check_status.sh" >nul
copy /y "install_dependencies.sh" "%PKG_DIR%\install_dependencies.sh" >nul
copy /y "config.json" "%PKG_DIR%\config.json" >nul
copy /y "install_agent.ps1" "%PKG_DIR%\install_agent.ps1" >nul
copy /y "install_autostart.ps1" "%PKG_DIR%\install_autostart.ps1" >nul
copy /y "uninstall_autostart.ps1" "%PKG_DIR%\uninstall_autostart.ps1" >nul
copy /y "install_linux.sh" "%PKG_DIR%\install_linux.sh" >nul
copy /y "uninstall_linux.sh" "%PKG_DIR%\uninstall_linux.sh" >nul
copy /y "install_macos.sh" "%PKG_DIR%\install_macos.sh" >nul
copy /y "uninstall_macos.sh" "%PKG_DIR%\uninstall_macos.sh" >nul
copy /y "EMPLOYEE_GUIDE.md" "%PKG_DIR%\EMPLOYEE_GUIDE.md" >nul
copy /y "PACKAGE_README.txt" "%PKG_DIR%\PACKAGE_README.txt" >nul
copy /y "SETUP_GUIDE.md" "%PKG_DIR%\SETUP_GUIDE.md" >nul
copy /y "DEPLOYMENT_GUIDE.md" "%PKG_DIR%\DEPLOYMENT_GUIDE.md" >nul

echo [4/4] Creating zip...
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
powershell -NoProfile -Command "Compress-Archive -Path '%PKG_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force"
if errorlevel 1 (
    echo WARNING: Zip creation failed. Folder package is still available at:
    echo %PKG_DIR%
    exit /b 0
)

echo.
echo Package ready:
echo Folder: %PKG_DIR%
echo Zip   : %ZIP_PATH%
exit /b 0
