/**
 * AI-powered Speech Recorder with real-time processing
 * Integrates with OpenAI Whisper for speech-to-text
 */

class AISpeechRecorder {
    constructor(options = {}) {
        this.options = {
            sampleRate: 16000,
            channels: 1,
            bitsPerSample: 16,
            maxRecordingTime: 30000, // 30 seconds
            minRecordingTime: 500,   // 0.5 seconds
            autoStop: true,
            noiseGate: true,
            ...options
        };
        
        this.isRecording = false;
        this.isPaused = false;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioChunks = [];
        this.recordingStartTime = null;
        this.silenceTimer = null;
        this.audioContext = null;
        this.analyser = null;
        
        // Event callbacks
        this.onRecordingStart = options.onRecordingStart || (() => {});
        this.onRecordingStop = options.onRecordingStop || (() => {});
        this.onDataAvailable = options.onDataAvailable || (() => {});
        this.onError = options.onError || console.error;
        this.onVolumeChange = options.onVolumeChange || (() => {});
        
        this.setupAudioContext();
    }
    
    async setupAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (error) {
            console.warn('AudioContext not available:', error);
        }
    }
    
    async requestMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.options.sampleRate,
                    channelCount: this.options.channels,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Test the stream and stop it
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (error) {
            this.onError('Microphone permission denied: ' + error.message);
            return false;
        }
    }
    
    async startRecording() {
        if (this.isRecording) {
            console.warn('Already recording');
            return false;
        }
        
        try {
            // Get microphone access
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.options.sampleRate,
                    channelCount: this.options.channels,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Setup audio analysis
            this.setupAudioAnalysis();
            
            // Create MediaRecorder
            const options = {
                mimeType: this.getSupportedMimeType(),
                audioBitsPerSecond: this.options.sampleRate * this.options.bitsPerSample
            };
            
            this.mediaRecorder = new MediaRecorder(this.audioStream, options);
            this.audioChunks = [];
            
            // Setup event listeners
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.handleRecordingStop();
            };
            
            this.mediaRecorder.onerror = (error) => {
                this.onError('MediaRecorder error: ' + error.error);
            };
            
            // Start recording
            this.mediaRecorder.start(100); // Collect data every 100ms
            this.isRecording = true;
            this.recordingStartTime = Date.now();
            
            // Setup auto-stop timer
            if (this.options.autoStop) {
                setTimeout(() => {
                    if (this.isRecording) {
                        this.stopRecording();
                    }
                }, this.options.maxRecordingTime);
            }
            
            this.onRecordingStart();
            return true;
            
        } catch (error) {
            this.onError('Failed to start recording: ' + error.message);
            return false;
        }
    }
    
    stopRecording() {
        if (!this.isRecording) {
            return false;
        }
        
        const recordingDuration = Date.now() - this.recordingStartTime;
        
        if (recordingDuration < this.options.minRecordingTime) {
            this.onError('Recording too short');
            this.cleanup();
            return false;
        }
        
        this.isRecording = false;
        
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        } else {
            this.handleRecordingStop();
        }
        
        return true;
    }
    
    pauseRecording() {
        if (!this.isRecording || this.isPaused) {
            return false;
        }
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.pause();
            this.isPaused = true;
            return true;
        }
        
        return false;
    }
    
    resumeRecording() {
        if (!this.isRecording || !this.isPaused) {
            return false;
        }
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
            this.mediaRecorder.resume();
            this.isPaused = false;
            return true;
        }
        
        return false;
    }
    
    setupAudioAnalysis() {
        if (!this.audioContext) return;
        
        try {
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            source.connect(this.analyser);
            
            // Start volume monitoring
            this.monitorVolume();
        } catch (error) {
            console.warn('Audio analysis setup failed:', error);
        }
    }
    
    monitorVolume() {
        if (!this.analyser || !this.isRecording) return;
        
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const checkVolume = () => {
            if (!this.isRecording) return;
            
            this.analyser.getByteFrequencyData(dataArray);
            
            // Calculate RMS volume
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i] * dataArray[i];
            }
            const rms = Math.sqrt(sum / bufferLength);
            const volume = rms / 255; // Normalize to 0-1
            
            this.onVolumeChange(volume);
            
            // Continue monitoring
            requestAnimationFrame(checkVolume);
        };
        
        checkVolume();
    }
    
    handleRecordingStop() {
        if (this.audioChunks.length === 0) {
            this.onError('No audio data recorded');
            this.cleanup();
            return;
        }
        
        // Create audio blob
        const audioBlob = new Blob(this.audioChunks, {
            type: this.getSupportedMimeType()
        });
        
        // Convert to base64 for API transmission
        this.convertToBase64(audioBlob).then(base64Data => {
            const recordingData = {
                audioBlob: audioBlob,
                base64Data: base64Data,
                duration: Date.now() - this.recordingStartTime,
                format: this.getAudioFormat(),
                size: audioBlob.size
            };
            
            this.onRecordingStop(recordingData);
            this.onDataAvailable(recordingData);
        }).catch(error => {
            this.onError('Failed to process audio: ' + error.message);
        });
        
        this.cleanup();
    }
    
    convertToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                // Remove data URL prefix
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    cleanup() {
        // Stop all tracks
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
        
        // Clear timers
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }
        
        // Reset state
        this.isRecording = false;
        this.isPaused = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.analyser = null;
    }
    
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/ogg',
            'audio/mp4',
            'audio/wav'
        ];
        
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        
        return 'audio/webm'; // fallback
    }
    
    getAudioFormat() {
        const mimeType = this.getSupportedMimeType();
        if (mimeType.includes('webm')) return 'webm';
        if (mimeType.includes('ogg')) return 'ogg';
        if (mimeType.includes('mp4')) return 'mp4';
        if (mimeType.includes('wav')) return 'wav';
        return 'webm';
    }
    
    // Test microphone quality
    async testMicrophone(duration = 3000) {
        const testRecorder = new AISpeechRecorder({
            maxRecordingTime: duration,
            onRecordingStop: (data) => {
                this.sendMicrophoneTest(data);
            },
            onError: this.onError
        });
        
        return await testRecorder.startRecording();
    }
    
    async sendMicrophoneTest(recordingData) {
        try {
            const response = await fetch('/api/practice/test-microphone/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrftoken
                },
                body: JSON.stringify({
                    audio_data: recordingData.base64Data,
                    audio_format: recordingData.format
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayMicrophoneTestResults(result);
            } else {
                this.onError('Microphone test failed: ' + result.error);
            }
        } catch (error) {
            this.onError('Network error during microphone test: ' + error.message);
        }
    }
    
    displayMicrophoneTestResults(result) {
        const { quality_rating, recommendations, transcription_test } = result;
        
        // You can customize this based on your UI
        console.log('Microphone Test Results:', {
            quality: quality_rating,
            recommendations: recommendations,
            transcriptionTest: transcription_test
        });
        
        // Trigger custom event for UI updates
        window.dispatchEvent(new CustomEvent('microphoneTestComplete', {
            detail: result
        }));
    }
}

