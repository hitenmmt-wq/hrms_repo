#!/usr/bin/env bash
# Quick test script for Ubuntu/Linux - no Python dependencies needed

set -e

echo "=========================================="
echo "HRMS Agent - Ubuntu Quick Test"
echo "=========================================="
echo ""

# Check Python
echo "[1/5] Checking Python..."
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
    echo "  ✓ Python found: $(python3 --version)"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
    echo "  ✓ Python found: $(python --version)"
else
    echo "  ✗ Python not found. Install: sudo apt install python3"
    exit 1
fi

# Check config.json
echo ""
echo "[2/5] Checking config.json..."
if [ ! -f "config.json" ]; then
    echo "  ✗ config.json not found"
    exit 1
fi
echo "  ✓ config.json exists"

# Check server_url
SERVER_URL=$(${PYTHON_CMD} -c "import json; print(json.load(open('config.json'))['server_url'])" 2>/dev/null || echo "")
if [ -z "$SERVER_URL" ]; then
    echo "  ✗ server_url not found in config.json"
    exit 1
fi
echo "  ✓ server_url: $SERVER_URL"

# Check tracking_token
TOKEN=$(${PYTHON_CMD} -c "import json; print(json.load(open('config.json')).get('tracking_token', 'NOT_SET'))" 2>/dev/null || echo "NOT_SET")
if [ "$TOKEN" = "PUT-DEVICE-TOKEN-HERE" ] || [ "$TOKEN" = "NOT_SET" ]; then
    echo "  ⚠ tracking_token not set - device needs registration"
    echo ""
    echo "To register device, run:"
    echo "  ${PYTHON_CMD} register_device.py"
else
    echo "  ✓ tracking_token: ${TOKEN:0:20}..."
fi

# Check dependencies
echo ""
echo "[3/5] Checking Python dependencies..."
MISSING_DEPS=""

if ! ${PYTHON_CMD} -c "import requests" 2>/dev/null; then
    echo "  ✗ requests not installed"
    MISSING_DEPS="${MISSING_DEPS} requests"
else
    echo "  ✓ requests installed"
fi

if ! ${PYTHON_CMD} -c "import pynput" 2>/dev/null; then
    echo "  ✗ pynput not installed"
    MISSING_DEPS="${MISSING_DEPS} pynput"
else
    echo "  ✓ pynput installed"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo ""
    echo "Install missing dependencies:"
    echo "  ${PYTHON_CMD} -m pip install --user${MISSING_DEPS}"
    exit 1
fi

# Check connectivity
echo ""
echo "[4/5] Testing server connectivity..."
ACTIVITY_ENDPOINT=$(${PYTHON_CMD} -c "import json; print(json.load(open('config.json')).get('activity_endpoint', '/superadmin/activity-log/'))" 2>/dev/null || echo "/superadmin/activity-log/")
ACTIVITY_URL="${SERVER_URL}${ACTIVITY_ENDPOINT}"

if command -v curl &>/dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$ACTIVITY_URL" -H "Content-Type: application/json" -d '{"tracking_token":"test","is_active":true,"idle_seconds":0}' --connect-timeout 5 || echo "000")
    if [ "$HTTP_CODE" = "000" ]; then
        echo "  ✗ Cannot connect to server"
        echo "    URL: $ACTIVITY_URL"
    elif [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
        echo "  ✓ Server reachable (HTTP $HTTP_CODE)"
    else
        echo "  ⚠ Server responded with HTTP $HTTP_CODE"
    fi
else
    echo "  ⚠ curl not found - skipping connectivity test"
fi

# Check if running in graphical session
echo ""
echo "[5/5] Checking environment..."
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "  ⚠ No graphical session detected (DISPLAY not set)"
    echo "    Input monitoring may not work over SSH"
else
    echo "  ✓ Graphical session detected"
fi

# Summary
echo ""
echo "=========================================="
echo "✅ Basic checks passed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
if [ "$TOKEN" = "PUT-DEVICE-TOKEN-HERE" ] || [ "$TOKEN" = "NOT_SET" ]; then
    echo "1. Register device:"
    echo "   ${PYTHON_CMD} register_device.py"
    echo ""
fi
echo "2. Install agent:"
echo "   chmod +x install_linux.sh"
echo "   ./install_linux.sh your@email.com password \"Device Name\" \"$SERVER_URL\""
echo ""
echo "3. Check status:"
echo "   systemctl --user status hrms-agent.service"
echo ""
