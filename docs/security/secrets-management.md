# 🔐 Secrets Management with Google Cloud Secret Manager

This document describes how the Speech Memorization Platform securely manages sensitive configuration using Google Cloud Secret Manager.

## Overview

Instead of hardcoding sensitive values like passwords, API keys, and database credentials in configuration files, we use Google Cloud Secret Manager to store and retrieve secrets securely.

### Benefits
- ✅ **Security**: Secrets are encrypted at rest and in transit
- ✅ **Rotation**: Easy to update secrets without redeploying
- ✅ **Audit**: Full audit trail of secret access
- ✅ **Versioning**: Keep multiple versions of secrets
- ✅ **Access Control**: Fine-grained IAM permissions

## Architecture

```mermaid
graph TD
    A[Cloud Run Application] --> B[Secret Manager Client]
    B --> C[Google Cloud Secret Manager]
    C --> D[Encrypted Secrets Storage]
    
    E[settings_cloud.py] --> F[Secret Paths Only]
    G[utils/secrets.py] --> B
```

## Current Implementation

### Secrets Stored
- `secret-key` - Django application secret key (auto-generated)
- `database-url` - Database connection string
- `openai-api-key` - OpenAI API key for AI features
- `google-cloud-project-id` - Google Cloud project identifier

### Configuration Strategy

**Local Development** - Uses .env file with python-decouple:
```python
# settings_cloud.py works for both local and production
from decouple import config
SECRET_KEY = config('SECRET_KEY')
DATABASE_URL = config('DATABASE_URL', default='sqlite:///db.sqlite3')
```

**Cloud Run Production** - Populates environment variables from Secret Manager:
```python
# settings_cloud.py (runs on app startup)
from utils.secrets import populate_env_from_secrets
populate_env_from_secrets()  # Populates os.environ from Secret Manager

# Then continues with same config() calls as local
SECRET_KEY = config('SECRET_KEY')  # Now reads from populated env vars
```

**utils/secrets.py** - Populates environment variables on Cloud Run:
```python
def populate_env_from_secrets():
    # Only sets env vars that aren't already set
    # Maps env var names to Secret Manager secret names
    # LOCAL: .env file → environment variables → config()
    # CLOUD: Secret Manager → environment variables → config()
```

## Setup Commands

### 1. Create Secrets (One-time setup)

```bash
# Create a secure random Django SECRET_KEY
gcloud secrets create SECRET_KEY --data-file=- <<< "$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"

# Create database URL
gcloud secrets create DATABASE_URL --data-file=- <<< "postgresql://user:pass@localhost/speech_memorization"

# Create OpenAI API key
gcloud secrets create OPENAI_API_KEY --data-file=- <<< "your-openai-api-key"

# Create Google Cloud Project ID
gcloud secrets create GOOGLE_CLOUD_PROJECT_ID --data-file=- <<< "serverless-test-12345"
```

### 2. View Existing Secrets

```bash
# List all secrets
gcloud secrets list

# View secret metadata (not the value)
gcloud secrets describe SECRET_KEY

# View secret versions
gcloud secrets versions list SECRET_KEY
```

### 3. Update Secrets

```bash
# Add new version of a secret
gcloud secrets versions add SECRET_KEY --data-file=- <<< "new-secret-value"

# Rotate Django secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' | gcloud secrets versions add SECRET_KEY --data-file=-
```

### 4. Access Secrets (for debugging)

```bash
# View current secret value (be careful - this exposes the secret!)
gcloud secrets versions access latest --secret="SECRET_KEY"

# View specific version
gcloud secrets versions access 1 --secret="DATABASE_URL"
```

## Local Development Setup

### 1. Create .env file

```bash
# Create .env file in project root (DO NOT COMMIT)
cat > .env << EOF
SECRET_KEY=django-insecure-local-development-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
OPENAI_API_KEY=your-local-openai-key
GOOGLE_CLOUD_PROJECT_ID=your-project-id
EOF
```

### 2. Add .env to .gitignore

