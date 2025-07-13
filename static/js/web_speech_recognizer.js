/**
 * Web Speech API recognizer for natural speech recognition
 * Provides browser-native speech recognition as a fallback/alternative
 */

class WebSpeechRecognizer {
    constructor(options = {}) {
        this.options = {
            language: 'en-US',
            continuous: true,
            interimResults: true,
            maxAlternatives: 3,
            autoRestart: true,
            restartDelay: 1000,
            confidenceThreshold: 0.7,
            ...options
        };
        
        this.recognition = null;
        this.isSupported = this.checkSupport();
        this.isRecognizing = false;
        this.finalTranscript = '';
        this.interimTranscript = '';
        this.lastResultTime = 0;
        this.restartTimer = null;
        
        // Callbacks
        this.onResult = options.onResult || (() => {});
        this.onInterimResult = options.onInterimResult || (() => {});
        this.onFinalResult = options.onFinalResult || (() => {});
        this.onError = options.onError || console.error;
        this.onStart = options.onStart || (() => {});
        this.onEnd = options.onEnd || (() => {});
        
        if (this.isSupported) {
            this.initializeRecognition();
        }
    }
    
    checkSupport() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn('Web Speech API not supported in this browser');
            return false;
        }
        return true;
    }
    
    initializeRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition
        this.recognition.continuous = this.options.continuous;
        this.recognition.interimResults = this.options.interimResults;
        this.recognition.maxAlternatives = this.options.maxAlternatives;
        this.recognition.lang = this.options.language;
        
        // Set up event handlers
        this.recognition.onstart = () => {
            console.log('Web Speech Recognition started');
            this.isRecognizing = true;
            this.onStart();
        };
        
        this.recognition.onresult = (event) => {
            this.handleResults(event);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Web Speech Recognition error:', event.error);
            this.handleError(event);
        };
        
        this.recognition.onend = () => {
            console.log('Web Speech Recognition ended');
            this.isRecognizing = false;
            this.onEnd();
            
            // Auto-restart if enabled and not manually stopped
            if (this.options.autoRestart && !this.manualStop) {
                this.scheduleRestart();
            }
        };
    }
    
    handleResults(event) {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;
            const confidence = result[0].confidence || 0;
            
            if (result.isFinal) {
                if (confidence >= this.options.confidenceThreshold) {
                    finalTranscript += transcript;
                    this.finalTranscript += transcript;
                    
                    // Call final result callback
                    this.onFinalResult({
                        transcript: transcript,
                        confidence: confidence,
                        isFinal: true,
                        alternatives: this.getAlternatives(result)
                    });
                }
            } else {
                interimTranscript += transcript;
                
                // Call interim result callback
                this.onInterimResult({
                    transcript: transcript,
                    confidence: confidence,
                    isFinal: false,
                    alternatives: this.getAlternatives(result)
                });
            }
        }
        
        this.interimTranscript = interimTranscript;
        this.lastResultTime = Date.now();
        
        // Call general result callback
        this.onResult({
            finalTranscript: this.finalTranscript,
            interimTranscript: interimTranscript,
            lastUpdate: this.lastResultTime
        });
    }
    
    getAlternatives(result) {
        const alternatives = [];
        for (let i = 0; i < result.length; i++) {
            alternatives.push({
                transcript: result[i].transcript,
                confidence: result[i].confidence || 0
            });
        }
        return alternatives;
    }
    
    handleError(event) {
        const errorMessage = this.getErrorMessage(event.error);
        this.onError({
            error: event.error,
            message: errorMessage,
            fatal: this.isFatalError(event.error)
        });
        
        // Auto-restart on recoverable errors
        if (!this.isFatalError(event.error) && this.options.autoRestart) {
            this.scheduleRestart();
        }
    }
    
    getErrorMessage(error) {
        const errorMessages = {
            'no-speech': 'No speech was detected. Please try speaking again.',
            'audio-capture': 'Audio capture failed. Please check your microphone.',
            'not-allowed': 'Microphone permission denied. Please allow microphone access.',
            'network': 'Network error occurred. Please check your internet connection.',
            'service-not-allowed': 'Speech recognition service is not allowed.',
            'bad-grammar': 'Grammar error in speech recognition.',
            'language-not-supported': 'Language not supported.',
            'aborted': 'Speech recognition was aborted.'
        };
        
        return errorMessages[error] || `Speech recognition error: ${error}`;
    }
    
    isFatalError(error) {
        const fatalErrors = ['not-allowed', 'service-not-allowed', 'language-not-supported'];
        return fatalErrors.includes(error);
    }
    
    scheduleRestart() {
        if (this.restartTimer) {
            clearTimeout(this.restartTimer);
        }
        
        this.restartTimer = setTimeout(() => {
            if (!this.isRecognizing && !this.manualStop) {
                console.log('Auto-restarting speech recognition');
                this.start();
            }
        }, this.options.restartDelay);
    }
    
    start() {
        if (!this.isSupported) {
            this.onError({
                error: 'not-supported',
                message: 'Web Speech API is not supported in this browser',
                fatal: true
            });
            return false;
        }
        
        if (this.isRecognizing) {
            console.warn('Speech recognition is already running');
            return false;
        }
        
        try {
            this.manualStop = false;
            this.finalTranscript = '';
            this.interimTranscript = '';
            this.recognition.start();
            return true;
        } catch (error) {
            console.error('Failed to start speech recognition:', error);
            this.onError({
                error: 'start-failed',
                message: 'Failed to start speech recognition: ' + error.message,
                fatal: false
            });
            return false;
        }
    }
    
    stop() {
        if (!this.isRecognizing) {
            return;
        }
        
        this.manualStop = true;
        
        if (this.restartTimer) {
            clearTimeout(this.restartTimer);
            this.restartTimer = null;
        }
        
        try {
            this.recognition.stop();
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
        }
    }
    
    abort() {
        if (!this.isRecognizing) {
            return;
        }
        
        this.manualStop = true;
        
        if (this.restartTimer) {
            clearTimeout(this.restartTimer);
            this.restartTimer = null;
        }
        
        try {
            this.recognition.abort();
        } catch (error) {
            console.error('Error aborting speech recognition:', error);
        }
    }
    
    isActive() {
        return this.isRecognizing;
    }
    
    getLastTranscript() {
        return {
            final: this.finalTranscript,
            interim: this.interimTranscript,
            combined: this.finalTranscript + this.interimTranscript,
            lastUpdate: this.lastResultTime
        };
    }
    
    clearTranscript() {
        this.finalTranscript = '';
        this.interimTranscript = '';
    }
    
    updateOptions(newOptions) {
        Object.assign(this.options, newOptions);
        
        if (this.recognition) {
            this.recognition.continuous = this.options.continuous;
            this.recognition.interimResults = this.options.interimResults;
            this.recognition.maxAlternatives = this.options.maxAlternatives;
            this.recognition.lang = this.options.language;
        }
    }
    
    getSupport() {
        return {
            isSupported: this.isSupported,
            hasPermission: navigator.permissions ? 
                navigator.permissions.query({name: 'microphone'}) : null,
            browser: this.detectBrowser()
        };
    }
    
    detectBrowser() {
        const userAgent = navigator.userAgent;
        if (userAgent.includes('Chrome')) return 'chrome';
        if (userAgent.includes('Firefox')) return 'firefox';
        if (userAgent.includes('Safari')) return 'safari';
        if (userAgent.includes('Edge')) return 'edge';
        return 'unknown';
    }
}

// Export for use in other scripts
window.WebSpeechRecognizer = WebSpeechRecognizer;