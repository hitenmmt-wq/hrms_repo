#!/usr/bin/env bash
# Quick status check for HRMS Agent

echo "=========================================="
echo "HRMS Agent Status Check"
echo "=========================================="
echo ""

# Check service status
echo "[1/3] Service Status:"
if systemctl --user is-active --quiet hrms-agent.service; then
    echo "  ✓ Service is RUNNING"
else
    echo "  ✗ Service is NOT running"
    echo ""
    echo "Start it with: systemctl --user start hrms-agent.service"
fi

# Check recent logs
echo ""
echo "[2/3] Recent Logs (last 10 lines):"
if [ -f "$HOME/.hrms_agent/agent.log" ]; then
    tail -n 10 "$HOME/.hrms_agent/agent.log"
else
    echo "  No log file found yet"
fi

# Check for errors
echo ""
echo "[3/3] Recent Errors:"
if [ -f "$HOME/.hrms_agent/agent.error.log" ]; then
    if [ -s "$HOME/.hrms_agent/agent.error.log" ]; then
        tail -n 10 "$HOME/.hrms_agent/agent.error.log"
    else
        echo "  ✓ No errors"
    fi
else
    echo "  ✓ No error log"
fi

echo ""
echo "=========================================="
echo "Commands:"
echo "  View live logs: tail -f ~/.hrms_agent/agent.log"
echo "  Restart agent: systemctl --user restart hrms-agent.service"
echo "  Stop agent: systemctl --user stop hrms-agent.service"
echo "=========================================="
