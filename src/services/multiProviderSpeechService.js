/**
 * Multi-Provider Speech Recognition Service
 * Implements sophisticated failover system from deployment-fixes branch
 */

class MultiProviderSpeechService {
    constructor() {
        this.providers = {
            'openai': {
                enabled: !!window.OPENAI_API_KEY,
                priority: 1,
                rateLimit: 50,
                lastRequestTime: 0,
                errorCount: 0,
                service: null
            },
            'google': {
                enabled: !!window.GOOGLE_CLOUD_API_KEY,
                priority: 2,
                rateLimit: 100,
                lastRequestTime: 0,
                errorCount: 0,
                service: null
            },
            'webkit': {
                enabled: 'webkitSpeechRecognition' in window,
                priority: 3,
                rateLimit: 1000,
                lastRequestTime: 0,
                errorCount: 0,
                service: null
            },
            'azure': {
                enabled: !!window.AZURE_SPEECH_KEY,
                priority: 4,
                rateLimit: 200,
                lastRequestTime: 0,
                errorCount: 0,
                service: null
            }
        };

        this.supportedFormats = ['webm', 'wav', 'mp3', 'mp4', 'mpeg', 'mpga', 'm4a'];
        this.isTranscribing = false;
        this.onResult = null;
        this.onError = null;
        this.onProviderSwitch = null;
    }

    async initialize() {
        console.log('🔧 Initializing multi-provider speech service...');
        
        // Initialize Google Cloud service if available
        if (this.providers.google.enabled) {
            const { default: GoogleSpeechService } = await import('./googleSpeechService.js');
            this.providers.google.service = new GoogleSpeechService(window.GOOGLE_CLOUD_API_KEY);
            await this.providers.google.service.initialize();
        }

        // Initialize WebKit service
        if (this.providers.webkit.enabled) {
            this.providers.webkit.service = this._createWebKitService();
        }

        const enabledProviders = this._getAvailableProviders();
        console.log(`✅ Multi-provider service initialized with ${enabledProviders.length} providers:`, 
                   enabledProviders.map(name => `${name} (priority ${this.providers[name].priority})`));
        
        return enabledProviders.length > 0;
    }

    async transcribeAudio(audioData, audioFormat = 'webm') {
        if (this.isTranscribing) {
            return {
                success: false,
                error: 'Transcription already in progress',
                transcript: ''
            };
        }

        if (!this.supportedFormats.includes(audioFormat)) {
            return {
                success: false,
                error: `Unsupported audio format: ${audioFormat}`,
                transcript: ''
            };
        }

        this.isTranscribing = true;
        const providersToTry = this._getAvailableProviders();

        console.log('🎤 Starting multi-provider transcription with providers:', providersToTry);

        for (const providerName of providersToTry) {
            try {
                console.log(`🔄 Trying provider: ${providerName}`);
                
                const result = await this._transcribeWithProvider(audioData, audioFormat, providerName);
                
                if (result.success) {
                    result.provider = providerName;
                    this._updateProviderSuccess(providerName);
                    this.isTranscribing = false;
                    
                    console.log(`✅ Transcription successful with ${providerName}:`, result.transcript);
                    
                    if (this.onResult) {
                        this.onResult(result);
                    }
                    
                    return result;
                } else {
                    console.warn(`❌ ${providerName} provider failed:`, result.error);
                    this._updateProviderError(providerName);
                }
                
            } catch (error) {
                console.error(`💥 ${providerName} provider exception:`, error);
                this._updateProviderError(providerName);
            }
        }

        // All providers failed
        this.isTranscribing = false;
        const errorResult = {
            success: false,
            error: 'All speech recognition providers failed',
            transcript: '',
            providersAttempted: providersToTry
        };

        if (this.onError) {
            this.onError(errorResult.error);
        }

        return errorResult;
    }

