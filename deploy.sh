#!/bin/bash

# Speech Memorization Platform - Quick Deploy Script
# This script automates the deployment process to Google Cloud Run

set -e  # Exit on any error

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID:-"speech-memorization"}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"speech-memorization"}
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI (gcloud) is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if user is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "You are not authenticated with Google Cloud. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    # Check if project exists and user has access
    if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        log_error "Project '$PROJECT_ID' does not exist or you don't have access to it."
        log_info "Available projects:"
        gcloud projects list --format="table(projectId,name)"
        exit 1
    fi
    
    log_success "Prerequisites check passed!"
}

# Set up project
setup_project() {
    log_info "Setting up project '$PROJECT_ID'..."
    
    # Set the project
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    log_info "Enabling required APIs..."
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    
    # Configure Docker for Google Cloud
    gcloud auth configure-docker --quiet
    
    log_success "Project setup complete!"
}

# Build and push Docker image
build_and_push() {
    log_info "Building and pushing Docker image..."
    
    # Detect architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
        log_info "Detected Apple Silicon (ARM64). Building for linux/amd64..."
        docker buildx build --platform linux/amd64 -t "$IMAGE_NAME" --push .
    else
        log_info "Building for current architecture..."
        docker build -t "$IMAGE_NAME" .
        docker push "$IMAGE_NAME"
    fi
    
    log_success "Docker image built and pushed successfully!"
}

# Deploy to Cloud Run
deploy() {
    log_info "Deploying to Cloud Run..."
    
    # Deploy the service
    gcloud run deploy "$SERVICE_NAME" \
        --image "$IMAGE_NAME" \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --memory 512Mi \
        --cpu 1 \
        --max-instances 5 \
        --min-instances 0
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    
    log_success "Deployment successful!"
    log_info "Service URL: $SERVICE_URL"
    
    # Check if service is accessible
    log_info "Testing service accessibility..."
    if curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL" | grep -q "200\|403"; then
        log_success "Service is responding!"
        log_warning "If you see a 403 error, you may need to disable IAM authentication manually:"
        log_info "1. Go to Google Cloud Console → Cloud Run → Services"
        log_info "2. Click on '$SERVICE_NAME'"
        log_info "3. Go to Security tab"
        log_info "4. Uncheck 'IAM authentication' for incoming requests"
        log_info "5. Click Save"
    else
        log_error "Service is not responding. Check the logs:"
        log_info "gcloud logs read --service=$SERVICE_NAME --limit=20"
    fi
}

# Main deployment function
main() {
    echo "🚀 Speech Memorization Platform - Deployment Script"
    echo "=================================================="
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Service Name: $SERVICE_NAME"
    echo ""
    
    # Check if user wants to proceed
    read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled."
        exit 0
    fi
    
    # Run deployment steps
    check_prerequisites
    setup_project
    build_and_push
    deploy
    
    echo ""
    log_success "🎉 Deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    log_info "1. Visit your service URL to test the application"
    log_info "2. Set up environment variables in Cloud Run if needed"
    log_info "3. Configure custom domain (optional)"
    log_info "4. Set up monitoring and alerts"
    echo ""
    log_info "For troubleshooting, see DEPLOYMENT_GUIDE.md"
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --project-id PROJECT_ID    Google Cloud project ID (default: speech-memorization)"
            echo "  --region REGION           Google Cloud region (default: us-central1)"
            echo "  --service-name NAME       Cloud Run service name (default: speech-memorization)"
            echo "  --help                    Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  GOOGLE_CLOUD_PROJECT_ID   Google Cloud project ID"
            echo "  GOOGLE_CLOUD_REGION       Google Cloud region"
            echo "  SERVICE_NAME              Cloud Run service name"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Update IMAGE_NAME with potentially new PROJECT_ID
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

# Run main function
main