#!/usr/bin/env python3
"""
Test Google Cloud Speech API integration
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'speech_memorization.settings_cloud')
django.setup()

from memorization.speech_health_check import get_speech_api_diagnostics
from memorization.google_speech_service import GoogleSpeechStreamingService, GoogleSpeechBatchService

def test_speech_api():
    """Test the Speech API integration"""
    print("🧪 Testing Google Cloud Speech API Integration")
    print("=" * 50)
    
    # Run diagnostics
    print("📋 Running diagnostics...")
    diagnostics = get_speech_api_diagnostics()
    
    # Display results
    print("\n🔍 Speech API Status:")
    speech_status = diagnostics['speech_api']
    print(f"  Status: {speech_status['status']}")
    print(f"  Library Installed: {speech_status['details'].get('library_installed', False)}")
    print(f"  Client Initialized: {speech_status['details'].get('client_initialization', False)}")
    
    if speech_status['recommendations']:
        print("  Recommendations:")
        for rec in speech_status['recommendations']:
            print(f"    - {rec}")
    
    print("\n🔐 Authentication Status:")
    auth_status = diagnostics['authentication']
    print(f"  Valid: {auth_status['valid']}")
    print(f"  Method: {auth_status.get('method', 'none')}")
    print(f"  Project ID: {auth_status.get('project_id', 'not set')}")
    
    if auth_status['recommendations']:
        print("  Recommendations:")
        for rec in auth_status['recommendations']:
            print(f"    - {rec}")
    
    print("\n🎤 Audio Dependencies:")
    audio_status = diagnostics['audio_dependencies']
    print(f"  PyAudio Available: {audio_status['pyaudio_available']}")
    print(f"  Audio Devices: {len(audio_status['audio_devices'])}")
    
    if audio_status['audio_devices']:
        print("  Available devices:")
        for device in audio_status['audio_devices'][:3]:  # Show first 3
            print(f"    - {device['name']} ({device['channels']} channels)")
    
    if audio_status['recommendations']:
        print("  Recommendations:")
        for rec in audio_status['recommendations']:
            print(f"    - {rec}")
    
    # Test service initialization
    print("\n🔧 Testing Service Initialization:")
    
    try:
        streaming_service = GoogleSpeechStreamingService()
        print(f"  Streaming Service Available: {streaming_service.is_available()}")
    except Exception as e:
        print(f"  Streaming Service Error: {e}")
    
    try:
        batch_service = GoogleSpeechBatchService()
        print(f"  Batch Service Available: {batch_service.is_available()}")
    except Exception as e:
        print(f"  Batch Service Error: {e}")
    
    # Overall assessment
    print("\n📊 Overall Assessment:")
    speech_healthy = speech_status['status'] == 'healthy'
    auth_valid = auth_status['valid']
    audio_available = audio_status['pyaudio_available']
    
    if speech_healthy and auth_valid:
        print("  ✅ Google Cloud Speech API is ready for deployment!")
        if not audio_available:
            print("  ⚠️  Audio recording not available (PyAudio missing)")
            print("      This will affect live microphone features")
    elif auth_valid:
        print("  ⚠️  Speech API partially configured")
        print("      Check Speech API permissions and quotas")
    else:
        print("  ❌ Speech API not properly configured")
        print("      Authentication needs to be set up")
    
    print("\n💡 Next Steps:")
    if not auth_valid:
        print("  1. Set up Google Cloud authentication")
        print("  2. Enable Speech API in your project")
        print("  3. Create and configure a service account")
    elif not speech_healthy:
        print("  1. Check Speech API quotas and billing")
        print("  2. Verify project permissions")
    elif not audio_available:
        print("  1. Install PyAudio for microphone support")
        print("  2. Test audio device permissions")
    else:
        print("  1. Deploy and test in Cloud Run")
        print("  2. Monitor API usage and costs")

if __name__ == "__main__":
    test_speech_api()