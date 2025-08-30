#!/bin/bash
set -e

echo "=== FIXING STATIC FILE SERVING ===" 

PROJECT_ID="serverless-test-12345"
SERVICE_NAME="speech-memorization-app"
REGION="us-central1"

# Set project
gcloud config set project $PROJECT_ID

echo "Collecting static files locally to verify..."
python3 manage.py collectstatic --noinput

echo "Deploying with explicit static file handling..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --timeout 300 \
    --max-instances 3 \
    --set-env-vars "DEBUG=True,DJANGO_SETTINGS_MODULE=speech_memorization.settings_minimal" \
    --quiet

echo "=== DEPLOYMENT COMPLETE ===" 
URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.address.url)")
echo "Service URL: $URL"
echo "Test static file: $URL/static/js/ai_speech_recorder.js"

echo "Testing static file availability..."
sleep 10
curl -I "$URL/static/js/ai_speech_recorder.js"