    _getAvailableProviders() {
        const available = [];
        
        for (const [name, config] of Object.entries(this.providers)) {
            if (config.enabled && this._isProviderHealthy(name)) {
                available.push([name, config.priority, config.errorCount]);
            }
        }

        // Sort by priority (lower is better) and error count (lower is better)
        available.sort((a, b) => {
            if (a[1] !== b[1]) return a[1] - b[1]; // Priority
            return a[2] - b[2]; // Error count
        });

        return available.map(item => item[0]);
    }

    _isProviderHealthy(providerName) {
        const config = this.providers[providerName];
        
        // Check rate limiting
        const timeSinceLastRequest = Date.now() - config.lastRequestTime;
        const minInterval = (60 * 1000) / config.rateLimit;
        
        if (timeSinceLastRequest < minInterval) {
            return false;
        }

        // Check error threshold
        if (config.errorCount > 5) {
            return false;
        }

        return true;
    }

    async _transcribeWithProvider(audioData, audioFormat, provider) {
        this.providers[provider].lastRequestTime = Date.now();

        switch (provider) {
            case 'openai':
                return await this._transcribeOpenAI(audioData, audioFormat);
            case 'google':
                return await this._transcribeGoogle(audioData, audioFormat);
            case 'webkit':
                return await this._transcribeWebKit(audioData);
            case 'azure':
                return await this._transcribeAzure(audioData, audioFormat);
            default:
                return {
                    success: false,
                    error: `Unknown provider: ${provider}`
                };
        }
    }

