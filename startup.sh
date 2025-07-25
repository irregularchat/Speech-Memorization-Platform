#!/bin/bash

# Startup script for Django app on Google App Engine
set +e  # Don't exit on errors

echo "Running database migrations..."
python manage.py migrate --noinput || echo "Migration failed, continuing..."

echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Static collection failed, continuing..."

echo "Creating superuser if needed..."
python manage.py shell << EOF || echo "Superuser creation failed, continuing..."
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print('Superuser created')
    else:
        print('Superuser already exists')
except Exception as e:
    print(f'Error creating superuser: {e}')
EOF

echo "Loading sample texts..."
python manage.py import_texts --military-only || echo "Sample texts loading failed, continuing..."

echo "Starting application..."
exec "$@"