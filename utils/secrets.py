"""
Secret management utilities for Django app
Populates environment variables from Google Secret Manager for Cloud Run
"""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def get_secret_from_manager(secret_id: str, project_id: str) -> Optional[str]:
    """
    Get secret from Google Secret Manager
    """
    try:
        from google.cloud import secretmanager
        
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
        
    except Exception as e:
        logger.warning(f"Failed to get secret {secret_id} from Secret Manager: {e}")
        return None

def populate_env_from_secrets(project_id: str = None) -> Dict[str, str]:
    """
    Populate environment variables from Secret Manager for Cloud Run deployment
    Only sets env vars that are not already set (allows local .env to override)
    
    Returns dict of secrets that were populated
    """
    if project_id is None:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'serverless-test-12345')
    
    # Define mapping of environment variable names to Secret Manager secret names
    secret_mappings = {
        'SECRET_KEY': 'SECRET_KEY',  # Use existing secret name
        'DATABASE_URL': 'database-url', 
        'OPENAI_API_KEY': 'openai-config',  # Use existing secret name
        'GOOGLE_CLOUD_PROJECT_ID': 'GOOGLE_CLOUD_PROJECT_ID',  # We'll create this
    }
    
    populated_secrets = {}
    
    for env_var, secret_name in secret_mappings.items():
        # Only populate if environment variable is not already set
        if not os.environ.get(env_var):
            secret_value = get_secret_from_manager(secret_name, project_id)
            if secret_value:
                os.environ[env_var] = secret_value
                populated_secrets[env_var] = '***'  # Don't log actual values
                logger.info(f"Populated {env_var} from Secret Manager")
            else:
                logger.warning(f"Could not retrieve {env_var} from Secret Manager")
        else:
            logger.info(f"{env_var} already set in environment, skipping Secret Manager")
    
    return populated_secrets

def is_cloud_run() -> bool:
    """
    Detect if we're running on Cloud Run
    """
    return (
        os.environ.get('K_SERVICE') is not None or  # Cloud Run
        os.environ.get('GAE_ENV') is not None or    # App Engine
        os.environ.get('GOOGLE_CLOUD_PROJECT') is not None  # Any Google Cloud
    )

def setup_secrets_for_environment():
    """
    Setup secrets based on the current environment
    - Cloud Run: Populate from Secret Manager
    - Local: Use .env file (via python-decouple)
    """
    if is_cloud_run():
        logger.info("Detected Cloud Run environment, loading secrets from Secret Manager")
        populate_env_from_secrets()
    else:
        logger.info("Local development detected, using .env file")