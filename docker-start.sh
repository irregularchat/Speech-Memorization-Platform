#!/bin/bash

# Speech Memorization Platform - Docker Setup Script
# This script helps users set up and run the Docker environment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎤 Speech Memorization Platform - Docker Setup${NC}"
echo "========================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Please create one based on .env.example${NC}"
    if [ -f .env.example ]; then
        echo -e "${BLUE}Creating .env file from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env file and set your environment variables${NC}"
        echo -e "${YELLOW}Important: Set your OPENAI_API_KEY in the .env file${NC}"
    else
        echo -e "${RED}❌ .env.example file not found. Please create .env file manually${NC}"
        exit 1
    fi
fi

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage: $0 [OPTION]${NC}"
    echo ""
    echo "Options:"
    echo "  up          Start all services (default)"
    echo "  down        Stop all services"
    echo "  build       Build and start services"
    echo "  logs        Show logs"
    echo "  shell       Open shell in web container"
    echo "  migrate     Run database migrations"
    echo "  test        Run tests"
    echo "  prod        Start with production profile (includes nginx)"
    echo "  clean       Clean up containers and volumes"
    echo "  help        Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  DEBUG=true           Enable debug mode"
    echo "  BUILD_TARGET=development  Use development build"
    echo "  MOUNT_MODE=rw        Mount code as read-write for development"
    echo ""
    echo "Examples:"
    echo "  $0 up                # Start development environment"
    echo "  $0 build             # Build and start services"
    echo "  $0 prod              # Start production environment with nginx"
    echo "  DEBUG=true $0 up     # Start with debug mode"
}

# Function to start services
start_services() {
    local profile=${1:-""}
    local extra_args=${2:-""}
    
    echo -e "${BLUE}🚀 Starting services...${NC}"
    
    if [ "$profile" = "prod" ]; then
        docker-compose --profile production up -d --build $extra_args
        echo -e "${GREEN}✅ Production services started${NC}"
        echo -e "${BLUE}🌐 Application available at: http://localhost${NC}"
    else
        docker-compose up -d --build $extra_args
        echo -e "${GREEN}✅ Development services started${NC}"
        echo -e "${BLUE}🌐 Application available at: http://localhost:8000${NC}"
    fi
}

# Function to stop services
stop_services() {
    echo -e "${BLUE}🛑 Stopping services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}📋 Showing logs...${NC}"
    docker-compose logs -f
}

# Function to open shell
open_shell() {
    echo -e "${BLUE}🐚 Opening shell in web container...${NC}"
    docker-compose exec web bash
}

# Function to run migrations
run_migrations() {
    echo -e "${BLUE}🔧 Running database migrations...${NC}"
    docker-compose exec web python manage.py migrate
    echo -e "${GREEN}✅ Migrations completed${NC}"
}

# Function to run tests
run_tests() {
    echo -e "${BLUE}🧪 Running tests...${NC}"
    docker-compose exec web python manage.py test
}

# Function to clean up
clean_up() {
    echo -e "${YELLOW}⚠️  This will remove all containers and volumes. Are you sure? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🧹 Cleaning up...${NC}"
        docker-compose down -v --remove-orphans
        docker system prune -f
        echo -e "${GREEN}✅ Cleanup completed${NC}"
    else
        echo -e "${BLUE}ℹ️  Cleanup cancelled${NC}"
    fi
}

# Parse command line arguments
case "${1:-up}" in
    up)
        start_services
        ;;
    down)
        stop_services
        ;;
    build)
        start_services "" "--build"
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    migrate)
        run_migrations
        ;;
    test)
        run_tests
        ;;
    prod)
        start_services "prod"
        ;;
    clean)
        clean_up
        ;;
    help)
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        show_usage
        exit 1
        ;;
esac 