HRMS Agent - Employee Device Package
=====================================

SUPPORTED PLATFORMS: Windows, Linux, macOS

FILES INCLUDED:
- agent.py (main agent - all platforms)
- register_device.py (device registration)
- test_agent.py (full test with dependencies)
- test_ubuntu.sh (quick test for Linux - no deps needed)
- config.json (configuration file)
- HRMSAgent.exe (Windows executable)
- install_agent.ps1 (Windows installer)
- install_autostart.ps1 (Windows auto-start)
- uninstall_autostart.ps1 (Windows uninstaller)
- install_linux.sh (Linux installer)
- uninstall_linux.sh (Linux uninstaller)
- install_macos.sh (macOS installer)
- uninstall_macos.sh (macOS uninstaller)
- SETUP_GUIDE.md (detailed documentation)
- DEPLOYMENT_GUIDE.md (quick reference)

=====================================
WINDOWS INSTALLATION
=====================================

1. Extract package to: C:\HRMSAgent

2. Update config.json:
   - Change "server_url" to your HRMS server
   - Set "tracking_token" to "PUT-DEVICE-TOKEN-HERE"

3. Test (optional):
   python test_agent.py

4. Open PowerShell as Administrator

5. Run:
   cd C:\HRMSAgent
   powershell -ExecutionPolicy Bypass -File .\install_agent.ps1 -Email employee@company.com -Password your_password

6. Verify:
   Get-ScheduledTask -TaskName HRMSDesktopAgent

MANUAL REGISTRATION (if needed):
   python register_device.py

UNINSTALL:
   powershell -ExecutionPolicy Bypass -File .\uninstall_autostart.ps1

=====================================
LINUX INSTALLATION (Ubuntu/Debian)
=====================================

1. Copy package to employee machine

2. Update config.json:
   - Change "server_url" to your HRMS server
   - Set "tracking_token" to "PUT-DEVICE-TOKEN-HERE"

3. Quick test (no dependencies needed):
   chmod +x test_ubuntu.sh
   ./test_ubuntu.sh

4. Install:
   chmod +x install_linux.sh
   ./install_linux.sh employee@company.com your_password "Device Name" "http://your-server:8000"

5. Verify:
   systemctl --user status hrms-agent.service
   tail -f ~/.hrms_agent/agent.log

MANUAL REGISTRATION (if needed):
   python3 register_device.py

UNINSTALL:
   chmod +x uninstall_linux.sh
   ./uninstall_linux.sh

=====================================
macOS INSTALLATION
=====================================

1. Copy package to employee machine

2. Update config.json:
   - Change "server_url" to your HRMS server
   - Set "tracking_token" to "PUT-DEVICE-TOKEN-HERE"

3. Test (optional):
   python3 test_agent.py

4. Install:
   chmod +x install_macos.sh
   ./install_macos.sh employee@company.com your_password "Device Name" "http://your-server:8000"

5. Grant Permissions:
   System Settings → Privacy & Security → Accessibility → Add Terminal/Python
   System Settings → Privacy & Security → Input Monitoring → Add Terminal/Python

6. Verify:
   launchctl list | grep com.hrms.agent
   tail -f ~/.hrms_agent/agent.log

MANUAL REGISTRATION (if needed):
   python3 register_device.py

UNINSTALL:
   chmod +x uninstall_macos.sh
   ./uninstall_macos.sh

=====================================
MANUAL REGISTRATION (All Platforms)
=====================================

If install scripts fail or you need to register manually:

1. Update config.json with server_url

2. Run registration:
   Windows:  python register_device.py
   Linux:    python3 register_device.py
   macOS:    python3 register_device.py

3. Enter your email and password when prompted

4. tracking_token will be saved to config.json

5. Then run install script or agent.py directly

=====================================
RUNNING AGENT MANUALLY (Testing)
=====================================

Before installing as service, test manually:

Windows:
  python agent.py

Linux/macOS:
  python3 agent.py

Press Ctrl+C to stop

=====================================
TESTING
=====================================

Windows/macOS:
  python test_agent.py
  (or python3 test_agent.py)

Linux (quick test, no dependencies):
  chmod +x test_ubuntu.sh
  ./test_ubuntu.sh

Linux (full test):
  python3 test_agent.py
