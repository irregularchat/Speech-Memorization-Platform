#!/bin/bash
# Setup Google Cloud Secret Manager secrets for Speech Memorization Platform
# Run this once to initialize secrets in your Google Cloud project

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"serverless-test-12345"}
echo "Setting up secrets for project: $PROJECT_ID"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

echo "🔐 Creating secrets in Google Cloud Secret Manager..."

# 1. Django SECRET_KEY - Generate a secure random key
echo "Creating Django SECRET_KEY..."
python3 -c "
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
" | gcloud secrets create secret-key --data-file=- || echo "Secret 'secret-key' already exists"

# 2. Database URL - You'll need to update this with your actual database
echo "Creating DATABASE_URL..."
echo "sqlite:///db.sqlite3" | gcloud secrets create database-url --data-file=- || echo "Secret 'database-url' already exists"

# 3. OpenAI API Key - You'll need to set this manually
echo "Creating OPENAI_API_KEY placeholder..."
echo "your-openai-api-key-replace-this" | gcloud secrets create openai-api-key --data-file=- || echo "Secret 'openai-api-key' already exists"

# 4. Google Cloud Project ID
echo "Creating GOOGLE_CLOUD_PROJECT_ID..."
echo "$PROJECT_ID" | gcloud secrets create google-cloud-project-id --data-file=- || echo "Secret 'google-cloud-project-id' already exists"

echo "✅ Secrets created successfully!"

# Get the default Cloud Run service account
SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="displayName:Compute Engine default service account" --format="value(email)")

if [ -z "$SERVICE_ACCOUNT" ]; then
    echo "⚠️  Could not find default service account. You may need to grant permissions manually."
    echo "   Run this command with your actual service account:"
    echo "   gcloud secrets add-iam-policy-binding SECRET_NAME --member='serviceAccount:YOUR_SERVICE_ACCOUNT' --role='roles/secretmanager.secretAccessor'"
else
    echo "🔑 Granting Secret Manager access to service account: $SERVICE_ACCOUNT"
    
    # Grant access to all secrets
    for secret in secret-key database-url openai-api-key google-cloud-project-id; do
        gcloud secrets add-iam-policy-binding $secret \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/secretmanager.secretAccessor" \
            --quiet || echo "Failed to grant access to $secret"
    done
fi

echo ""
echo "🎯 Next steps:"
echo "1. Update the OpenAI API key:"
echo "   echo 'your-actual-openai-key' | gcloud secrets versions add openai-api-key --data-file=-"
echo ""
echo "2. Update the database URL for production:"
echo "   echo 'postgresql://user:pass@host/db' | gcloud secrets versions add database-url --data-file=-"
echo ""
echo "3. Deploy your application:"
echo "   gcloud run deploy speech-memorization --source . --region us-central1"
echo ""
echo "4. View secrets (metadata only):"
echo "   gcloud secrets list"
echo ""
echo "5. Test secret access:"
echo "   gcloud secrets versions access latest --secret=secret-key"