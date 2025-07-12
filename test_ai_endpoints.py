#!/usr/bin/env python3
"""
Test script for AI Speech endpoints
This will generate test data and make requests to test the AI functionality
"""

import requests
import json
import base64
import os
from django.contrib.auth import authenticate
from django.test import Client

# Test configuration
BASE_URL = "http://localhost:8880"
TEST_AUDIO_DATA = b"fake_audio_data_for_testing"  # In real app, this would be actual audio

def test_microphone_endpoint():
    """Test the microphone quality endpoint"""
    print("🎤 Testing microphone quality endpoint...")
    
    # Encode test audio data
    audio_b64 = base64.b64encode(TEST_AUDIO_DATA).decode('utf-8')
    
    # Prepare test data
    test_data = {
        "audio_data": audio_b64,
        "audio_format": "webm"
    }
    
    try:
        # Test without authentication (should fail)
        response = requests.post(
            f"{BASE_URL}/api/practice/test-microphone/",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data),
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Microphone test endpoint responding")
            print(f"Response: {json.dumps(result, indent=2)}")
        elif response.status_code == 302:
            print("🔄 Redirected to login (authentication required)")
        elif response.status_code == 403:
            print("🔒 Authentication required")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_static_files():
    """Test if static files are loading"""
    print("\n📁 Testing static files...")
    
    static_files = [
        "/static/js/ai_speech_recorder.js",
    ]
    
    for file_path in static_files:
        try:
            response = requests.get(f"{BASE_URL}{file_path}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {file_path} - OK")
            else:
                print(f"❌ {file_path} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {file_path} - Error: {e}")

def test_main_pages():
    """Test main application pages"""
    print("\n🌐 Testing main pages...")
    
    pages = [
        "/",
        "/texts/",
        "/about/",
        "/login/",
    ]
    
    for page in pages:
        try:
            response = requests.get(f"{BASE_URL}{page}", timeout=5, allow_redirects=True)
            print(f"✅ {page} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {page} - Error: {e}")

def check_openai_config():
    """Check OpenAI configuration"""
    print("\n🤖 Checking OpenAI configuration...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OpenAI API Key configured (length: {len(openai_key)})")
        print(f"🔑 Key starts with: {openai_key[:10]}...")
    else:
        print("❌ OpenAI API Key not found in environment")

def main():
    print("🧪 Speech Memorization Platform - AI Endpoint Tests")
    print("=" * 55)
    print()
    
    # Check configuration first
    check_openai_config()
    
    # Test basic connectivity
    test_main_pages()
    
    # Test static files
    test_static_files()
    
    # Test AI endpoints
    test_microphone_endpoint()
    
    print("\n" + "=" * 55)
    print("✅ Test suite completed!")
    print("Check logs/speech_memorization.log for AI processing details")

if __name__ == "__main__":
    main()