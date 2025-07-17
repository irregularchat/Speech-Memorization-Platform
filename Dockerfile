FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=speech_memorization.settings_minimal

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install all dependencies
RUN pip install -r requirements.txt

# Copy app code
COPY . .

# Create static files directory and collect static
RUN mkdir -p staticfiles && \
    python manage.py collectstatic --noinput

# Run database migrations
RUN python manage.py migrate

# Create user and set permissions
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["gunicorn", "speech_memorization.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "1"]