/**
 * Unified Speech Service
 * Uses Google Cloud Speech-to-Text API with fallback to WebKit
 */

import GoogleSpeechService from './googleSpeechService.js';
import { GOOGLE_CLOUD_CONFIG, isGoogleCloudConfigured, getSpeechServiceType } from '../config/apiConfig.js';

class UnifiedSpeechService {
    constructor() {
        this.serviceType = getSpeechServiceType();
        this.currentService = null;
        this.isInitialized = false;
        
        // Event callbacks
        this.onResult = null;
        this.onError = null;
        this.onStart = null;
        this.onEnd = null;
        
        console.log(`🎤 Speech service type: ${this.serviceType}`);
    }
    
    async initialize() {
        try {
            // Always try WebKit first since Google Cloud has CORS issues in browsers
            if ('webkitSpeechRecognition' in window) {
                console.log('🎤 Using WebKit Speech Recognition (browser native)');
                this.serviceType = 'webkit';
                this.initializeWebKitSpeech();
            } else if (this.serviceType === 'google-cloud') {
                console.log('🌐 Attempting Google Cloud Speech (may have CORS issues)');
                await this.initializeGoogleCloudSpeech();
            } else {
                throw new Error('No speech recognition service available in this browser');
            }
            
            this.isInitialized = true;
            console.log('✅ Speech service initialized successfully');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize speech service:', error);
            
            // Try fallback to WebKit if Google Cloud fails
            if (this.serviceType === 'google-cloud' && 'webkitSpeechRecognition' in window) {
                console.log('🔄 Falling back to WebKit Speech Recognition');
                try {
                    this.serviceType = 'webkit';
                    this.initializeWebKitSpeech();
                    this.isInitialized = true;
                    return true;
                } catch (fallbackError) {
                    console.error('❌ Fallback also failed:', fallbackError);
                }
            }
            
            if (this.onError) {
                this.onError(`Speech recognition not available: ${error.message}`);
            }
            return false;
        }
    }
    
    async initializeGoogleCloudSpeech() {
        const apiKey = GOOGLE_CLOUD_CONFIG.API_KEY;
        this.currentService = new GoogleSpeechService(apiKey);
        
        // Set up event handlers
        this.currentService.onRecognitionResult((result) => {
            if (this.onResult) {
                this.onResult({
                    transcript: result.transcript,
                    confidence: result.confidence,
                    isFinal: result.isFinal
                });
            }
        });
        
        this.currentService.onRecognitionError((error) => {
            if (this.onError) {
                this.onError(error);
            }
        });
        
        this.currentService.onRecognitionStart(() => {
            if (this.onStart) {
                this.onStart();
            }
        });
        
        this.currentService.onRecognitionEnd(() => {
            if (this.onEnd) {
                this.onEnd();
            }
        });
        
        const initialized = await this.currentService.initialize();
        if (!initialized) {
            throw new Error('Google Cloud Speech service failed to initialize');
        }
        
        console.log('🌟 Google Cloud Speech-to-Text API initialized');
    }
    
    initializeWebKitSpeech() {
        if (!('webkitSpeechRecognition' in window)) {
            throw new Error('WebKit Speech Recognition not supported in this browser');
        }
        
        this.currentService = new webkitSpeechRecognition();
        this.currentService.continuous = false; // Changed to false for better reliability
        this.currentService.interimResults = false; // Changed to false for final results only
        this.currentService.lang = 'en-US';
        this.currentService.maxAlternatives = 1;
        
        this.currentService.onstart = () => {
            console.log('🎤 WebKit Speech Recognition started');
            if (this.onStart) {
                this.onStart();
            }
        };
        
        this.currentService.onend = () => {
            console.log('🔇 WebKit Speech Recognition ended');
            if (this.onEnd) {
                this.onEnd();
            }
        };
        
        this.currentService.onresult = (event) => {
            console.log('🗣️ WebKit speech result event:', event);
            const results = event.results;
            
            for (let i = 0; i < results.length; i++) {
                const result = results[i];
                if (result.isFinal && this.onResult) {
                    const transcript = result[0].transcript.trim();
                    const confidence = result[0].confidence || 0.85;
                    
                    console.log('📝 Final transcript:', transcript, 'confidence:', confidence);
                    
                    this.onResult({
                        transcript: transcript,
                        confidence: confidence,
                        isFinal: true
                    });
                }
            }
        };
        
        this.currentService.onerror = (event) => {
            console.error('❌ WebKit Speech Recognition error:', event.error);
            let errorMessage = `Speech recognition error: ${event.error}`;
            
            switch(event.error) {
                case 'no-speech':
                    errorMessage = 'No speech detected. Please try speaking louder.';
                    break;
                case 'audio-capture':
                    errorMessage = 'Microphone not accessible. Please check permissions.';
                    break;
                case 'not-allowed':
                    errorMessage = 'Microphone permission denied. Please allow microphone access.';
                    break;
                case 'network':
                    errorMessage = 'Network error. Please check your internet connection.';
                    break;
            }
            
            if (this.onError) {
                this.onError(errorMessage);
            }
        };
        
        console.log('⚡ WebKit Speech Recognition initialized successfully');
    }
    
    async startRecording() {
        if (!this.isInitialized) {
            const initialized = await this.initialize();
            if (!initialized) return false;
        }
        
        try {
            if (this.serviceType === 'google-cloud') {
                return await this.currentService.startRecording();
            } else {
                this.currentService.start();
                return true;
            }
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            if (this.onError) {
                this.onError(`Failed to start recording: ${error.message}`);
            }
            return false;
        }
    }
    
    stopRecording() {
        try {
            if (this.serviceType === 'google-cloud') {
                this.currentService.stopRecording();
            } else {
                this.currentService.stop();
            }
        } catch (error) {
            console.error('❌ Failed to stop recording:', error);
        }
    }
    
    // Streaming recognition (primarily for Google Cloud)
    async startStreamingRecognition() {
        if (!this.isInitialized) {
            const initialized = await this.initialize();
            if (!initialized) return false;
        }
        
        if (this.serviceType === 'google-cloud') {
            return await this.currentService.startStreamingRecognition();
        } else {
            // For WebKit, just use regular continuous recognition
            return await this.startRecording();
        }
    }
    
    // Event handler setters
    setOnResult(callback) {
        this.onResult = callback;
    }
    
    setOnError(callback) {
        this.onError = callback;
    }
    
    setOnStart(callback) {
        this.onStart = callback;
    }
    
    setOnEnd(callback) {
        this.onEnd = callback;
    }
    
    // Get service information
    getServiceInfo() {
        return {
            type: this.serviceType,
            isInitialized: this.isInitialized,
            isGoogleCloud: this.serviceType === 'google-cloud',
            apiConfigured: isGoogleCloudConfigured()
        };
    }
    
    // Cleanup
    destroy() {
        if (this.currentService) {
            if (this.serviceType === 'google-cloud') {
                this.currentService.destroy();
            } else {
                // WebKit doesn't need explicit cleanup
            }
        }
        
        this.currentService = null;
        this.isInitialized = false;
        console.log('🧹 Speech service destroyed');
    }
}

export default UnifiedSpeechService;