#!/bin/bash

# Speech Memorization Platform Production Deployment Script
set -e

echo "🚀 Starting Speech Memorization Platform deployment..."

# Configuration
DEPLOYMENT_ENV=${1:-production}
PROJECT_ROOT=$(pwd)
BACKUP_DIR="./backups"
CONFIG_DIR="./config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check environment file
    if [ ! -f ".env.${DEPLOYMENT_ENV}" ]; then
        log_error "Environment file .env.${DEPLOYMENT_ENV} not found."
        log_info "Please copy .env.${DEPLOYMENT_ENV}.example to .env.${DEPLOYMENT_ENV} and configure it."
        exit 1
    fi
    
    # Check Google Cloud credentials
    if [ ! -f "${CONFIG_DIR}/google-cloud-service-account.json" ]; then
        log_warning "Google Cloud service account file not found at ${CONFIG_DIR}/google-cloud-service-account.json"
        log_warning "Speech recognition may not work properly without Google Cloud credentials."
    fi
    
    log_success "All requirements check passed!"
}

# Backup existing data
backup_data() {
    log_info "Creating backup of existing data..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="${BACKUP_DIR}/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    # Backup database if running
    if docker-compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
        log_info "Backing up database..."
        docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $DATABASE_USER -d $DATABASE_NAME | gzip > "${BACKUP_DIR}/db_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
    fi
    
    # Backup media files
    if [ -d "./media" ]; then
        log_info "Backing up media files..."
        tar -czf "$BACKUP_FILE" ./media
        log_success "Backup created: $BACKUP_FILE"
    fi
}

# Build and deploy
deploy_application() {
    log_info "Deploying application..."
    
    # Load environment variables
    source ".env.${DEPLOYMENT_ENV}"
    
    # Build images
    log_info "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    log_info "Running database migrations..."
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput
    
    # Collect static files
    log_info "Collecting static files..."
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
    
    # Create superuser if it doesn't exist
    log_info "Creating superuser if needed..."
    docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"
    
    log_success "Application deployed successfully!"
}

# Health check
health_check() {
    log_info "Performing health checks..."
    
    # Check if services are running
    if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_error "Some services are not running properly"
        docker-compose -f docker-compose.prod.yml ps
        exit 1
    fi
    
    # Check web service health
    log_info "Checking web service health..."
    sleep 15  # Give time for services to start
    
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        log_success "Web service is healthy"
    else
        log_warning "Web service health check failed - this might be normal during startup"
    fi
    
    # Check Google Cloud Speech availability
    log_info "Checking Google Cloud Speech integration..."
    if docker-compose -f docker-compose.prod.yml exec -T web python -c "
from memorization.google_speech_service import GoogleSpeechBatchService
service = GoogleSpeechBatchService()
print('Google Speech available:', service.is_available())
"; then
        log_success "Google Cloud Speech integration check completed"
    else
        log_warning "Google Cloud Speech integration check failed"
    fi
}

# SSL setup
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    # Create SSL directory
    mkdir -p "${CONFIG_DIR}/ssl"
    
    if [ ! -f "${CONFIG_DIR}/ssl/cert.pem" ] || [ ! -f "${CONFIG_DIR}/ssl/key.pem" ]; then
        log_warning "SSL certificates not found. Generating self-signed certificates for development..."
        
        # Generate self-signed certificate
        openssl req -x509 -newkey rsa:4096 -keyout "${CONFIG_DIR}/ssl/key.pem" -out "${CONFIG_DIR}/ssl/cert.pem" -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        log_warning "Self-signed certificates generated. For production, replace with valid SSL certificates."
    else
        log_success "SSL certificates found"
    fi
}

# Monitoring setup
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create Prometheus config if it doesn't exist
    if [ ! -f "${CONFIG_DIR}/prometheus.yml" ]; then
        cat > "${CONFIG_DIR}/prometheus.yml" << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'django'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics/'
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
EOF
        log_success "Prometheus configuration created"
    fi
}

# Show deployment information
show_deployment_info() {
    log_success "🎉 Deployment completed successfully!"
    echo
    log_info "Application Information:"
    echo "  📊 Application URL: https://localhost (or your configured domain)"
    echo "  👤 Admin URL: https://localhost/admin/"
    echo "  🔑 Default admin credentials: admin / admin123"
    echo "  📈 Monitoring: http://localhost:9090 (Prometheus)"
    echo
    log_info "Useful Commands:"
    echo "  📋 View logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  🔄 Restart services: docker-compose -f docker-compose.prod.yml restart"
    echo "  🛑 Stop services: docker-compose -f docker-compose.prod.yml down"
    echo "  🗄️  Database shell: docker-compose -f docker-compose.prod.yml exec db psql -U \$DATABASE_USER -d \$DATABASE_NAME"
    echo
    log_warning "Important Notes:"
    echo "  • Change default admin password immediately"
    echo "  • Configure proper SSL certificates for production"
    echo "  • Set up regular backups"
    echo "  • Monitor application performance and logs"
    echo "  • Configure Google Cloud Speech API for full functionality"
}

# Main deployment process
main() {
    log_info "🎯 Speech Memorization Platform - Production Deployment"
    echo "   Environment: $DEPLOYMENT_ENV"
    echo "   Timestamp: $(date)"
    echo
    
    check_requirements
    backup_data
    setup_ssl
    setup_monitoring
    deploy_application
    health_check
    show_deployment_info
    
    log_success "✅ Deployment completed successfully!"
}

# Handle script arguments
case "$1" in
    "production"|"staging"|"")
        main
        ;;
    "health")
        health_check
        ;;
    "backup")
        backup_data
        ;;
    "ssl")
        setup_ssl
        ;;
    *)
        echo "Usage: $0 [production|staging|health|backup|ssl]"
        echo
        echo "Commands:"
        echo "  production  - Deploy to production (default)"
        echo "  staging     - Deploy to staging"
        echo "  health      - Run health checks only"
        echo "  backup      - Create backup only"
        echo "  ssl         - Set up SSL certificates only"
        exit 1
        ;;
esac