# 🛠️ Deployment Scripts

This directory contains scripts to help with setup, deployment, and management of the Speech Memorization Platform.

## Scripts Overview

### 🔐 `setup-secrets.sh`
**Purpose**: Initialize Google Cloud Secret Manager secrets for production deployment

**Usage**:
```bash
./scripts/setup-secrets.sh
```

**What it does**:
- Creates all required secrets in Google Cloud Secret Manager
- Generates secure Django SECRET_KEY
- Sets up IAM permissions for Cloud Run service account
- Provides next steps for updating API keys

**Prerequisites**:
- `gcloud` CLI installed and authenticated
- Project permissions to create secrets and manage IAM

---

### 🏠 `setup-local-dev.sh`
**Purpose**: Set up local development environment

**Usage**:
```bash
./scripts/setup-local-dev.sh
```

**What it does**:
- Creates `.env` file from `.env.example`
- Generates secure local Django SECRET_KEY
- Installs Python dependencies
- Runs database migrations
- Collects static files
- Optional: Creates Django superuser

**Prerequisites**:
- Python 3.11+ installed
- Run from project root directory (where `manage.py` is located)

---

### 🚀 `deploy-to-cloud-run.sh`
**Purpose**: Deploy application to Google Cloud Run with proper secret management

**Usage**:
```bash
./scripts/deploy-to-cloud-run.sh
```

**What it does**:
- Validates all required secrets exist in Secret Manager
- Builds and deploys Docker container to Cloud Run
- Configures service with appropriate resources and environment
- Tests deployment health
- Provides monitoring and management URLs

**Prerequisites**:
- `gcloud` CLI installed and authenticated
- Secrets already created (run `setup-secrets.sh` first)
- Docker installed (for building container)

## Typical Workflow

### First Time Setup (Production)

1. **Initialize secrets**:
   ```bash
   ./scripts/setup-secrets.sh
   ```

2. **Update API keys** (after setup-secrets.sh):
   ```bash
   # Update OpenAI API key
   echo 'sk-your-actual-openai-key' | gcloud secrets versions add openai-api-key --data-file=-
   
   # Update database URL for production
   echo 'postgresql://user:pass@host/db' | gcloud secrets versions add database-url --data-file=-
   ```

3. **Deploy to Cloud Run**:
   ```bash
   ./scripts/deploy-to-cloud-run.sh
   ```

### Local Development Setup

1. **Set up local environment**:
   ```bash
   ./scripts/setup-local-dev.sh
   ```

2. **Edit `.env` file** with your local configuration:
   ```bash
   nano .env  # Update OPENAI_API_KEY, DATABASE_URL, etc.
   ```

3. **Start development server**:
   ```bash
   python manage.py runserver
   ```

### Subsequent Deployments

After the initial setup, you can deploy updates with just:
```bash
./scripts/deploy-to-cloud-run.sh
```

## Environment Variables

### Required for Production
- `SECRET_KEY` - Django secret key (auto-generated)
- `DATABASE_URL` - Database connection string
- `OPENAI_API_KEY` - OpenAI API key
- `GOOGLE_CLOUD_PROJECT_ID` - Google Cloud project ID

### Optional Configuration
- `DEBUG` - Enable Django debug mode (default: False in production)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS` - Comma-separated list of trusted origins

## Secret Management Strategy

### Local Development
- Uses `.env` file (git-ignored)
- Read by `python-decouple`
- No Google Cloud Secret Manager required

### Production (Cloud Run)
- Secrets stored in Google Cloud Secret Manager
- Populated into environment variables at startup
- Same `config()` calls work transparently

### Security Benefits
- ✅ No secrets in source code
- ✅ Different secrets for different environments
- ✅ Easy secret rotation without redeployment
- ✅ Audit trail of secret access
- ✅ Fine-grained IAM permissions

## Troubleshooting

### Common Issues

**"Permission denied" when creating secrets**:
```bash
# Ensure you have the right permissions
gcloud auth list
gcloud config set project your-project-id
```

**"Secrets not found" during deployment**:
```bash
# Check if secrets exist
gcloud secrets list
# If missing, run setup-secrets.sh
./scripts/setup-secrets.sh
```

**Local development can't find .env**:
```bash
# Make sure you're in the project root
ls -la .env  # Should exist
# If not, run setup-local-dev.sh
./scripts/setup-local-dev.sh
```

**Cloud Run deployment fails**:
```bash
# Check logs
gcloud run logs tail speech-memorization --region=us-central1
# Verify secrets permissions
gcloud secrets get-iam-policy secret-key
```

## Security Notes

- 🔒 **Never commit secrets** to version control
- 🔒 **Use different secrets** for different environments
- 🔒 **Rotate secrets regularly** using Secret Manager versioning
- 🔒 **Monitor secret access** using Cloud Logging
- 🔒 **Grant minimal permissions** (secretAccessor role only)

---

For more detailed information, see `docs/security/secrets-management.md`