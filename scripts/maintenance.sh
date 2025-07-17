#!/bin/bash

# System Maintenance Script for Speech Memorization Platform
# Performs routine maintenance tasks

set -e

PROJECT_DIR="/app"
LOG_DIR="/var/log/speech-memorization"

echo "Starting maintenance tasks at $(date)"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Database maintenance
echo "Performing database maintenance..."
if [ "$DB_ENGINE" = "postgresql" ]; then
    # PostgreSQL maintenance
    echo "Running PostgreSQL VACUUM and ANALYZE..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "VACUUM ANALYZE;"
    
    # Check database size
    DB_SIZE=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | xargs)
    echo "Database size: $DB_SIZE"
else
    # SQLite maintenance
    echo "Running SQLite VACUUM..."
    sqlite3 "$PROJECT_DIR/db.sqlite3" "VACUUM;" 2>/dev/null || true
    
    # Check database size
    if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
        DB_SIZE=$(du -h "$PROJECT_DIR/db.sqlite3" | cut -f1)
        echo "Database size: $DB_SIZE"
    fi
fi

# Clean up old sessions
echo "Cleaning up expired sessions..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py clearsessions || true

# Clean up temporary files
echo "Cleaning up temporary files..."
find /tmp -name "*.tmp" -mtime +1 -delete 2>/dev/null || true
find "$PROJECT_DIR/media/temp" -name "*" -mtime +1 -delete 2>/dev/null || true

# Log file rotation
echo "Rotating log files..."
find "$LOG_DIR" -name "*.log" -size +100M -exec gzip {} \; 2>/dev/null || true
find "$LOG_DIR" -name "*.gz" -mtime +30 -delete 2>/dev/null || true

# Docker maintenance
echo "Performing Docker maintenance..."
docker system prune -f --volumes || true
docker image prune -f || true

# Check disk space
echo "Checking disk space..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
echo "Root filesystem usage: ${DISK_USAGE}%"

if [ "$DISK_USAGE" -gt 85 ]; then
    echo "WARNING: Disk usage is above 85%"
    # Send alert (implement your notification system here)
fi

# Check service health
echo "Checking service health..."
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "Services are running"
else
    echo "WARNING: Some services may be down"
fi

# Generate maintenance report
REPORT_FILE="$LOG_DIR/maintenance_$(date +%Y%m%d_%H%M%S).log"
cat > "$REPORT_FILE" << EOF
Maintenance Report - $(date)
================================

Database Size: $DB_SIZE
Disk Usage: ${DISK_USAGE}%
Services Status: $(docker-compose -f docker-compose.prod.yml ps --services --filter "status=running" | wc -l) running

Tasks Completed:
- Database optimization
- Session cleanup
- Temporary file cleanup
- Log rotation
- Docker cleanup
- Health checks

EOF

echo "Maintenance completed at $(date)"
echo "Report saved to: $REPORT_FILE"

# Log maintenance completion
echo "$(date): Maintenance completed successfully" >> "$LOG_DIR/maintenance.log"