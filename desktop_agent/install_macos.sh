#!/usr/bin/env bash
set -euo pipefail

EMAIL="${1:-${HRMS_EMAIL:-}}"
PASSWORD="${2:-${HRMS_PASSWORD:-}}"
DEVICE_NAME="${3:-$(hostname)}"
SERVER_URL="${4:-}"

if [[ -z "${EMAIL}" || -z "${PASSWORD}" ]]; then
  echo "Usage: ./install_macos.sh <email> <password> [device_name] [server_url]"
  echo "Or set HRMS_EMAIL and HRMS_PASSWORD environment variables."
  exit 1
fi

# Detect Python command
if command -v python3 &>/dev/null; then
  PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
  PYTHON_CMD="python"
else
  echo "Error: Python not found. Please install Python 3.8+"
  exit 1
fi

echo "Using Python: $(${PYTHON_CMD} --version)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.hrms_agent"
CONFIG_PATH="${TARGET_DIR}/config.json"
PLIST_PATH="${HOME}/Library/LaunchAgents/com.hrms.agent.plist"

echo "Installing to: ${TARGET_DIR}"
mkdir -p "${TARGET_DIR}"
cp -f "${SCRIPT_DIR}/agent.py" "${TARGET_DIR}/agent.py"
cp -f "${SCRIPT_DIR}/config.json" "${CONFIG_PATH}"

echo "Installing Python dependencies..."

# Check if pip is available
if ! ${PYTHON_CMD} -m pip --version &>/dev/null; then
    echo "  ⚠ pip not found. Installing..."
    if command -v brew &>/dev/null; then
        # macOS with Homebrew
        echo "  Run: ${PYTHON_CMD} -m ensurepip --upgrade"
    fi
    echo "  Skipping pip install. Install dependencies manually."
else
    # pip is available
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        # Inside virtualenv - install without --user
        ${PYTHON_CMD} -m pip install requests pynput 2>&1 | grep -v "Requirement already satisfied" || true
    else
        # Outside virtualenv - install to user directory
        ${PYTHON_CMD} -m pip install --user requests pynput 2>&1 | grep -v "Requirement already satisfied" || true
    fi
fi

if [[ -n "${SERVER_URL}" ]]; then
  echo "Updating server URL to: ${SERVER_URL}"
  ${PYTHON_CMD} - "$CONFIG_PATH" "$SERVER_URL" <<'PY'
import json, sys
path, server = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as f:
    c = json.load(f)
c["server_url"] = server
with open(path, "w", encoding="utf-8") as f:
    json.dump(c, f, indent=2)
PY
fi

echo "Registering device: ${DEVICE_NAME}"
${PYTHON_CMD} - "$CONFIG_PATH" "$EMAIL" "$PASSWORD" "$DEVICE_NAME" <<'PY'
import json, sys, requests
config_path, email, password, device_name = sys.argv[1:5]
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)
server = config["server_url"].rstrip("/")
token = (config.get("tracking_token") or "").strip()
if not token or token == "PUT-DEVICE-TOKEN-HERE":
    login = requests.post(
        f"{server}/superadmin/auth/login/",
        json={"email": email, "password": password},
        timeout=10,
    )
    login.raise_for_status()
    access = login.json().get("access")
    if not access:
        raise RuntimeError("Login response missing access token.")
    headers = {"Authorization": f"Bearer {access}"}
    payload = {"device_name": device_name} if device_name else {}
    reg = requests.post(
        f"{server}/superadmin/device/register/",
        headers=headers,
        json=payload,
        timeout=10,
    )
    reg.raise_for_status()
    t = reg.json().get("tracking_token")
    if not t:
        raise RuntimeError("Register response missing tracking_token.")
    config["tracking_token"] = t
    with open(config_path, "w", encoding="utf-8") as fw:
        json.dump(config, fw, indent=2)
PY

# Get full path to Python
PYTHON_PATH=$(command -v ${PYTHON_CMD})

echo "Creating LaunchAgent..."
mkdir -p "${HOME}/Library/LaunchAgents"
cat > "${PLIST_PATH}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.hrms.agent</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON_PATH}</string>
    <string>${TARGET_DIR}/agent.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${TARGET_DIR}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${TARGET_DIR}/agent.log</string>
  <key>StandardErrorPath</key>
  <string>${TARGET_DIR}/agent.error.log</string>
</dict>
</plist>
EOF

echo "Loading and starting LaunchAgent..."
launchctl unload "${PLIST_PATH}" >/dev/null 2>&1 || true
launchctl load "${PLIST_PATH}"
launchctl start com.hrms.agent >/dev/null 2>&1 || true

echo ""
echo "✓ Installation complete!"
echo "✓ LaunchAgent: com.hrms.agent"
echo "✓ Config: ${CONFIG_PATH}"
echo "✓ Logs: ${TARGET_DIR}/agent.log"
echo ""
echo "IMPORTANT: Grant permissions in System Settings:"
echo "  1. Privacy & Security → Accessibility → Add Terminal/Python"
echo "  2. Privacy & Security → Input Monitoring → Add Terminal/Python"
echo ""
echo "Check status: launchctl list | grep com.hrms.agent"
echo "View logs: tail -f ${TARGET_DIR}/agent.log"
