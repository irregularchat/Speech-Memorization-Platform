# Speech Memorization Platform - Deployment Guide

## Overview

This guide walks you through deploying the Speech Memorization Platform to Google Cloud Run. The application is a Django-based web service that helps users memorize speeches and texts using spaced repetition techniques.

## Prerequisites

### 1. Google Cloud Account
- Active Google Cloud account with billing enabled
- Google Cloud CLI (`gcloud`) installed and configured
- Docker installed locally

### 2. Local Setup
```bash
# Clone the repository
git clone <repository-url>
cd Speech-Memorization-Platform

# Install Google Cloud CLI (if not already installed)
# macOS: brew install google-cloud-sdk
# Linux: Follow https://cloud.google.com/sdk/docs/install

# Authenticate with Google Cloud
gcloud auth login
gcloud auth configure-docker
```

### 3. Required APIs
Enable these Google Cloud APIs in your project:
- Cloud Run API
- Container Registry API
- Cloud Build API
- Secret Manager API

## Step-by-Step Deployment

### Step 1: Project Setup

```bash
# Create a new project (or use existing)
gcloud projects create speech-memorization-YOURNAME --name="Speech Memorization Platform"

# Set the project as default
gcloud config set project speech-memorization-YOURNAME

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing/linkedaccount?project=speech-memorization-YOURNAME
```

### Step 2: Enable Required APIs

```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### Step 3: Configure Dependencies

**Important**: Ensure all dependencies are uncommented in `requirements.txt`:

```txt
# Core Django
Django==5.2.4
python-decouple==3.8

# Database
psycopg2-binary==2.9.9
dj-database-url==3.0.1

# Web serving
gunicorn==23.0.0
whitenoise[brotli]==6.8.2

# Google Cloud
google-cloud-speech==2.33.0

# AI processing  
openai==1.59.3

# Core utilities
requests==2.32.4
python-dateutil==2.9.0.post0

# Audio processing (REQUIRED - don't comment out!)
numpy==1.26.4
librosa==0.10.2.post1

# Skip problematic audio libraries for initial deployment
# soundfile==0.12.1
# pyaudio==0.2.14
```

### Step 4: Build and Push Container

**For Apple Silicon Macs (M1/M2):**
```bash
# Build for correct architecture
docker buildx build --platform linux/amd64 \
  -t gcr.io/speech-memorization-YOURNAME/speech-memorization:latest \
  --push .
```

**For Intel/AMD machines:**
```bash
# Build and push
docker build -t gcr.io/speech-memorization-YOURNAME/speech-memorization:latest .
docker push gcr.io/speech-memorization-YOURNAME/speech-memorization:latest
```

### Step 5: Deploy to Cloud Run

```bash
# Deploy the service
gcloud run deploy speech-memorization \
  --image gcr.io/speech-memorization-YOURNAME/speech-memorization:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

**Note**: If you get an organization policy error, see the troubleshooting section below.

### Step 6: Make Service Publicly Accessible

If the `--allow-unauthenticated` flag fails due to organization policies:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **Cloud Run** → **Services**
3. Click on your `speech-memorization` service
4. Go to the **Security** tab
5. **Uncheck** "IAM authentication" for incoming requests
6. Click **Save**

## Troubleshooting

### 1. Organization Policy Errors

**Error**: `FAILED_PRECONDITION: One or more users named in the policy do not belong to a permitted customer`

**Solution**: 
- Use the Google Cloud Console method above
- Or contact your organization admin to modify the `constraints/iam.allowedPolicyMemberDomains` policy

### 2. Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'librosa'`

**Solution**:
- Ensure all dependencies in `requirements.txt` are uncommented
- Rebuild the container with all dependencies

### 3. Architecture Mismatch

**Error**: Cloud Run rejecting container image

**Solution**:
- Use `docker buildx build --platform linux/amd64` for Apple Silicon Macs
- Ensure you're building for the correct target architecture

### 4. Database Migration Issues

**Error**: Django migrations failing during build

**Solution**:
- Ensure all dependencies are installed before running migrations
- Check that the Dockerfile includes the migration step

### 5. Disk Space Issues

**Error**: `no space left on device`

**Solution**:
```bash
# Clean up Docker
docker system prune -a --volumes

# Check available disk space
df -h
```

## Configuration

### Environment Variables

The application uses these environment variables (set in Cloud Run):

- `DJANGO_SETTINGS_MODULE`: `speech_memorization.settings_minimal`
- `SECRET_KEY`: Django secret key
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `GOOGLE_CLOUD_PROJECT_ID`: Your Google Cloud project ID

### Settings Files

- `settings_minimal.py`: For Cloud Run deployment (SQLite database)
- `settings_cloud.py`: For full cloud deployment (Cloud SQL)
- `settings.py`: For local development

## Monitoring and Maintenance

### View Logs
```bash
gcloud logs read --service=speech-memorization --limit=50
```

### Check Service Status
```bash
gcloud run services describe speech-memorization --region=us-central1
```

### Update Deployment
```bash
# Rebuild and redeploy
docker buildx build --platform linux/amd64 \
  -t gcr.io/speech-memorization-YOURNAME/speech-memorization:latest \
  --push .

gcloud run deploy speech-memorization \
  --image gcr.io/speech-memorization-YOURNAME/speech-memorization:latest \
  --region us-central1
```

## Cost Optimization

### Cloud Run Settings
- **Min instances**: 0 (scale to zero when not in use)
- **Max instances**: 5 (prevent runaway costs)
- **Memory**: 512Mi (sufficient for speech processing)
- **CPU**: 1 (adequate for most workloads)

### Monitoring Costs
- Set up billing alerts in Google Cloud Console
- Monitor usage in Cloud Run metrics
- Review costs monthly

## Security Considerations

### Current Security Features
- HTTPS-only communication
- CSRF protection enabled
- Secure headers configured
- No secrets in container images

### Recommended Enhancements
- Set up Cloud Armor for DDoS protection
- Configure VPC for private networking
- Implement proper user authentication
- Set up audit logging

## Development Workflow

### Local Development
```bash
# Run locally with Docker
docker build -t speech-memorization .
docker run -p 8000:8080 speech-memorization

# Or run with Django development server
python manage.py runserver
```

### Testing Before Deployment
```bash
# Run tests
python manage.py test

# Check for issues
python manage.py check --deploy
```

## Support and Resources

### Documentation
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Community
- [Matrix Chat Room](https://matrix.to/#/%23speech-memorization-platform:irregularchat.com)
- GitHub Issues for bug reports
- Pull requests welcome

## Quick Deployment Script

Create a `deploy.sh` script for easy redeployment:

```bash
#!/bin/bash
set -e

PROJECT_ID="speech-memorization-YOURNAME"
REGION="us-central1"
SERVICE_NAME="speech-memorization"

echo "Building and pushing container..."
docker buildx build --platform linux/amd64 \
  -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --push .

echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --region $REGION \
  --platform managed

echo "Deployment complete!"
echo "Service URL: $(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')"
```

Make it executable:
```bash
chmod +x deploy.sh
./deploy.sh
```

## Conclusion

This deployment guide covers the essential steps to get the Speech Memorization Platform running on Google Cloud Run. The application is designed to be cost-effective, scalable, and secure for production use.

For advanced features like Cloud SQL integration, Redis caching, and custom domains, refer to the full deployment documentation in the project repository.

Happy deploying! 🚀 