```bash
echo ".env" >> .gitignore
echo "*.env" >> .gitignore
echo ".env.*" >> .gitignore
```

### 3. Install python-decouple

```bash
pip install python-decouple
```

## Use Cases

### 1. Rotating Database Password

```bash
# Generate new connection string and update secret
NEW_DB_URL="postgresql://user:newpass@host/database"
echo "$NEW_DB_URL" | gcloud secrets versions add DATABASE_URL --data-file=-

# The application will use the new URL on next restart
# No redeployment needed!
```

### 2. Adding New Secrets

```bash
# Create new secret for external API
gcloud secrets create EXTERNAL_API_KEY --data-file=- <<< "your-api-key"

# Update utils/secrets.py to retrieve it
# Update settings to use it
# Redeploy application
```

### 3. Environment-Specific Secrets

```bash
# Create production secrets
gcloud secrets create PROD_SECRET_KEY --data-file=- <<< "$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"

# Create staging secrets  
gcloud secrets create STAGING_SECRET_KEY --data-file=- <<< "$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"

# Use different secret names in different environments
```

## Security Best Practices

### 1. Principle of Least Privilege
```bash
# Grant minimal permissions - only secret accessor, not admin
gcloud secrets add-iam-policy-binding SECRET_KEY \
    --member="serviceAccount:speech-memorization@serverless-test-12345.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2. Never Commit Secrets
```bash
# Always use .env for local development
# Always use Secret Manager for production
# Never hardcode secrets in source code
```

### 3. Audit Access
```bash
# View who accessed secrets
gcloud logging read "resource.type=gce_instance AND protoPayload.serviceName=secretmanager.googleapis.com" --project=serverless-test-12345
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Check IAM permissions
   gcloud secrets get-iam-policy SECRET_KEY
   
   # Add missing permissions
   gcloud secrets add-iam-policy-binding SECRET_KEY \
       --member="serviceAccount:your-service@project.iam.gserviceaccount.com" \
       --role="roles/secretmanager.secretAccessor"
   ```

2. **Secret Not Found**
   ```bash
   # Verify secret exists
   gcloud secrets describe SECRET_KEY
   
   # Check secret name matches code
   ```

3. **Fallback Values Used**
   ```bash
   # Check application logs
   gcloud run logs read speech-memorization --region=us-central1 | grep -i secret
   
   # Verify Secret Manager client initialization
   ```

### Debug Commands

```bash
# Test secret access from Cloud Shell
gcloud secrets versions access latest --secret="SECRET_KEY"

# Verify service account has access
gcloud secrets get-iam-policy SECRET_KEY

# Check application logs for secret-related errors
gcloud run logs read speech-memorization --region=us-central1 --limit=100 | grep -E "(secret|Secret|SECRET)"
```

## Migration Plan

### Phase 1: Create Secret Manager Infrastructure
1. ✅ Create `utils/secrets.py` module
2. ✅ Update `requirements.txt` with `google-cloud-secret-manager`
3. Create secrets in Secret Manager
4. Update IAM permissions

### Phase 2: Update Settings Files
1. ✅ Update `settings_cloud.py` to use Secret Manager
2. Keep `settings_minimal.py` for local development with .env
3. Remove hardcoded secret defaults

### Phase 3: Test and Deploy
1. Test locally with .env files
2. Test on Cloud Run with Secret Manager
3. Verify all secrets are retrieved correctly
4. Remove any remaining hardcoded values

### Phase 4: Documentation and Training
1. ✅ Document secret management strategy
2. Create deployment runbooks
3. Set up secret rotation procedures

## Current Status

- ✅ Secret management architecture designed
- ✅ `utils/secrets.py` module created
- ⏳ Secrets need to be created in Secret Manager
- ⏳ Settings files need to be updated
- ⏳ Cloud Run deployment needs testing
- ⏳ Local .env setup needs documentation

---

**Security Note**: Never commit actual secret values to version control. Always use .env files for local development and Secret Manager for production.