"""
Entry point for Cloud Run deployment with database initialization
"""

import os
import django
from django.core.wsgi import get_wsgi_application
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'speech_memorization.settings_simple')

# Initialize Django
django.setup()

# Run migrations on startup (safe to run multiple times)
try:
    print("Running database migrations...")
    execute_from_command_line(['manage.py', 'migrate', '--noinput'])
    print("Migrations completed successfully")
except Exception as e:
    print(f"Migration warning: {e} - continuing with demo data")

# Get WSGI application
application = get_wsgi_application()

# For Cloud Run
app = application