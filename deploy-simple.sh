#!/bin/bash

# Simplified Google Cloud Run deployment for Speech Memorization Platform
set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT_ID:-serverless-test-12345}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="speech-memorization"

echo "🚀 Deploying Speech Memorization Platform to Google Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Set the active project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required Google Cloud APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    speech.googleapis.com

# Create Django secret key
echo "🔐 Creating Django secret..."
DJANGO_SECRET=$(openssl rand -base64 32)
echo $DJANGO_SECRET | gcloud secrets create django-secret --data-file=- || \
echo $DJANGO_SECRET | gcloud secrets versions add django-secret --data-file=-

# Create OpenAI secret
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "🤖 Creating OpenAI secret..."
    echo $OPENAI_API_KEY | gcloud secrets create openai-config --data-file=- || \
    echo $OPENAI_API_KEY | gcloud secrets versions add openai-config --data-file=-
fi

# Grant service account permissions
echo "🔑 Setting up service account permissions..."
SERVICE_ACCOUNT="speech-memorization-sa@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Grant access to secrets
for secret in django-secret openai-config; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" || true
done

# Build and deploy the application
echo "🔨 Building application container..."
gcloud builds submit --config=cloudbuild.yaml .

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --platform managed \
    --region $REGION \
    --service-account $SERVICE_ACCOUNT \
    --set-env-vars "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "DEBUG=False" \
    --set-env-vars "ALLOWED_HOSTS=*" \
    --set-secrets "SECRET_KEY=django-secret:latest" \
    --set-secrets "OPENAI_API_KEY=openai-config:latest" \
    --memory 2Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 5 \
    --min-instances 0 \
    --concurrency 100 \
    --allow-unauthenticated

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)")

echo "🎉 Deployment completed successfully!"
echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo "🏥 Health check: $SERVICE_URL/health/"
echo ""
echo "📋 Next steps:"
echo "1. Visit $SERVICE_URL to test the application"
echo "2. The app is using SQLite database (data will be ephemeral)"
echo "3. To persist data, set up Cloud SQL using the full deploy-cloud.sh script"
echo "4. Configure custom domain if needed"