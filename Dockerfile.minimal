FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=speech_memorization.settings_minimal

WORKDIR /app

# Install only essential dependencies
RUN pip install Django==5.2.4 gunicorn==23.0.0 whitenoise==6.8.2

# Copy app code
COPY . .

# Create static files directory and collect static
RUN mkdir -p staticfiles && \
    python manage.py collectstatic --noinput

# Create user and set permissions
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["gunicorn", "speech_memorization.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "1"]