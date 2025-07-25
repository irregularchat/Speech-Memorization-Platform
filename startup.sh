#!/bin/bash

# Startup script for Django app on Google App Engine
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if needed..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
EOF

echo "Loading sample texts..."
python manage.py import_texts --military-only || echo "Sample texts already loaded or command failed"

echo "Starting application..."
exec "$@"