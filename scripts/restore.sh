#!/bin/bash

# Database and Media Restore Script for Speech Memorization Platform
# Usage: ./restore.sh <backup_timestamp>

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_timestamp>"
    echo "Example: $0 20241217_143000"
    echo ""
    echo "Available backups:"
    ls -la /backups/*backup_* 2>/dev/null | grep -E "(\.sql|\.sqlite3|\.tar\.gz)$" || echo "No backups found"
    exit 1
fi

BACKUP_TIMESTAMP="$1"
BACKUP_DIR="/backups"
PROJECT_DIR="/app"

echo "Starting restore process for backup: $BACKUP_TIMESTAMP"

# Stop services before restore
echo "Stopping services..."
docker-compose -f docker-compose.prod.yml down

# Database restore
if [ "$DB_ENGINE" = "postgresql" ]; then
    DB_BACKUP="$BACKUP_DIR/db_backup_$BACKUP_TIMESTAMP.sql"
    if [ -f "$DB_BACKUP" ]; then
        echo "Restoring PostgreSQL database from $DB_BACKUP..."
        
        # Drop and recreate database
        PGPASSWORD="$DB_PASSWORD" dropdb -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" --if-exists
        PGPASSWORD="$DB_PASSWORD" createdb -h "$DB_HOST" -U "$DB_USER" "$DB_NAME"
        
        # Restore from backup
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" < "$DB_BACKUP"
        echo "Database restore completed"
    else
        echo "Warning: Database backup not found: $DB_BACKUP"
    fi
else
    SQLITE_BACKUP="$BACKUP_DIR/db_backup_$BACKUP_TIMESTAMP.sqlite3"
    if [ -f "$SQLITE_BACKUP" ]; then
        echo "Restoring SQLite database from $SQLITE_BACKUP..."
        cp "$SQLITE_BACKUP" "$PROJECT_DIR/db.sqlite3"
        echo "SQLite restore completed"
    else
        echo "Warning: SQLite backup not found: $SQLITE_BACKUP"
    fi
fi

# Media files restore
MEDIA_BACKUP="$BACKUP_DIR/media_backup_$BACKUP_TIMESTAMP.tar.gz"
if [ -f "$MEDIA_BACKUP" ]; then
    echo "Restoring media files from $MEDIA_BACKUP..."
    rm -rf "$PROJECT_DIR/media"
    tar -xzf "$MEDIA_BACKUP" -C "$PROJECT_DIR"
    echo "Media files restore completed"
else
    echo "Warning: Media backup not found: $MEDIA_BACKUP"
fi

# Uploads restore
UPLOADS_BACKUP="$BACKUP_DIR/uploads_backup_$BACKUP_TIMESTAMP.tar.gz"
if [ -f "$UPLOADS_BACKUP" ]; then
    echo "Restoring uploaded files from $UPLOADS_BACKUP..."
    rm -rf "$PROJECT_DIR/uploads"
    tar -xzf "$UPLOADS_BACKUP" -C "$PROJECT_DIR"
    echo "Uploads restore completed"
else
    echo "Warning: Uploads backup not found: $UPLOADS_BACKUP"
fi

# Configuration restore
CONFIG_BACKUP="$BACKUP_DIR/config_backup_$BACKUP_TIMESTAMP.tar.gz"
if [ -f "$CONFIG_BACKUP" ]; then
    echo "Restoring configuration from $CONFIG_BACKUP..."
    tar -xzf "$CONFIG_BACKUP" -C "$PROJECT_DIR"
    echo "Configuration restore completed"
else
    echo "Warning: Configuration backup not found: $CONFIG_BACKUP"
fi

# Fix permissions
echo "Fixing file permissions..."
chown -R 1000:1000 "$PROJECT_DIR/media" 2>/dev/null || true
chown -R 1000:1000 "$PROJECT_DIR/uploads" 2>/dev/null || true
chmod 644 "$PROJECT_DIR/db.sqlite3" 2>/dev/null || true

# Start services
echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo "Restore completed at $(date)"
echo "Services are starting up..."

# Log restore completion
echo "$(date): Restore completed for backup $BACKUP_TIMESTAMP" >> "$BACKUP_DIR/restore.log"