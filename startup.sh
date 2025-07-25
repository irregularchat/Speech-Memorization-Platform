#!/bin/bash
set -e  # Exit on any error

echo "Starting application startup script..."

# Use main settings with Cloud Run detection
export DJANGO_SETTINGS_MODULE=speech_memorization.settings

# Debug: Show which settings are being used
echo "Environment variables:"
echo "PORT=$PORT"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

# Test settings loading
echo "Testing Django settings..."
python -c "
import django
from django.conf import settings
django.setup()
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
print('DEBUG:', settings.DEBUG)
print('Database NAME:', settings.DATABASES['default']['NAME'])
"

# Function to retry operations
retry() {
    local retries=$1
    shift
    local count=0
    until "$@"; do
        exit=$?
        wait=$((2 ** $count))
        count=$(($count + 1))
        if [ $count -lt $retries ]; then
            echo "Retry $count/$retries exited $exit, retrying in $wait seconds..."
            sleep $wait
        else
            echo "Retry $count/$retries exited $exit, no more retries left."
            return $exit
        fi
    done
    return 0
}

# Create database directory if needed
if [ ! -z "$PORT" ]; then
    echo "Running in Cloud Run environment..."
    mkdir -p /tmp
fi

# Run database migrations with retry
echo "Running database migrations..."
retry 5 python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "Creating default superuser if needed..."
python manage.py shell << EOF
import os
from django.contrib.auth.models import User
from django.db import IntegrityError

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@speechmemorization.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'speech_admin_2024')

try:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"Superuser '{username}' created successfully.")
    else:
        print(f"Superuser '{username}' already exists.")
except IntegrityError as e:
    print(f"Error creating superuser: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
EOF

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Startup script completed successfully."

# Start the server
exec "$@"