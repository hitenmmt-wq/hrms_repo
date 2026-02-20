#!/usr/bin/env bash
set -euo pipefail

systemctl --user disable --now hrms-agent.service >/dev/null 2>&1 || true
rm -f "${HOME}/.config/systemd/user/hrms-agent.service"
systemctl --user daemon-reload

echo "Removed hrms-agent.service"
