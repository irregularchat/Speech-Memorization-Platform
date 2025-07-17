#!/bin/bash

# System Monitoring Script for Speech Memorization Platform
# Monitors system health and sends alerts if needed

set -e

PROJECT_DIR="/app"
LOG_DIR="/var/log/speech-memorization"
ALERT_EMAIL="${ADMIN_EMAIL:-admin@example.com}"

# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=85
RESPONSE_TIME_THRESHOLD=5000  # milliseconds

echo "Starting system monitoring at $(date)"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to send alert
send_alert() {
    local subject="$1"
    local message="$2"
    echo "ALERT: $subject - $message" | tee -a "$LOG_DIR/alerts.log"
    # Implement your notification system here (email, Slack, etc.)
}

# Check CPU usage
CPU_USAGE=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' 2>/dev/null || echo "0")
if [ "${CPU_USAGE%.*}" -gt "$CPU_THRESHOLD" ]; then
    send_alert "High CPU Usage" "CPU usage is ${CPU_USAGE}% (threshold: ${CPU_THRESHOLD}%)"
fi

# Check memory usage
MEMORY_USAGE=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//' 2>/dev/null || echo "0")
# Convert to percentage (simplified for macOS)
if [ "$MEMORY_USAGE" -gt 500000 ]; then  # Approximate threshold
    send_alert "High Memory Usage" "Memory usage is high"
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt "$DISK_THRESHOLD" ]; then
    send_alert "High Disk Usage" "Disk usage is ${DISK_USAGE}% (threshold: ${DISK_THRESHOLD}%)"
fi

# Check application response time
if command -v curl >/dev/null 2>&1; then
    RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/ 2>/dev/null || echo "999")
    RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc 2>/dev/null || echo "9999")
    
    if [ "${RESPONSE_TIME_MS%.*}" -gt "$RESPONSE_TIME_THRESHOLD" ]; then
        send_alert "Slow Response Time" "Application response time is ${RESPONSE_TIME_MS}ms (threshold: ${RESPONSE_TIME_THRESHOLD}ms)"
    fi
fi

# Check database connectivity
if [ "$DB_ENGINE" = "postgresql" ]; then
    if ! PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
        send_alert "Database Connection Failed" "Cannot connect to PostgreSQL database"
    fi
else
    if [ ! -f "$PROJECT_DIR/db.sqlite3" ]; then
        send_alert "Database File Missing" "SQLite database file not found"
    fi
fi

# Check Docker services
if command -v docker-compose >/dev/null 2>&1; then
    DOWN_SERVICES=$(docker-compose -f docker-compose.prod.yml ps --services --filter "status=exited" 2>/dev/null | wc -l)
    if [ "$DOWN_SERVICES" -gt 0 ]; then
        send_alert "Services Down" "$DOWN_SERVICES Docker services are not running"
    fi
fi

# Check log errors
ERROR_COUNT=$(grep -c "ERROR" "$LOG_DIR"/*.log 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
if [ "$ERROR_COUNT" -gt 10 ]; then
    send_alert "High Error Rate" "Found $ERROR_COUNT errors in logs"
fi

# Generate monitoring report
REPORT_FILE="$LOG_DIR/monitoring_$(date +%Y%m%d_%H%M%S).log"
cat > "$REPORT_FILE" << EOF
System Monitoring Report - $(date)
==================================

System Metrics:
- CPU Usage: ${CPU_USAGE}%
- Disk Usage: ${DISK_USAGE}%
- Response Time: ${RESPONSE_TIME_MS:-N/A}ms
- Error Count: $ERROR_COUNT

Service Status:
$(docker-compose -f docker-compose.prod.yml ps 2>/dev/null || echo "Docker not available")

Thresholds:
- CPU: ${CPU_THRESHOLD}%
- Memory: ${MEMORY_THRESHOLD}%
- Disk: ${DISK_THRESHOLD}%
- Response Time: ${RESPONSE_TIME_THRESHOLD}ms

EOF

# Log metrics for trending
echo "$(date),${CPU_USAGE},${DISK_USAGE},${RESPONSE_TIME_MS:-0},${ERROR_COUNT}" >> "$LOG_DIR/metrics.csv"

echo "Monitoring completed at $(date)"
echo "Report saved to: $REPORT_FILE"