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
            if (this.serviceType === 'google-cloud') {
                await this.initializeGoogleCloudSpeech();
            } else if (this.serviceType === 'webkit') {
                this.initializeWebKitSpeech();
            } else {
                throw new Error('No speech recognition service available');
            }
            
            this.isInitialized = true;
            console.log('✅ Speech service initialized successfully');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize speech service:', error);
            if (this.onError) {
                this.onError(`Failed to initialize speech recognition: ${error.message}`);
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
            throw new Error('WebKit Speech Recognition not supported');
        }
        
        this.currentService = new webkitSpeechRecognition();
        this.currentService.continuous = true;
        this.currentService.interimResults = true;
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
            const results = event.results;
            const lastResult = results[results.length - 1];
            
            if (lastResult.isFinal && this.onResult) {
                this.onResult({
                    transcript: lastResult[0].transcript.trim(),
                    confidence: lastResult[0].confidence || 0.8,
                    isFinal: true
                });
            }
        };
        
        this.currentService.onerror = (event) => {
            console.error('WebKit Speech Recognition error:', event.error);
            if (this.onError) {
                this.onError(`Speech recognition error: ${event.error}`);
            }
        };
        
        console.log('⚡ WebKit Speech Recognition initialized (fallback mode)');
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