#!/usr/bin/env bash
# Install HRMS Agent dependencies on Ubuntu/Debian

set -e

echo "=========================================="
echo "HRMS Agent - Dependency Installer"
echo "=========================================="
echo ""

# Detect Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found!"
    echo ""
    echo "Install Python:"
    echo "  sudo apt update"
    echo "  sudo apt install python3"
    exit 1
fi

echo "✓ Python found: $(${PYTHON_CMD} --version)"
echo ""

# Method 1: Try pip
echo "[Method 1] Installing via pip..."
if ${PYTHON_CMD} -m pip --version &>/dev/null; then
    echo "  ✓ pip is available"
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        ${PYTHON_CMD} -m pip install requests pynput
    else
        ${PYTHON_CMD} -m pip install --user requests pynput || ${PYTHON_CMD} -m pip install requests pynput
    fi
    echo "  ✓ Dependencies installed via pip"
    exit 0
fi

# Method 2: Install pip first
echo "  ⚠ pip not found. Installing pip..."
if command -v apt &>/dev/null; then
    echo ""
    echo "Run these commands:"
    echo "  sudo apt update"
    echo "  sudo apt install python3-pip"
    echo ""
    read -p "Install pip now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update
        sudo apt install -y python3-pip
        ${PYTHON_CMD} -m pip install --user requests pynput
        echo "  ✓ Dependencies installed via pip"
        exit 0
    fi
fi

# Method 3: System packages
echo ""
echo "[Method 2] Installing via system packages..."
if command -v apt &>/dev/null; then
    echo "Run these commands:"
    echo "  sudo apt update"
    echo "  sudo apt install python3-requests python3-pynput"
    echo ""
    read -p "Install system packages now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update
        sudo apt install -y python3-requests python3-pynput
        echo "  ✓ Dependencies installed via apt"
        exit 0
    fi
fi

echo ""
echo "=========================================="
echo "Manual Installation Required"
echo "=========================================="
echo ""
echo "Option 1 (pip):"
echo "  sudo apt install python3-pip"
echo "  ${PYTHON_CMD} -m pip install --user requests pynput"
echo ""
echo "Option 2 (system packages):"
echo "  sudo apt install python3-requests python3-pynput"
echo ""
