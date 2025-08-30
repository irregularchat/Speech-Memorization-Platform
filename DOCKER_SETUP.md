# Docker Setup Guide for Speech Memorization Platform

This guide will help you set up the Speech Memorization Platform using Docker and Docker Compose.

## Prerequisites

- Docker Desktop installed on your system
- Docker Compose (included with Docker Desktop)
- OpenAI API Key (for AI features)

## Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   git clone <repository-url>
   cd Speech-Memorization-Platform
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file and set your OpenAI API key and other configurations
   ```

3. **Start the application:**
   ```bash
   docker-compose up -d --build
   ```

4. **Access the application:**
   - Web application: http://localhost:8000
   - Django admin: http://localhost:8000/admin/

## Environment Variables

The application uses the following environment variables (defined in `.env`):

### Required
- `OPENAI_API_KEY` - Your OpenAI API key for AI features

### Optional (with defaults)
- `DEBUG` - Enable debug mode (default: False)
- `SECRET_KEY` - Django secret key (generate a secure one for production)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts (default: localhost,127.0.0.1,0.0.0.0)
- `DB_NAME` - Database name (default: speech_memorization)
- `DB_USER` - Database user (default: speech_user)
- `DB_PASSWORD` - Database password (default: speech_password)
- `PORT` - Web server port (default: 8000)

## Docker Services

The application consists of the following services:

### Core Services (always running)
- **web** - Django application server
- **postgres** - PostgreSQL database
- **redis** - Redis cache and session store

### Optional Services (use profiles to enable)
- **nginx** - Reverse proxy (production profile)
- **celery** - Background task processor (background-tasks profile)
- **celery-beat** - Periodic task scheduler (background-tasks profile)

## Using the Helper Script

The `docker-start.sh` script provides convenient commands:

```bash
# Make it executable
chmod +x docker-start.sh

# Start development environment
./docker-start.sh up

# Start with production profile (includes nginx)
./docker-start.sh prod

# Show logs
./docker-start.sh logs

# Open shell in web container
./docker-start.sh shell

# Run database migrations
./docker-start.sh migrate

# Run tests
./docker-start.sh test

# Stop all services
./docker-start.sh down

# Clean up all containers and volumes
./docker-start.sh clean
```

## Common Commands

### Start all services
```bash
docker-compose up -d --build
```

### Stop all services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f web
```

### Run Django commands
```bash
docker-compose exec web python manage.py [command]
```

### Access database
```bash
docker-compose exec postgres psql -U speech_user -d speech_memorization
```

### Access Redis
```bash
docker-compose exec redis redis-cli
```

## Development Setup

For development, you can mount your code as read-write:

```bash
# Set environment variables for development
export DEBUG=true
export BUILD_TARGET=development
export MOUNT_MODE=rw

# Start with development settings
docker-compose up -d --build
```

## Production Setup

For production deployment:

1. **Set production environment variables:**
   ```bash
   # In .env file
   DEBUG=False
   SECRET_KEY=your-secure-secret-key
   SECURE_SSL_REDIRECT=True
   SECURE_HSTS_SECONDS=31536000
   DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
   DJANGO_SUPERUSER_PASSWORD=secure-password
   ```

2. **Start with production profile:**
   ```bash
   ./docker-start.sh prod
   ```

3. **The application will be available at:**
   - Direct access: http://localhost:8000
   - Through nginx: http://localhost

## Profiles

Use Docker Compose profiles to enable additional services:

### Production Profile
```bash
docker-compose --profile production up -d --build
```
Includes: nginx reverse proxy

### Background Tasks Profile
```bash
docker-compose --profile background-tasks up -d --build
```
Includes: celery worker and celery beat scheduler

### All Profiles
```bash
docker-compose --profile production --profile background-tasks up -d --build
```

## Volumes

The application uses the following Docker volumes for persistent data:

- `postgres_data` - Database files
- `redis_data` - Redis persistence
- `media_files` - User uploaded files
- `static_files` - Static assets
- `log_files` - Application logs
- `audio_temp` - Temporary audio processing files

## Ports

Default port mapping:
- **8000** - Web application
- **5432** - PostgreSQL (for external connections)
- **6379** - Redis (for external connections)
- **80** - Nginx (production profile only)
- **443** - Nginx HTTPS (production profile only)

## Troubleshooting

### Check service status
```bash
docker-compose ps
```

### Check logs for errors
```bash
docker-compose logs web
docker-compose logs postgres
docker-compose logs redis
```

### Reset database
```bash
docker-compose down -v
docker-compose up -d --build
```

### Access web container shell
```bash
docker-compose exec web bash
```

### Check Django configuration
```bash
docker-compose exec web python manage.py check
```

## Health Checks

All services include health checks:
- **postgres** - `pg_isready` command
- **redis** - `redis-cli ping`
- **web** - Django system check

Services will show as "healthy" when ready to accept connections.

## Development Features

When running in development mode (`DEBUG=True`):
- Django debug toolbar is available
- Live code reloading (with `MOUNT_MODE=rw`)
- Detailed error pages
- Development server instead of Gunicorn

## Security Notes

- Always use strong passwords in production
- Set `DEBUG=False` in production
- Use HTTPS in production
- Regularly update Docker images
- Monitor container resources

## Support

For issues or questions, please refer to the main README.md or create an issue in the repository. 