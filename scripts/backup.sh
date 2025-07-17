#!/bin/bash

# Database and Media Backup Script for Speech Memorization Platform
# Run this script daily via cron job

set -e

# Configuration
BACKUP_DIR="/backups"
PROJECT_DIR="/app"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting backup process at $(date)"

# Database backup
if [ "$DB_ENGINE" = "postgresql" ]; then
    echo "Backing up PostgreSQL database..."
    PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    echo "Database backup completed: db_backup_$TIMESTAMP.sql"
else
    echo "Backing up SQLite database..."
    cp "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3" 2>/dev/null || true
    echo "SQLite backup completed: db_backup_$TIMESTAMP.sqlite3"
fi

# Media files backup
if [ -d "$PROJECT_DIR/media" ]; then
    echo "Backing up media files..."
    tar -czf "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" -C "$PROJECT_DIR" media/
    echo "Media backup completed: media_backup_$TIMESTAMP.tar.gz"
fi

# User uploaded texts backup
if [ -d "$PROJECT_DIR/uploads" ]; then
    echo "Backing up uploaded files..."
    tar -czf "$BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz" -C "$PROJECT_DIR" uploads/
    echo "Uploads backup completed: uploads_backup_$TIMESTAMP.tar.gz"
fi

# Configuration backup
echo "Backing up configuration files..."
tar -czf "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz" \
    -C "$PROJECT_DIR" \
    .env \
    docker-compose.prod.yml \
    nginx/nginx.conf 2>/dev/null || true
echo "Configuration backup completed: config_backup_$TIMESTAMP.tar.gz"

# Clean up old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "*backup_*.sql" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*backup_*.sqlite3" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Generate backup report
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "Backup completed at $(date)"
echo "Total backup size: $BACKUP_SIZE"
echo "Backup location: $BACKUP_DIR"

# Log backup completion
echo "$(date): Backup completed successfully" >> "$BACKUP_DIR/backup.log"