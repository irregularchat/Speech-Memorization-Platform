"""
Django settings for Google Cloud deployment
"""

import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
# Allow all hosts for Cloud Run (since we don't know the exact URL until deployment)
# This overrides any other ALLOWED_HOSTS setting completely
ALLOWED_HOSTS = ['*']

# Force logging and print to ensure visibility
import logging
import sys

# Force immediate output
print("=== CLOUD SETTINGS LOADING ===", file=sys.stderr, flush=True)
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}", file=sys.stderr, flush=True)
print(f"DEBUG: {DEBUG}", file=sys.stderr, flush=True)
print("=== CLOUD SETTINGS LOADED ===", file=sys.stderr, flush=True)

# Also add to logging
logger = logging.getLogger(__name__)
logger.error(f"CLOUD SETTINGS: ALLOWED_HOSTS set to: {ALLOWED_HOSTS}")
logger.error(f"CLOUD SETTINGS: DEBUG set to: {DEBUG}")

# Google Cloud specific settings
USE_CLOUD_SQL_AUTH_PROXY = config('USE_CLOUD_SQL_AUTH_PROXY', default=False, cast=bool)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # For static files
    'django.contrib.staticfiles',
    
    # Our apps
    'core',
    'memorization',
    'analytics',
    'users',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'speech_memorization.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'speech_memorization.wsgi.application'

# Database configuration for Google Cloud
DATABASE_URL = config('DATABASE_URL', default='')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # Fallback to SQLite for local development and Cloud Run
    import os
    
    # Use /tmp directory for Cloud Run to avoid read-only file system issues
    if os.environ.get('PORT'):  # Cloud Run sets PORT
        db_name = '/tmp/db.sqlite3'
        # Ensure /tmp directory exists
        os.makedirs('/tmp', exist_ok=True)
    else:
        db_name = BASE_DIR / 'db.sqlite3'
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_name,
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files configuration for Google Cloud
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Use WhiteNoise for static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files - use Google Cloud Storage for production
USE_GCS = config('USE_GCS', default=False, cast=bool)
if USE_GCS:
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = config('GS_BUCKET_NAME')
    GS_PROJECT_ID = config('GOOGLE_CLOUD_PROJECT_ID')
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# API Configuration
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

# Google Cloud Speech Configuration
GOOGLE_CLOUD_PROJECT_ID = config('GOOGLE_CLOUD_PROJECT_ID', default='')

# Google Cloud authentication
if not DEBUG:
    # In production, use default credentials (service account)
    import google.auth
    import logging
    logger = logging.getLogger(__name__)
    try:
        credentials, project = google.auth.default()
        GOOGLE_CLOUD_PROJECT_ID = project or GOOGLE_CLOUD_PROJECT_ID
    except Exception as e:
        logger.warning(f"Could not load Google Cloud credentials: {e}")

# Enable Google Cloud Speech API
GOOGLE_SPEECH_ENABLED = bool(GOOGLE_CLOUD_PROJECT_ID)

# Use in-memory cache for App Engine
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'speech-memorization-cache',
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Session configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    
    # CSRF settings for Cloud Run
    CSRF_TRUSTED_ORIGINS = [
        'https://*.run.app',  # Allow all Cloud Run domains
        'https://speech-memorization-496146455129.us-central1.run.app',
        'https://speech-memorization-nesvf2duwa-uc.a.run.app'
    ]

# Logging configuration for Google Cloud
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'memorization': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Email configuration (optional for Cloud Run)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

# Health check endpoint
HEALTH_CHECK_URL = '/health/'