# HRMS Agent - Employee Quick Start

## What is this?
This software tracks your work activity (keyboard/mouse) and reports it to the company HRMS system. It runs in the background and starts automatically when you log in.

---

## Windows Setup (5 minutes)

### Step 1: Extract Files
- Extract the ZIP to `C:\HRMSAgent`

### Step 2: Update Server Address
- Open `config.json` in Notepad
- Change `"server_url"` to your company's HRMS address
- Save and close

### Step 3: Install
- Right-click PowerShell → Run as Administrator
- Type:
  ```
  cd C:\HRMSAgent
  powershell -ExecutionPolicy Bypass -File .\install_agent.ps1 -Email your@email.com -Password yourpassword
  ```
- Press Enter

### Done!
The agent is now running and will start automatically when you log in.

---

## Linux/Ubuntu Setup (5 minutes)

### Step 1: Copy Files
- Copy the extracted folder to your home directory

### Step 2: Update Server Address
- Open `config.json` in text editor
- Change `"server_url"` to your company's HRMS address
- Save and close

### Step 3: Quick Test (Optional)
```bash
cd ~/HRMSAgent_Package
chmod +x test_ubuntu.sh
./test_ubuntu.sh
```

### Step 4: Install
```bash
chmod +x install_linux.sh
./install_linux.sh your@email.com yourpassword "My Laptop"
```

### Done!
The agent is now running and will start automatically when you log in.

---

## macOS Setup (5 minutes)

### Step 1: Copy Files
- Copy the extracted folder to your home directory

### Step 2: Update Server Address
- Open `config.json` in TextEdit
- Change `"server_url"` to your company's HRMS address
- Save and close

### Step 3: Install
```bash
cd ~/HRMSAgent_Package
chmod +x install_macos.sh
./install_macos.sh your@email.com yourpassword "My Mac"
```

### Step 4: Grant Permissions
- Open System Settings
- Go to Privacy & Security → Accessibility
- Click the lock, add Terminal (or Python)
- Go to Privacy & Security → Input Monitoring
- Click the lock, add Terminal (or Python)

### Done!
The agent is now running and will start automatically when you log in.

---

## Manual Registration (If Automatic Fails)

If the install script doesn't work:

1. Open Terminal/Command Prompt
2. Navigate to the agent folder
3. Run:
   - Windows: `python register_device.py`
   - Linux/Mac: `python3 register_device.py`
4. Enter your email and password
5. Run the install script again

---

## How to Check if It's Working

### Windows
```powershell
Get-ScheduledTask -TaskName HRMSDesktopAgent
```
Should show "Ready" or "Running"

### Linux
```bash
systemctl --user status hrms-agent.service
```
Should show "active (running)"

### macOS
```bash
launchctl list | grep com.hrms.agent
```
Should show a process ID

---

## How to Uninstall

### Windows
```powershell
cd C:\HRMSAgent
powershell -ExecutionPolicy Bypass -File .\uninstall_autostart.ps1
```

### Linux
```bash
cd ~/HRMSAgent_Package
./uninstall_linux.sh
```

### macOS
```bash
cd ~/HRMSAgent_Package
./uninstall_macos.sh
```

---

## Troubleshooting

### "Python not found"
- Install Python 3.8 or higher from python.org
- Make sure "Add to PATH" is checked during installation

### "Connection failed"
- Check your internet connection
- Verify the server_url in config.json is correct
- Contact IT support

### "Permission denied" (Linux/Mac)
- Make sure scripts are executable: `chmod +x *.sh`
- For macOS, grant Accessibility permissions

### Still not working?
- Check PACKAGE_README.txt for detailed instructions
- Contact IT support with error messages
- Check log files:
  - Linux/Mac: `~/.hrms_agent/agent.log`
  - Windows: Same folder as agent

---

## Privacy Note

This agent monitors:
- Keyboard activity (not keystrokes, just activity)
- Mouse movements
- Idle time

It does NOT record:
- What you type
- Screenshots
- Websites visited
- File contents

All data is sent securely to your company's HRMS system.
