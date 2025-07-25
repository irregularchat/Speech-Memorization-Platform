"""
Health check utilities for Google Cloud Speech API
"""

import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

def check_speech_api_health() -> Dict[str, Any]:
    """
    Comprehensive health check for Google Cloud Speech API
    
    Returns:
        Dict containing health status and details
    """
    health_status = {
        'service': 'Google Cloud Speech API',
        'status': 'unknown',
        'details': {},
        'recommendations': []
    }
    
    try:
        # Check if google-cloud-speech is installed
        try:
            import google.cloud.speech as speech
            health_status['details']['library_installed'] = True
        except ImportError as e:
            health_status['status'] = 'error'
            health_status['details']['library_installed'] = False
            health_status['details']['error'] = str(e)
            health_status['recommendations'].append('Install google-cloud-speech: pip install google-cloud-speech')
            return health_status
        
        # Check authentication
        auth_status = check_authentication()
        health_status['details']['authentication'] = auth_status
        
        if not auth_status['valid']:
            health_status['status'] = 'error'
            health_status['recommendations'].extend(auth_status['recommendations'])
            return health_status
        
        # Try to initialize client
        try:
            client = speech.SpeechClient()
            health_status['details']['client_initialization'] = True
            
            # Test basic functionality (without audio)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
            )
            
            # This validates configuration but doesn't make an API call
            health_status['details']['config_valid'] = True
            health_status['status'] = 'healthy'
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['details']['client_initialization'] = False
            health_status['details']['client_error'] = str(e)
            health_status['recommendations'].append('Check Google Cloud project and Speech API permissions')
            
    except Exception as e:
        health_status['status'] = 'error'
        health_status['details']['unexpected_error'] = str(e)
        health_status['recommendations'].append('Check system configuration and dependencies')
    
    return health_status


def check_authentication() -> Dict[str, Any]:
    """
    Check Google Cloud authentication status
    
    Returns:
        Dict containing authentication details
    """
    auth_status = {
        'valid': False,
        'method': None,
        'project_id': None,
        'recommendations': []
    }
    
    try:
        # Check environment variables
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
        
        if credentials_path:
            auth_status['method'] = 'service_account_file'
            auth_status['credentials_path'] = credentials_path
            
            # Check if file exists
            if os.path.exists(credentials_path):
                auth_status['credentials_file_exists'] = True
            else:
                auth_status['credentials_file_exists'] = False
                auth_status['recommendations'].append(f'Credentials file not found: {credentials_path}')
                return auth_status
        
        # Try default credentials (works in Cloud Run)
        try:
            import google.auth
            credentials, detected_project = google.auth.default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            auth_status['valid'] = True
            auth_status['method'] = auth_status.get('method', 'default_credentials')
            auth_status['project_id'] = project_id or detected_project
            
            if not auth_status['project_id']:
                auth_status['recommendations'].append('Set GOOGLE_CLOUD_PROJECT_ID environment variable')
            
        except Exception as e:
            auth_status['auth_error'] = str(e)
            auth_status['recommendations'].extend([
                'Set GOOGLE_APPLICATION_CREDENTIALS environment variable',
                'Or run in Google Cloud environment with default service account',
                'Or use gcloud auth application-default login for local development'
            ])
    
    except Exception as e:
        auth_status['unexpected_error'] = str(e)
        auth_status['recommendations'].append('Check system configuration')
    
    return auth_status


def check_audio_dependencies() -> Dict[str, Any]:
    """
    Check audio processing dependencies
    
    Returns:
        Dict containing audio dependency status
    """
    audio_status = {
        'pyaudio_available': False,
        'audio_devices': [],
        'recommendations': []
    }
    
    try:
        import pyaudio
        audio_status['pyaudio_available'] = True
        
        # Check for audio input devices
        try:
            pa = pyaudio.PyAudio()
            device_count = pa.get_device_count()
            
            for i in range(device_count):
                device_info = pa.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    audio_status['audio_devices'].append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
            
            pa.terminate()
            
            if not audio_status['audio_devices']:
                audio_status['recommendations'].append('No audio input devices found')
            
        except Exception as e:
            audio_status['device_check_error'] = str(e)
            audio_status['recommendations'].append('Audio device detection failed')
    
    except ImportError:
        audio_status['recommendations'].extend([
            'Install PyAudio: pip install pyaudio',
            'On Ubuntu/Debian: sudo apt-get install portaudio19-dev python3-pyaudio',
            'On macOS: brew install portaudio, then pip install pyaudio',
            'On Windows: pip install pyaudio (may require Visual C++ Build Tools)'
        ])
    
    return audio_status


def get_speech_api_diagnostics() -> Dict[str, Any]:
    """
    Get comprehensive diagnostics for Speech API setup
    
    Returns:
        Complete diagnostic report
    """
    return {
        'speech_api': check_speech_api_health(),
        'authentication': check_authentication(),
        'audio_dependencies': check_audio_dependencies(),
        'environment': {
            'google_application_credentials': os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
            'google_cloud_project_id': os.environ.get('GOOGLE_CLOUD_PROJECT_ID'),
            'python_version': __import__('sys').version
        }
    }


# Django view for health check endpoint
def speech_health_view(request):
    """Django view for Speech API health check"""
    from django.http import JsonResponse
    
    diagnostics = get_speech_api_diagnostics()
    
    # Determine overall status
    speech_healthy = diagnostics['speech_api']['status'] == 'healthy'
    auth_valid = diagnostics['authentication']['valid']
    audio_available = diagnostics['audio_dependencies']['pyaudio_available']
    
    overall_status = 'healthy' if (speech_healthy and auth_valid) else 'degraded'
    if not auth_valid:
        overall_status = 'error'
    
    return JsonResponse({
        'overall_status': overall_status,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'diagnostics': diagnostics
    })