#!/bin/bash

# HRMS Monitoring Script
# Usage: ./monitor.sh

HEALTH_URL="http://localhost/health/"
ALERT_EMAIL="admin@yourhrms.com"
LOG_FILE="/var/log/hrms-monitor.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_health() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")

    if [[ "$response" == "200" ]]; then
        log "✅ Health check passed"
        return 0
    else
        log "❌ Health check failed with status: $response"
        return 1
    fi
}

check_disk_space() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

    if [[ $usage -gt 85 ]]; then
        log "⚠️  Disk usage is at ${usage}%"
        return 1
    else
        log "✅ Disk usage is at ${usage}%"
        return 0
    fi
}

check_memory() {
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')

    if [[ $usage -gt 85 ]]; then
        log "⚠️  Memory usage is at ${usage}%"
        return 1
    else
        log "✅ Memory usage is at ${usage}%"
        return 0
    fi
}

check_containers() {
    local unhealthy=$(docker-compose -f docker-compose.prod.yml ps | grep -c "unhealthy\|Exit")

    if [[ $unhealthy -gt 0 ]]; then
        log "❌ Found $unhealthy unhealthy containers"
        docker-compose -f docker-compose.prod.yml ps | tee -a "$LOG_FILE"
        return 1
    else
        log "✅ All containers are healthy"
        return 0
    fi
}

send_alert() {
    local message="$1"
    log "🚨 ALERT: $message"

    # Send email alert (requires mailutils)
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "HRMS Alert" "$ALERT_EMAIL"
    fi

    # You can add other alerting mechanisms here (Slack, Discord, etc.)
}

main() {
    log "Starting HRMS monitoring check..."

    local alerts=()

    if ! check_health; then
        alerts+=("Application health check failed")
    fi

    if ! check_disk_space; then
        alerts+=("High disk usage detected")
    fi

    if ! check_memory; then
        alerts+=("High memory usage detected")
    fi

    if ! check_containers; then
        alerts+=("Container health issues detected")
    fi

    if [[ ${#alerts[@]} -gt 0 ]]; then
        local alert_message="HRMS System Issues Detected:\n"
        for alert in "${alerts[@]}"; do
            alert_message+="\n- $alert"
        done
        send_alert "$alert_message"
    else
        log "✅ All systems operational"
    fi

    log "Monitoring check completed"
}

main "$@"
