#!/bin/bash

# Deploy Speech Memorization Platform with Google Cloud Speech API
# This script enables the Speech API and deploys with proper service account

set -e

echo "🚀 Deploying Speech Memorization Platform with Google Cloud Speech API..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No Google Cloud project is set"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Using project: $PROJECT_ID"

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable speech.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create service account for Cloud Run
SERVICE_ACCOUNT_NAME="speech-memorization-service"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "👤 Creating service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    echo "Creating new service account..."
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Speech Memorization Service Account" \
        --description="Service account for Speech Memorization Platform"
    
    # Wait a moment for service account to propagate
    echo "⏳ Waiting for service account to propagate..."
    sleep 5
else
    echo "✅ Service account already exists"
fi

# Grant necessary permissions to service account
echo "🔐 Setting up service account permissions..."

# Check and add Speech API role
if ! gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT_EMAIL} AND bindings.role:roles/speech.client" | grep -q "roles/speech.client"; then
    echo "Adding Speech API client role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="roles/speech.client"
else
    echo "✅ Speech API role already granted"
fi

# Check and add Secret Manager role
if ! gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT_EMAIL} AND bindings.role:roles/secretmanager.secretAccessor" | grep -q "roles/secretmanager.secretAccessor"; then
    echo "Adding Secret Manager accessor role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="roles/secretmanager.secretAccessor"
else
    echo "✅ Secret Manager role already granted"
fi

# Check and add Cloud SQL role
if ! gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT_EMAIL} AND bindings.role:roles/cloudsql.client" | grep -q "roles/cloudsql.client"; then
    echo "Adding Cloud SQL client role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="roles/cloudsql.client"
else
    echo "✅ Cloud SQL role already granted"
fi

# Build and deploy
echo "🏗️ Building and deploying application..."

# Build the container
gcloud builds submit --config cloudbuild.yaml .

# Deploy to Cloud Run with service account
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy speech-memorization \
    --image gcr.io/$PROJECT_ID/speech-memorization:latest \
    --platform managed \
    --region us-central1 \
    --service-account $SERVICE_ACCOUNT_EMAIL \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "DEBUG=False" \
    --set-env-vars "USE_CLOUD_SQL_AUTH_PROXY=False" \
    --memory 2Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --port 8080

# Get the deployed URL
SERVICE_URL=$(gcloud run services describe speech-memorization --region=us-central1 --format='value(status.url)')

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📝 Next steps:"
echo "1. Configure your ALLOWED_HOSTS environment variable with: ${SERVICE_URL#https://}"
echo "2. Set up your database connection if using Cloud SQL"
echo "3. Configure any additional secrets in Secret Manager"
echo ""
echo "🎤 Google Cloud Speech API is now enabled and configured!"