/**
 * AI Speech Practice Integration
 * Handles speech-to-text and practice session management
 */
class AISpeechPracticeManager {
    constructor(sessionKey, options = {}) {
        this.sessionKey = sessionKey;
        this.options = {
            autoProcessSpeech: true,
            showLiveTranscription: false,
            confidenceThreshold: 0.6,
            ...options
        };
        
        this.recorder = null;
        this.isProcessing = false;
        this.lastTranscription = '';
        
        // Event callbacks
        this.onSpeechProcessed = options.onSpeechProcessed || (() => {});
        this.onError = options.onError || console.error;
        this.onStatusChange = options.onStatusChange || (() => {});
    }
    
    async initializeRecorder() {
        this.recorder = new AISpeechRecorder({
            onRecordingStart: () => {
                this.onStatusChange('recording', 'Listening...');
            },
            onRecordingStop: (data) => {
                this.handleRecordingComplete(data);
            },
            onVolumeChange: (volume) => {
                this.updateVolumeIndicator(volume);
            },
            onError: this.onError
        });
        
        // Request microphone permission
        const hasPermission = await this.recorder.requestMicrophonePermission();
        if (!hasPermission) {
            throw new Error('Microphone permission required for speech practice');
        }
        
        return true;
    }
    
    async startListening() {
        if (!this.recorder) {
            await this.initializeRecorder();
        }
        
        return await this.recorder.startRecording();
    }
    
    stopListening() {
        if (this.recorder) {
            return this.recorder.stopRecording();
        }
        return false;
    }
    
    async handleRecordingComplete(recordingData) {
        if (this.isProcessing) return;
        
        this.isProcessing = true;
        this.onStatusChange('processing', 'Processing speech...');
        
        try {
            const response = await fetch('/api/practice/speech/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrftoken
                },
                body: JSON.stringify({
                    session_key: this.sessionKey,
                    audio_data: recordingData.base64Data,
                    audio_format: recordingData.format
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.lastTranscription = result.ai_analysis?.transcription || '';
                this.onSpeechProcessed(result);
                this.onStatusChange('ready', 'Ready to listen...');
            } else {
                this.handleSpeechError(result);
            }
            
        } catch (error) {
            this.onError('Network error processing speech: ' + error.message);
            this.onStatusChange('error', 'Network error');
        } finally {
            this.isProcessing = false;
        }
    }
    
    handleSpeechError(result) {
        if (result.quality_issues) {
            this.onStatusChange('warning', 'Audio quality issues detected');
            this.onError('Audio quality too low: ' + result.quality_issues.join(', '));
        } else if (result.transcription_attempted) {
            this.onStatusChange('warning', 'Speech not recognized clearly');
            this.onError('Speech recognition failed: ' + result.error);
        } else {
            this.onStatusChange('error', 'Processing failed');
            this.onError('Speech processing error: ' + result.error);
        }
    }
    
    updateVolumeIndicator(volume) {
        // Trigger custom event for volume visualization
        window.dispatchEvent(new CustomEvent('speechVolumeUpdate', {
            detail: { volume: volume }
        }));
    }
    
    async requestPronunciationFeedback(spokenText, expectedWord) {
        try {
            const response = await fetch('/api/practice/pronunciation-feedback/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrftoken
                },
                body: JSON.stringify({
                    spoken_text: spokenText,
                    expected_word: expectedWord,
                    context: 'practice_session'
                })
            });
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            console.error('Failed to get pronunciation feedback:', error);
            return { success: false, error: error.message };
        }
    }
    
    destroy() {
        if (this.recorder) {
            this.recorder.cleanup();
            this.recorder = null;
        }
        this.isProcessing = false;
    }
}

// Export for use in other modules
window.AISpeechRecorder = AISpeechRecorder;
window.AISpeechPracticeManager = AISpeechPracticeManager;