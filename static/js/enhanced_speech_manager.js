/**
 * Enhanced Speech Recognition Manager
 * Combines streaming recognition with Web Speech API for optimal results
 */

class EnhancedSpeechManager {
    constructor(options = {}) {
        this.options = {
            useWebSpeech: true,
            useStreaming: true,
            preferWebSpeech: true,  // Web Speech API is better for natural speech
            fusionMode: 'best_confidence', // 'best_confidence', 'fastest', 'consensus'
            confidenceThreshold: 0.6,
            timeout: 10000, // 10 seconds
            ...options
        };
        
        this.webSpeechRecognizer = null;
        this.streamingRecorder = null;
        this.currentMethod = null;
        this.isRecording = false;
        this.results = [];
        
        // Callbacks
        this.onResult = options.onResult || (() => {});
        this.onInterimResult = options.onInterimResult || (() => {});
        this.onError = options.onError || console.error;
        this.onStart = options.onStart || (() => {});
        this.onStop = options.onStop || (() => {});
        
        this.initializeRecognizers();
    }
    
    initializeRecognizers() {
        // Initialize Web Speech API recognizer
        if (this.options.useWebSpeech && typeof WebSpeechRecognizer !== 'undefined') {
            this.webSpeechRecognizer = new WebSpeechRecognizer({
                continuous: false,
                interimResults: true,
                maxAlternatives: 3,
                autoRestart: false,
                confidenceThreshold: this.options.confidenceThreshold,
                onResult: (result) => this.handleWebSpeechResult(result),
                onInterimResult: (result) => this.handleWebSpeechInterim(result),
                onFinalResult: (result) => this.handleWebSpeechFinal(result),
                onError: (error) => this.handleWebSpeechError(error),
                onStart: () => console.log('Web Speech started'),
                onEnd: () => console.log('Web Speech ended')
            });
            
            console.log('Web Speech recognizer initialized');
        }
        
        // Initialize streaming recognizer
        if (this.options.useStreaming && typeof StreamingSpeechRecorder !== 'undefined') {
            this.streamingRecorder = new StreamingSpeechRecorder({
                naturalSpeechMode: true,
                chunkDuration: 4000, // 4 second chunks
                maxSilence: 6000,    // 6 seconds of silence
                volumeThreshold: 0.003,
                vadThreshold: 0.2,
                onChunkReady: (chunk) => this.handleStreamingChunk(chunk),
                onError: (error) => this.handleStreamingError(error),
                onStreamStart: () => console.log('Streaming started'),
                onStreamStop: () => console.log('Streaming stopped')
            });
            
            console.log('Streaming recognizer initialized');
        }
    }
    
    async startRecognition(preferredMethod = null) {
        if (this.isRecording) {
            console.warn('Recognition already in progress');
            return false;
        }
        
        this.isRecording = true;
        this.results = [];
        this.currentMethod = preferredMethod || this.selectBestMethod();
        
        console.log(`Starting recognition with method: ${this.currentMethod}`);
        
        try {
            if (this.currentMethod === 'webspeech' && this.webSpeechRecognizer) {
                const started = this.webSpeechRecognizer.start();
                if (started) {
                    this.onStart({ method: 'webspeech' });
                    return true;
                }
            }
            
            if (this.currentMethod === 'streaming' && this.streamingRecorder) {
                const started = await this.streamingRecorder.startStreaming();
                if (started) {
                    this.onStart({ method: 'streaming' });
                    return true;
                }
            }
            
            // Fallback to alternative method
            return await this.startFallbackMethod();
            
        } catch (error) {
            console.error('Failed to start recognition:', error);
            this.isRecording = false;
            this.onError({
                error: 'start_failed',
                message: 'Failed to start speech recognition: ' + error.message
            });
            return false;
        }
    }
    
    async startFallbackMethod() {
        console.log('Trying fallback recognition method');
        
        if (this.currentMethod !== 'webspeech' && this.webSpeechRecognizer) {
            this.currentMethod = 'webspeech';
            const started = this.webSpeechRecognizer.start();
            if (started) {
                this.onStart({ method: 'webspeech', fallback: true });
                return true;
            }
        }
        
        if (this.currentMethod !== 'streaming' && this.streamingRecorder) {
            this.currentMethod = 'streaming';
            const started = await this.streamingRecorder.startStreaming();
            if (started) {
                this.onStart({ method: 'streaming', fallback: true });
                return true;
            }
        }
        
        this.isRecording = false;
        this.onError({
            error: 'no_method_available',
            message: 'No speech recognition method available'
        });
        return false;
    }
    
    selectBestMethod() {
        // Prefer Web Speech API for natural speech recognition
        if (this.options.preferWebSpeech && this.webSpeechRecognizer?.isSupported) {
            return 'webspeech';
        }
        
        if (this.streamingRecorder) {
            return 'streaming';
        }
        
        if (this.webSpeechRecognizer?.isSupported) {
            return 'webspeech';
        }
        
        return null;
    }
    
