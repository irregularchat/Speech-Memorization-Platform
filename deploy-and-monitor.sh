#!/bin/bash

# Deploy and Monitor Script for Speech Memorization Platform
# Deploys to Cloud Run and monitors deployment status

set -e

PROJECT_ID="speech-memorization"
SERVICE_NAME="speech-memorization"
REGION="us-central1"
SOURCE_DIR="/Users/admin/Documents/Git/Speech-Memorization-Platform"

echo "🚀 Starting deployment and monitoring for Speech Memorization Platform"
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Source: $SOURCE_DIR"
echo "=========================="

# Function to check service health
check_health() {
    echo "🏥 Checking service health..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")
    
    if [ -z "$SERVICE_URL" ]; then
        echo "❌ Could not get service URL"
        return 1
    fi
    
    echo "📍 Service URL: $SERVICE_URL"
    
    # Test health endpoint with auth
    echo "🔍 Testing health endpoint..."
    ACCESS_TOKEN=$(gcloud auth print-access-token 2>/dev/null || echo "")
    
    if [ -z "$ACCESS_TOKEN" ]; then
        echo "❌ Could not get access token"
        return 1
    fi
    
    # Test health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -m 30 \
        "$SERVICE_URL/health/" 2>/dev/null || echo "000")
    
    echo "📊 Health endpoint returned: HTTP $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Health check passed!"
        return 0
    else
        echo "⚠️ Health check failed with HTTP $HTTP_CODE"
        return 1
    fi
}

# Function to show recent logs
show_logs() {
    echo "📋 Recent logs (last 5 minutes):"
    echo "--------------------------------"
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
        --limit=20 \
        --format="table(timestamp,severity,textPayload)" \
        --freshness=5m || echo "❌ Could not fetch logs"
    echo "--------------------------------"
}

# Function to show deployment status
show_status() {
    echo "📊 Deployment Status:"
    echo "--------------------"
    
    # Service description
    echo "🔍 Service Status:"
    gcloud run services describe $SERVICE_NAME --region=$REGION \
        --format="table(status.conditions[].type,status.conditions[].status,status.conditions[].message)" 2>/dev/null || echo "❌ Could not get service status"
    
    # Traffic allocation
    echo ""
    echo "🚦 Traffic Allocation:"
    gcloud run services describe $SERVICE_NAME --region=$REGION \
        --format="table(status.traffic[].revisionName,status.traffic[].percent)" 2>/dev/null || echo "❌ Could not get traffic info"
    
    # Latest revision
    echo ""
    echo "📦 Latest Revision:"
    LATEST_REVISION=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.latestReadyRevisionName)" 2>/dev/null || echo "unknown")
    echo "Revision: $LATEST_REVISION"
    
    # Revision health
    if [ "$LATEST_REVISION" != "unknown" ] && [ -n "$LATEST_REVISION" ]; then
        echo "🏥 Revision Health:"
        gcloud run revisions describe $LATEST_REVISION --region=$REGION \
            --format="table(status.conditions[].type,status.conditions[].status)" 2>/dev/null || echo "❌ Could not get revision status"
    fi
    
    echo "--------------------"
}

# Start deployment
echo "🔨 Starting deployment..."
echo "Settings: speech_memorization.settings_simple"

# Deploy with timeout and progress monitoring
echo "⏳ Deploying (this may take 5-10 minutes)..."

# Start deployment in background and capture output
DEPLOY_LOG="/tmp/deploy-$$.log"
gcloud run deploy $SERVICE_NAME \
    --source "$SOURCE_DIR" \
    --set-env-vars "DJANGO_SETTINGS_MODULE=speech_memorization.settings_simple" \
    --region $REGION \
    --timeout 600 > "$DEPLOY_LOG" 2>&1 &

DEPLOY_PID=$!

# Monitor deployment progress
echo "📈 Monitoring deployment progress..."
COUNTER=0
while kill -0 $DEPLOY_PID 2>/dev/null; do
    COUNTER=$((COUNTER + 1))
    
    # Show progress every 30 seconds
    if [ $((COUNTER % 6)) -eq 0 ]; then
        MINUTES=$((COUNTER / 12))
        echo "⏱️  Deployment running for ${MINUTES} minutes..."
        
        # Show any new logs
        if [ -f "$DEPLOY_LOG" ]; then
            echo "📝 Latest deployment output:"
            tail -5 "$DEPLOY_LOG" | grep -v "^$" || echo "   (building...)"
        fi
    fi
    
    sleep 5
done

# Check deployment result
wait $DEPLOY_PID
DEPLOY_EXIT_CODE=$?

echo ""
echo "📋 Final deployment output:"
echo "=========================="
cat "$DEPLOY_LOG"
echo "=========================="

# Clean up log file
rm -f "$DEPLOY_LOG"

if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
    echo "✅ Deployment completed successfully!"
else
    echo "❌ Deployment failed with exit code $DEPLOY_EXIT_CODE"
    echo ""
    echo "🔍 Checking current service status..."
    show_status
    echo ""
    show_logs
    exit 1
fi

# Post-deployment monitoring
echo ""
echo "🔍 Post-deployment verification..."
echo "================================="

# Wait a moment for service to be ready
echo "⏳ Waiting 10 seconds for service to be ready..."
sleep 10

# Show deployment status
show_status

echo ""

# Health check
echo "🏥 Performing health checks..."
if check_health; then
    echo "✅ Deployment verification successful!"
else
    echo "⚠️ Deployment completed but health checks failed"
    echo ""
    echo "🔍 Investigating issues..."
    show_logs
fi

echo ""
echo "🎯 Deployment Summary:"
echo "====================="
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null || echo "unknown")
echo "Service URL: $SERVICE_URL"
echo "Region: $REGION"
echo "Settings: speech_memorization.settings_simple"
echo "Auth required: Yes (use gcloud auth)"

echo ""
echo "🔧 Quick testing commands:"
echo "------------------------"
echo "Health check:"
echo "curl -H \"Authorization: Bearer \$(gcloud auth print-access-token)\" $SERVICE_URL/health/"
echo ""
echo "Home page:"
echo "curl -H \"Authorization: Bearer \$(gcloud auth print-access-token)\" $SERVICE_URL/"
echo ""
echo "View logs:"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit=10"

echo ""
echo "🏁 Monitoring complete!"