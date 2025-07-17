#!/bin/bash

# Speech Memorization Platform - Google Cloud Deployment Script
set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT_ID:-serverless-test-12345}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="speech-memorization"
DATABASE_INSTANCE_NAME="speech-memorization-db"
REDIS_INSTANCE_NAME="speech-memorization-redis"

echo "🚀 Deploying Speech Memorization Platform to Google Cloud"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Set the active project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required Google Cloud APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    storage-component.googleapis.com \
    storage.googleapis.com \
    speech.googleapis.com \
    secretmanager.googleapis.com

# Create Cloud SQL instance for PostgreSQL
echo "🗄️ Creating Cloud SQL PostgreSQL instance..."
if ! gcloud sql instances describe $DATABASE_INSTANCE_NAME --quiet 2>/dev/null; then
    gcloud sql instances create $DATABASE_INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-auto-increase \
        --storage-size=10GB \
        --storage-type=SSD \
        --backup-start-time=03:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --deletion-protection
        
    echo "✅ Cloud SQL instance created"
else
    echo "✅ Cloud SQL instance already exists"
fi

# Create database and user
echo "📊 Setting up database and user..."
gcloud sql databases create speech_memorization --instance=$DATABASE_INSTANCE_NAME || true
gcloud sql users create speech_user --instance=$DATABASE_INSTANCE_NAME --password=speech_password || true

# Create Redis instance
echo "🔴 Creating Redis instance..."
if ! gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --quiet 2>/dev/null; then
    gcloud redis instances create $REDIS_INSTANCE_NAME \
        --size=1 \
        --region=$REGION \
        --redis-version=redis_6_x \
        --tier=basic \
        --network=default
        
    echo "✅ Redis instance created"
else
    echo "✅ Redis instance already exists"
fi

# Create storage bucket for media files
echo "📦 Creating storage bucket..."
BUCKET_NAME="${PROJECT_ID}-speech-memorization-media"
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME/ || true
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME || true

# Create secrets
echo "🔐 Creating secrets..."

# Generate Django secret key
DJANGO_SECRET=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
echo $DJANGO_SECRET | gcloud secrets create django-secret --data-file=- || \
echo $DJANGO_SECRET | gcloud secrets versions add django-secret --data-file=-

# Database URL
DB_CONNECTION_NAME=$(gcloud sql instances describe $DATABASE_INSTANCE_NAME --format="value(connectionName)")
DATABASE_URL="postgresql://speech_user:speech_password@/$DATABASE_INSTANCE_NAME?host=/cloudsql/$DB_CONNECTION_NAME"
echo $DATABASE_URL | gcloud secrets create database-config --data-file=- || \
echo $DATABASE_URL | gcloud secrets versions add database-config --data-file=-

# Redis URL
REDIS_IP=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REGION --format="value(host)")
REDIS_URL="redis://$REDIS_IP:6379/0"
echo $REDIS_URL | gcloud secrets create redis-config --data-file=- || \
echo $REDIS_URL | gcloud secrets versions add redis-config --data-file=-

# OpenAI API Key (you'll need to set this manually)
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo $OPENAI_API_KEY | gcloud secrets create openai-config --data-file=- || \
    echo $OPENAI_API_KEY | gcloud secrets versions add openai-config --data-file=-
else
    echo "⚠️ OPENAI_API_KEY not set. Please create the secret manually:"
    echo "echo 'your-openai-api-key' | gcloud secrets create openai-config --data-file=-"
fi

# Update service account permissions
echo "🔑 Setting up service account permissions..."
SERVICE_ACCOUNT="speech-memorization-sa@$PROJECT_ID.iam.gserviceaccount.com"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/redis.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Grant access to secrets
for secret in django-secret database-config redis-config openai-config; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" || true
done

# Build and deploy the application
echo "🔨 Building application container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:latest --file Dockerfile.cloud .

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --platform managed \
    --region $REGION \
    --service-account $SERVICE_ACCOUNT \
    --add-cloudsql-instances $DB_CONNECTION_NAME \
    --set-env-vars "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "USE_GCS=True" \
    --set-env-vars "GS_BUCKET_NAME=$BUCKET_NAME" \
    --set-secrets "SECRET_KEY=django-secret:latest" \
    --set-secrets "DATABASE_URL=database-config:latest" \
    --set-secrets "REDIS_URL=redis-config:latest" \
    --set-secrets "OPENAI_API_KEY=openai-config:latest" \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1 \
    --concurrency 100 \
    --allow-unauthenticated

# Run database migrations
echo "🔄 Running database migrations..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)")

# Get a one-time migration job running
gcloud run jobs create migrate-db \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --region $REGION \
    --service-account $SERVICE_ACCOUNT \
    --add-cloudsql-instances $DB_CONNECTION_NAME \
    --set-env-vars "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID" \
    --set-secrets "SECRET_KEY=django-secret:latest" \
    --set-secrets "DATABASE_URL=database-config:latest" \
    --set-secrets "REDIS_URL=redis-config:latest" \
    --command "python" \
    --args "manage.py,migrate,--settings=speech_memorization.settings_cloud" \
    --memory 2Gi \
    --cpu 1 \
    --task-timeout 300 \
    --parallelism 1 \
    --task-count 1 || true

gcloud run jobs execute migrate-db --region $REGION --wait

# Import military creeds
echo "🪖 Importing military creeds..."
gcloud run jobs create import-creeds \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --region $REGION \
    --service-account $SERVICE_ACCOUNT \
    --add-cloudsql-instances $DB_CONNECTION_NAME \
    --set-env-vars "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID" \
    --set-secrets "SECRET_KEY=django-secret:latest" \
    --set-secrets "DATABASE_URL=database-config:latest" \
    --set-secrets "REDIS_URL=redis-config:latest" \
    --command "python" \
    --args "manage.py,import_texts,--military-only,--settings=speech_memorization.settings_cloud" \
    --memory 2Gi \
    --cpu 1 \
    --task-timeout 300 \
    --parallelism 1 \
    --task-count 1 || true

gcloud run jobs execute import-creeds --region $REGION --wait

echo "🎉 Deployment completed successfully!"
echo ""
echo "Service URL: $SERVICE_URL"
echo "Admin interface: $SERVICE_URL/admin/"
echo ""
echo "📋 Next steps:"
echo "1. Visit the service URL to test the application"
echo "2. Create a superuser: gcloud run jobs create create-superuser ..."
echo "3. Configure custom domain if needed"
echo "4. Set up monitoring and alerts"
echo ""
echo "💰 Cost optimization tips:"
echo "- Monitor usage in Cloud Console"
echo "- Consider scaling down instances during low usage"
echo "- Review and optimize database and Redis tiers"