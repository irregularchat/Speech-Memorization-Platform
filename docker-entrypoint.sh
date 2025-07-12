#!/bin/bash

# Speech Memorization Platform - Docker Entrypoint
# This script handles database initialization and app setup

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎤 Speech Memorization Platform - Docker Entrypoint${NC}"
echo "========================================================"

# Function to wait for database
wait_for_db() {
    echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
    
    while ! python manage.py check --database default > /dev/null 2>&1; do
        echo -e "${YELLOW}Database not ready yet. Retrying in 5 seconds...${NC}"
        sleep 5
    done
    
    echo -e "${GREEN}✅ Database is ready!${NC}"
}

# Function to setup database
setup_database() {
    echo -e "${BLUE}🔧 Setting up database...${NC}"
    
    # Run migrations
    echo -e "${BLUE}Running database migrations...${NC}"
    python manage.py migrate --noinput
    
    # Create superuser if it doesn't exist
    if [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
        echo -e "${BLUE}Creating superuser...${NC}"
        python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        username='${DJANGO_SUPERUSER_USERNAME:-admin}',
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
    else
        # Create default admin user if no superuser exists
        echo -e "${BLUE}Creating default admin user...${NC}"
        python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print('Default admin user created with password: admin123')
else:
    # Ensure existing admin user has a password
    admin_user = User.objects.filter(username='admin').first()
    if admin_user and not admin_user.check_password('admin123'):
        admin_user.set_password('admin123')
        admin_user.save()
        print('Admin user password updated to: admin123')
    else:
        print('Admin user already exists with password')
"
    fi
    
    # Load initial data if specified
    if [ "$LOAD_INITIAL_DATA" = "true" ]; then
        echo -e "${BLUE}Loading initial data...${NC}"
        python manage.py loaddata initial_data.json 2>/dev/null || echo "No initial data found"
    fi
}

# Function to collect static files
collect_static() {
    echo -e "${BLUE}📁 Collecting static files...${NC}"
    python manage.py collectstatic --noinput --clear
}

# Function to run app
run_app() {
    echo -e "${GREEN}🚀 Starting application...${NC}"
    echo -e "${YELLOW}📝 Login credentials:${NC}"
    echo -e "${YELLOW}   Username: admin${NC}"
    echo -e "${YELLOW}   Password: admin123${NC}"
    echo -e "${YELLOW}   URL: http://localhost:8000/login/${NC}"
    
    if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ]; then
        echo -e "${YELLOW}Running in development mode${NC}"
        exec python manage.py runserver 0.0.0.0:8000
    else
        echo -e "${GREEN}Running in production mode${NC}"
        exec gunicorn \
            --bind 0.0.0.0:8000 \
            --workers 4 \
            --worker-class sync \
            --timeout 120 \
            --max-requests 1000 \
            --max-requests-jitter 100 \
            speech_memorization.wsgi:application
    fi
}

# Main execution
case "$1" in
    web)
        wait_for_db
        setup_database
        collect_static
        run_app
        ;;
    celery)
        wait_for_db
        echo -e "${GREEN}🔄 Starting Celery worker...${NC}"
        exec celery -A speech_memorization worker -l info --concurrency=2
        ;;
    celery-beat)
        wait_for_db
        echo -e "${GREEN}⏰ Starting Celery beat scheduler...${NC}"
        exec celery -A speech_memorization beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;
    migrate)
        wait_for_db
        setup_database
        echo -e "${GREEN}✅ Database migration completed${NC}"
        ;;
    test)
        wait_for_db
        echo -e "${BLUE}🧪 Running tests...${NC}"
        exec python manage.py test
        ;;
    bash)
        echo -e "${BLUE}🐚 Starting bash shell...${NC}"
        exec bash
        ;;
    *)
        echo -e "${GREEN}🎯 Executing command: $@${NC}"
        exec "$@"
        ;;
esac 