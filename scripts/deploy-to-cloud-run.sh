#!/bin/bash
# Deploy Speech Memorization Platform to Google Cloud Run
# This script handles deployment with proper secret management

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"serverless-test-12345"}
SERVICE_NAME="speech-memorization"
REGION="us-central1"
MIN_INSTANCES=0
MAX_INSTANCES=3
MEMORY="1Gi"
CPU=1
TIMEOUT=300

echo "🚀 Deploying Speech Memorization Platform to Cloud Run"
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Check if required secrets exist
echo "🔍 Checking if secrets exist in Secret Manager..."
REQUIRED_SECRETS=("secret-key" "database-url" "openai-api-key" "google-cloud-project-id")
MISSING_SECRETS=()

for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! gcloud secrets describe $secret >/dev/null 2>&1; then
        MISSING_SECRETS+=($secret)
    fi
done

if [ ${#MISSING_SECRETS[@]} -ne 0 ]; then
    echo "❌ Missing required secrets: ${MISSING_SECRETS[*]}"
    echo "   Run ./scripts/setup-secrets.sh to create them"
    exit 1
fi

echo "✅ All required secrets found"

# Deploy to Cloud Run
echo "🏗️  Building and deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory $MEMORY \
    --cpu $CPU \
    --timeout $TIMEOUT \
    --min-instances $MIN_INSTANCES \
    --max-instances $MAX_INSTANCES \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,DJANGO_SETTINGS_MODULE=speech_memorization.settings_cloud" \
    --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo "🔗 Login URL: $SERVICE_URL/login/"
echo "🩺 Health Check: $SERVICE_URL/health/"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: gcloud run logs tail $SERVICE_NAME --region=$REGION"
echo "   View service: gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "   Update service: gcloud run services update $SERVICE_NAME --region=$REGION"
echo ""
echo "🔐 Secret management:"
echo "   List secrets: gcloud secrets list"
echo "   Update secret: echo 'new-value' | gcloud secrets versions add SECRET_NAME --data-file=-"
echo "   View secret: gcloud secrets versions access latest --secret=SECRET_NAME"
echo ""
echo "📊 Monitor your deployment:"
echo "   Metrics: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
echo "   Logs: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/logs?project=$PROJECT_ID"

# Test the deployment
echo ""
echo "🧪 Testing deployment..."
if curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health/" | grep -q "200"; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed - check logs for issues"
    echo "   gcloud run logs tail $SERVICE_NAME --region=$REGION"
fi