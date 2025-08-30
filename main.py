"""
Entry point for Cloud Run deployment
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'speech_memorization.settings_minimal')

application = get_wsgi_application()

# For Cloud Run
app = application