    async _transcribeOpenAI(audioData, audioFormat) {
        try {
            if (!window.OPENAI_API_KEY) {
                throw new Error('OpenAI API key not configured');
            }

            // Create form data for OpenAI Whisper API
            const formData = new FormData();
            const audioBlob = new Blob([audioData], { type: `audio/${audioFormat}` });
            formData.append('file', audioBlob, `audio.${audioFormat}`);
            formData.append('model', 'whisper-1');
            formData.append('language', 'en');
            formData.append('response_format', 'verbose_json');
            formData.append('temperature', '0.0');
            formData.append('prompt', 'This is conversational speech for memorization practice. Please transcribe naturally spoken sentences.');

            const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${window.OPENAI_API_KEY}`
                },
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`OpenAI API error: ${response.status} - ${errorText}`);
            }

            const result = await response.json();
            const confidence = this._calculateWhisperConfidence(result);

            return {
                success: true,
                transcript: result.text.trim(),
                confidence: confidence,
                language: result.language || 'en',
                duration: result.duration || 0,
                segments: result.segments || []
            };

        } catch (error) {
            return {
                success: false,
                error: `OpenAI Whisper failed: ${error.message}`
            };
        }
    }

    async _transcribeGoogle(audioData, audioFormat) {
        if (this.providers.google.service) {
            try {
                // Convert audioData to base64 for Google Cloud API
                const base64Data = await this._audioDataToBase64(audioData);
                return await this.providers.google.service.recognizeSpeech(base64Data);
            } catch (error) {
                return {
                    success: false,
                    error: `Google Cloud Speech failed: ${error.message}`
                };
            }
        }
        
        return {
            success: false,
            error: 'Google Cloud Speech service not initialized'
        };
    }

    async _transcribeWebKit(audioData) {
        return new Promise((resolve) => {
            if (!this.providers.webkit.service) {
                resolve({
                    success: false,
                    error: 'WebKit Speech Recognition not available'
                });
                return;
            }

            const recognition = this.providers.webkit.service;
            let resolved = false;

            recognition.onresult = (event) => {
                if (resolved) return;
                resolved = true;

                const result = event.results[event.results.length - 1];
                const transcript = result[0].transcript;
                const confidence = result[0].confidence || 0.7;

                resolve({
                    success: true,
                    transcript: transcript.trim(),
                    confidence: confidence,
                    language: 'en'
                });
            };

            recognition.onerror = (event) => {
                if (resolved) return;
                resolved = true;

                resolve({
                    success: false,
                    error: `WebKit Speech Recognition error: ${event.error}`
                });
            };

            recognition.onend = () => {
                if (!resolved) {
                    resolved = true;
                    resolve({
                        success: false,
                        error: 'WebKit Speech Recognition ended without result'
                    });
                }
            };

            try {
                recognition.start();
            } catch (error) {
                resolve({
                    success: false,
                    error: `Failed to start WebKit recognition: ${error.message}`
                });
            }
        });
    }

    async _transcribeAzure(audioData, audioFormat) {
        try {
            if (!window.AZURE_SPEECH_KEY || !window.AZURE_SPEECH_REGION) {
                throw new Error('Azure Speech API credentials not configured');
            }

            // Convert to WAV format for Azure
            const wavData = await this._convertToWav(audioData, audioFormat);
            
            const region = window.AZURE_SPEECH_REGION;
            const url = `https://${region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1`;
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Ocp-Apim-Subscription-Key': window.AZURE_SPEECH_KEY,
                    'Content-Type': 'audio/wav',
                    'Accept': 'application/json'
                },
                body: wavData
            });

            if (!response.ok) {
                throw new Error(`Azure API error: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.RecognitionStatus === 'Success') {
                const bestResult = result.NBest?.[0] || result;
                return {
                    success: true,
                    transcript: bestResult.Display || '',
                    confidence: bestResult.Confidence || 0.7,
                    language: 'en'
                };
            } else {
                return {
                    success: false,
                    error: `Azure recognition failed: ${result.RecognitionStatus}`
                };
            }

        } catch (error) {
            return {
                success: false,
                error: `Azure Speech failed: ${error.message}`
            };
        }
    }

    _createWebKitService() {
        if (!('webkitSpeechRecognition' in window)) {
            return null;
        }

        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        return recognition;
    }

    _calculateWhisperConfidence(whisperResult) {
        if (whisperResult.segments && whisperResult.segments.length > 0) {
            // Calculate average confidence from segments
            const confidences = whisperResult.segments
                .filter(segment => segment.avg_logprob !== undefined)
                .map(segment => Math.min(1.0, Math.max(0.0, segment.avg_logprob + 1.0)));
            
            if (confidences.length > 0) {
                return confidences.reduce((sum, conf) => sum + conf, 0) / confidences.length;
            }
        }

        // Default confidence based on text length
        const textLength = whisperResult.text ? whisperResult.text.trim().length : 0;
        if (textLength === 0) return 0.0;
        if (textLength < 5) return 0.6;
        return 0.8;
    }

    async _audioDataToBase64(audioData) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            const blob = new Blob([audioData]);
            
            reader.onloadend = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    async _convertToWav(audioData, fromFormat) {
        // For now, assume audioData is already in correct format
        // In production, you'd use a proper audio conversion library
        if (fromFormat === 'wav') {
            return audioData;
        }
        
        // Simplified conversion - in production use proper audio processing
        return audioData;
    }

    _updateProviderSuccess(providerName) {
        if (this.providers[providerName]) {
            this.providers[providerName].errorCount = Math.max(0, this.providers[providerName].errorCount - 1);
        }
    }

    _updateProviderError(providerName) {
        if (this.providers[providerName]) {
            this.providers[providerName].errorCount += 1;
            
            if (this.onProviderSwitch) {
                this.onProviderSwitch(providerName, this.providers[providerName].errorCount);
            }
        }
    }

    getProviderStatus() {
        const status = {};
        for (const [name, config] of Object.entries(this.providers)) {
            status[name] = {
                enabled: config.enabled,
                healthy: this._isProviderHealthy(name),
                errorCount: config.errorCount,
                priority: config.priority
            };
        }
        return status;
    }

    // Event handlers
    onRecognitionResult(callback) {
        this.onResult = callback;
    }

    onRecognitionError(callback) {
        this.onError = callback;
    }

    onProviderSwitchEvent(callback) {
        this.onProviderSwitch = callback;
    }
}

export default MultiProviderSpeechService;