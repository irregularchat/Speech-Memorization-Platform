/**
 * API Configuration
 * Manages API keys and service configurations
 */

// Google Cloud Speech-to-Text API configuration
export const GOOGLE_CLOUD_CONFIG = {
    // Replace with your actual Google Cloud API key
    // You can get this from Google Cloud Console -> APIs & Services -> Credentials
    API_KEY: import.meta.env.VITE_GOOGLE_CLOUD_API_KEY || 'YOUR_GOOGLE_CLOUD_API_KEY_HERE',
    
    // Speech recognition settings
    SPEECH_CONFIG: {
        encoding: 'WEBM_OPUS',
        sampleRateHertz: 48000,
        languageCode: 'en-US',
        enableAutomaticPunctuation: true,
        enableWordTimeOffsets: true,
        model: 'latest_long',
        useEnhanced: true,
        maxAlternatives: 1,
        profanityFilter: false,
        enableWordConfidence: true
    },
    
    // Audio recording settings
    AUDIO_CONFIG: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 48000,
        channelCount: 1
    }
};

// Fallback configuration for when Google Cloud API is not available
export const FALLBACK_CONFIG = {
    useWebKitSpeechRecognition: true,
    continuous: true,
    interimResults: true,
    lang: 'en-US',
    maxAlternatives: 1
};

// API endpoints
export const API_ENDPOINTS = {
    GOOGLE_SPEECH: 'https://speech.googleapis.com/v1/speech',
    GOOGLE_SPEECH_STREAMING: 'wss://speech.googleapis.com/v1/speech:streamingRecognize'
};

// Check if API key is configured
export function isGoogleCloudConfigured() {
    const apiKey = GOOGLE_CLOUD_CONFIG.API_KEY;
    return apiKey && apiKey !== 'YOUR_GOOGLE_CLOUD_API_KEY_HERE' && apiKey.length > 10;
}

// Get the appropriate speech service based on configuration
export function getSpeechServiceType() {
    if (isGoogleCloudConfigured()) {
        return 'google-cloud';
    } else if ('webkitSpeechRecognition' in window) {
        return 'webkit';
    } else {
        return 'none';
    }
}