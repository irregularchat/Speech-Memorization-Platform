FROM python:3.11-slim

WORKDIR /app

# Copy just what we need
COPY requirements.txt* ./
COPY speech_memorization/ ./speech_memorization/
COPY core/ ./core/
COPY templates/ ./templates/
COPY static/ ./static/
COPY manage.py ./

# Install minimal dependencies
RUN pip install Django==5.2.4 gunicorn==23.0.0 whitenoise==6.8.2

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=speech_memorization.settings_minimal
ENV DEBUG=True
ENV PORT=8080

# Create staticfiles directory
RUN python manage.py collectstatic --noinput --settings=speech_memorization.settings_minimal || true

EXPOSE 8080

CMD ["gunicorn", "speech_memorization.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "30"]