    stopRecognition() {
        if (!this.isRecording) {
            return;
        }
        
        console.log('Stopping recognition');
        this.isRecording = false;
        
        if (this.currentMethod === 'webspeech' && this.webSpeechRecognizer) {
            this.webSpeechRecognizer.stop();
        }
        
        if (this.currentMethod === 'streaming' && this.streamingRecorder) {
            this.streamingRecorder.stopStreaming();
        }
        
        this.onStop({ method: this.currentMethod, results: this.results });
    }
    
    handleWebSpeechResult(result) {
        console.log('Web Speech result:', result);
        this.results.push({
            method: 'webspeech',
            type: 'result',
            data: result,
            timestamp: Date.now()
        });
    }
    
    handleWebSpeechInterim(result) {
        console.log('Web Speech interim:', result.transcript);
        this.onInterimResult({
            transcript: result.transcript,
            confidence: result.confidence,
            method: 'webspeech',
            isFinal: false
        });
    }
    
    handleWebSpeechFinal(result) {
        console.log('Web Speech final:', result.transcript, 'confidence:', result.confidence);
        
        this.results.push({
            method: 'webspeech',
            type: 'final',
            data: result,
            timestamp: Date.now()
        });
        
        // Auto-stop on final result for single phrase recognition
        if (!this.webSpeechRecognizer.options.continuous) {
            setTimeout(() => this.stopRecognition(), 100);
        }
        
        this.onResult({
            transcript: result.transcript,
            confidence: result.confidence,
            method: 'webspeech',
            isFinal: true,
            alternatives: result.alternatives
        });
    }
    
    handleWebSpeechError(error) {
        console.error('Web Speech error:', error);
        
        // Handle recoverable errors
        if (error.error === 'no-speech' && this.streamingRecorder) {
            console.log('No speech detected, falling back to streaming');
            this.currentMethod = 'streaming';
            this.streamingRecorder.startStreaming();
            return;
        }
        
        this.onError({
            method: 'webspeech',
            error: error.error,
            message: error.message,
            fatal: error.fatal
        });
        
        if (error.fatal) {
            this.isRecording = false;
        }
    }
    
    async handleStreamingChunk(chunk) {
        console.log('Processing streaming chunk:', chunk.sequence);
        
        try {
            // Send chunk to backend for processing
            const response = await fetch('/memorization/process_speech_chunk/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    audio_data: chunk.base64Data,
                    format: chunk.format,
                    chunk_info: {
                        sequence: chunk.sequence,
                        timestamp: chunk.timestamp,
                        speech_probability: chunk.speechProbability
                    }
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.transcription) {
                this.results.push({
                    method: 'streaming',
                    type: 'chunk',
                    data: result,
                    timestamp: Date.now()
                });
                
                this.onResult({
                    transcript: result.transcription,
                    confidence: result.confidence || 0.5,
                    method: 'streaming',
                    isFinal: false,
                    provider: result.provider
                });
            }
            
        } catch (error) {
            console.error('Error processing streaming chunk:', error);
            this.handleStreamingError('Processing error: ' + error.message);
        }
    }
    
    handleStreamingError(error) {
        console.error('Streaming error:', error);
        this.onError({
            method: 'streaming',
            error: 'streaming_error',
            message: error,
            fatal: false
        });
    }
    
    getBestResult() {
        if (this.results.length === 0) {
            return null;
        }
        
        // Filter final/complete results
        const finalResults = this.results.filter(r => 
            r.type === 'final' || (r.type === 'chunk' && r.data.transcription)
        );
        
        if (finalResults.length === 0) {
            return null;
        }
        
        // Sort by confidence and method preference
        finalResults.sort((a, b) => {
            const confidenceA = a.data.confidence || 0;
            const confidenceB = b.data.confidence || 0;
            
            // Prefer Web Speech API if confidence is similar
            if (Math.abs(confidenceA - confidenceB) < 0.1) {
                if (a.method === 'webspeech' && b.method !== 'webspeech') return -1;
                if (b.method === 'webspeech' && a.method !== 'webspeech') return 1;
            }
            
            return confidenceB - confidenceA;
        });
        
        return finalResults[0];
    }
    
    getAvailableMethods() {
        const methods = [];
        
        if (this.webSpeechRecognizer?.isSupported) {
            methods.push('webspeech');
        }
        
        if (this.streamingRecorder) {
            methods.push('streaming');
        }
        
        return methods;
    }
    
    getStatus() {
        return {
            isRecording: this.isRecording,
            currentMethod: this.currentMethod,
            availableMethods: this.getAvailableMethods(),
            resultsCount: this.results.length,
            webSpeechSupported: this.webSpeechRecognizer?.isSupported || false,
            streamingAvailable: !!this.streamingRecorder
        };
    }
}

// Export for use in other scripts
window.EnhancedSpeechManager = EnhancedSpeechManager;