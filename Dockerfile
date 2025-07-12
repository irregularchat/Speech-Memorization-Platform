# Multi-stage build for Speech Memorization Platform with AI
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for AI processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    gcc \
    g++ \
    # Audio processing libraries
    libsndfile1-dev \
    libsndfile1 \
    portaudio19-dev \
    libasound2-dev \
    pulseaudio \
    # FFmpeg for audio format conversion
    ffmpeg \
    # SSL and compression
    libssl-dev \
    libffi-dev \
    zlib1g-dev \
    # PostgreSQL client
    libpq-dev \
    # Git for potential package installations
    git \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs media static staticfiles && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python manage.py check --deploy || exit 1

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["web"]

# Development stage
FROM base as development

USER root

# Install development dependencies
RUN pip install django-debug-toolbar ipython

# Switch back to app user
USER appuser

# Development command
CMD ["web"]