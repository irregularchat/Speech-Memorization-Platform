#!/usr/bin/env python
"""
Startup script for Speech Memorization Platform on Cloud Run
Runs database migrations and starts the application
"""
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings

def main():
    """Run migrations and start application"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'speech_memorization.settings_simple')
    
    try:
        django.setup()
        
        # Run migrations
        print("Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Collect static files
        print("Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        
        print("Startup complete!")
        
    except Exception as e:
        print(f"Startup error: {e}")
        # Continue anyway - app might still work with demo data
    
    # Start the WSGI application (this would be done by gunicorn)
    print("Application ready!")

if __name__ == '__main__':
    main()