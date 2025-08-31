/**
 * Real-time Streaming Speech Recognition Service
 * Implements continuous speech recognition with live feedback
 * Based on streaming_views.py from deployment-fixes branch
 */

class StreamingRecognitionService {
    constructor() {
        this.isStreaming = false;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioChunks = [];
        this.chunkSize = 1000; // 1-second chunks
        this.processingTimeout = null;
        
        // Callbacks
        this.onInterimResult = null;
        this.onFinalResult = null;
        this.onError = null;
        this.onStreamingStart = null;
        this.onStreamingEnd = null;
        this.onVolumeLevel = null;
        
        // Configuration
        this.config = {
            interimResults: true,
            singleUtterance: false,
            continuous: true,
            language: 'en-US',
            maxAlternatives: 3
        };

        // Audio analysis
        this.audioContext = null;
        this.analyser = null;
        this.volumeData = null;
        this.volumeCallback = null;
        
        // Speech detection
        this.speechDetectionThreshold = 0.01;
        this.silenceThreshold = 0.005;
        this.silenceDuration = 2000; // 2 seconds of silence
        this.lastSpeechTime = 0;
        this.speechDetected = false;
    }

    async initialize() {
        try {
            console.log('🔧 Initializing streaming recognition service...');
            
            // Request microphone permission and setup audio stream
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000,
                    channelCount: 1
                }
            });

            // Setup audio context for volume monitoring
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 512;
            source.connect(this.analyser);
            
            this.volumeData = new Uint8Array(this.analyser.frequencyBinCount);
            
            console.log('✅ Streaming recognition service initialized');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize streaming service:', error);
            if (this.onError) {
                this.onError(`Microphone access denied: ${error.message}`);
            }
            return false;
        }
    }

    async startStreaming(multiProviderService) {
        if (this.isStreaming) {
            console.warn('⚠️ Streaming already active');
            return false;
        }

        if (!this.audioStream) {
            const initialized = await this.initialize();
            if (!initialized) return false;
        }

        try {
            this.isStreaming = true;
            this.audioChunks = [];
            this.speechDetected = false;
            this.lastSpeechTime = 0;

            // Setup media recorder for chunk-based processing
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.mediaRecorder.ondataavailable = async (event) => {
                if (event.data.size > 0 && this.isStreaming) {
                    await this._processAudioChunk(event.data, multiProviderService);
                }
            };

            this.mediaRecorder.onerror = (error) => {
                console.error('MediaRecorder error:', error);
                if (this.onError) {
                    this.onError('Recording error occurred');
                }
            };

            // Start recording in chunks
            this.mediaRecorder.start(this.chunkSize);
            
            // Start volume monitoring
            this._startVolumeMonitoring();
            
            if (this.onStreamingStart) {
                this.onStreamingStart();
            }

            console.log('🎤 Started streaming recognition');
            return true;

        } catch (error) {
            console.error('❌ Failed to start streaming:', error);
            this.isStreaming = false;
            if (this.onError) {
                this.onError(`Streaming failed: ${error.message}`);
            }
            return false;
        }
    }

    stopStreaming() {
        if (!this.isStreaming) return;

        console.log('🛑 Stopping streaming recognition...');
        this.isStreaming = false;

        // Stop media recorder
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        // Clear processing timeout
        if (this.processingTimeout) {
            clearTimeout(this.processingTimeout);
        }

        // Stop volume monitoring
        this._stopVolumeMonitoring();

        // Process any remaining chunks
        if (this.audioChunks.length > 0) {
            this._processAccumulatedAudio();
        }

        if (this.onStreamingEnd) {
            this.onStreamingEnd();
        }
    }

    async _processAudioChunk(audioBlob, multiProviderService) {
        if (!this.isStreaming || !multiProviderService) return;

        try {
            // Add to accumulated chunks
            this.audioChunks.push(audioBlob);
            
            // Check for speech activity
            const volumeLevel = this._getCurrentVolumeLevel();
            
            if (volumeLevel > this.speechDetectionThreshold) {
                this.lastSpeechTime = Date.now();
                if (!this.speechDetected) {
                    this.speechDetected = true;
                    console.log('🗣️ Speech detected, starting recognition...');
                }
            }

            // Process accumulated audio if we have enough or if speech ended
            const timeSinceSpeech = Date.now() - this.lastSpeechTime;
            const shouldProcess = this.audioChunks.length >= 3 || 
                                 (this.speechDetected && timeSinceSpeech > this.silenceDuration);

            if (shouldProcess && this.audioChunks.length > 0) {
                // Combine accumulated chunks
                const combinedBlob = new Blob(this.audioChunks, { type: 'audio/webm;codecs=opus' });
                
                // Convert to array buffer for processing
                const arrayBuffer = await combinedBlob.arrayBuffer();
                
                // Send for recognition
                const result = await multiProviderService.transcribeAudio(arrayBuffer, 'webm');
                
                if (result.success && result.transcript.trim()) {
                    const isFinal = timeSinceSpeech > this.silenceDuration;
                    
                    if (isFinal) {
                        console.log('✅ Final result:', result.transcript);
                        if (this.onFinalResult) {
                            this.onFinalResult(result.transcript, result.confidence || 0.8);
                        }
                        
                        // Reset for next utterance
                        this.audioChunks = [];
                        this.speechDetected = false;
                    } else {
                        console.log('⏳ Interim result:', result.transcript);
                        if (this.onInterimResult) {
                            this.onInterimResult(result.transcript, result.confidence || 0.8);
                        }
                    }
                } else if (result.success && isFinal) {
                    // Silent period ended but no speech recognized
                    this.audioChunks = [];
                    this.speechDetected = false;
                }
                
                // Keep only recent chunks for next processing
                if (!isFinal && this.audioChunks.length > 5) {
                    this.audioChunks = this.audioChunks.slice(-3);
                }
            }

        } catch (error) {
            console.error('Error processing audio chunk:', error);
            if (this.onError) {
                this.onError(`Processing error: ${error.message}`);
            }
        }
    }

    async _processAccumulatedAudio() {
        if (this.audioChunks.length === 0) return;

        try {
            const combinedBlob = new Blob(this.audioChunks, { type: 'audio/webm;codecs=opus' });
            console.log('🔄 Processing final accumulated audio chunks...');
            
            // This would be processed by the multi-provider service
            // For now, just log that we have final audio to process
            console.log('📦 Final audio chunk ready for processing:', combinedBlob.size, 'bytes');
            
        } catch (error) {
            console.error('Error processing accumulated audio:', error);
        }
    }

    _startVolumeMonitoring() {
        if (!this.analyser) return;

        const updateVolume = () => {
            if (!this.isStreaming) return;

            this.analyser.getByteFrequencyData(this.volumeData);
            
            // Calculate average volume
            let sum = 0;
            for (let i = 0; i < this.volumeData.length; i++) {
                sum += this.volumeData[i];
            }
            const averageVolume = sum / this.volumeData.length / 255; // Normalize to 0-1

            if (this.onVolumeLevel) {
                this.onVolumeLevel(averageVolume);
            }

            // Continue monitoring
            requestAnimationFrame(updateVolume);
        };

        updateVolume();
    }

    _stopVolumeMonitoring() {
        // Volume monitoring stops automatically when isStreaming becomes false
    }

    _getCurrentVolumeLevel() {
        if (!this.analyser || !this.volumeData) return 0;

        this.analyser.getByteFrequencyData(this.volumeData);
        
        let sum = 0;
        for (let i = 0; i < this.volumeData.length; i++) {
            sum += this.volumeData[i];
        }
        
        return sum / this.volumeData.length / 255;
    }

    // Configuration methods
    setConfiguration(config) {
        this.config = { ...this.config, ...config };
    }

    setSpeechDetectionThreshold(threshold) {
        this.speechDetectionThreshold = Math.max(0, Math.min(1, threshold));
    }

    setSilenceDuration(duration) {
        this.silenceDuration = Math.max(500, duration); // Minimum 500ms
    }

    // Event handlers
    onStreamingInterimResult(callback) {
        this.onInterimResult = callback;
    }

    onStreamingFinalResult(callback) {
        this.onFinalResult = callback;
    }

    onStreamingError(callback) {
        this.onError = callback;
    }

    onStreamingStarted(callback) {
        this.onStreamingStart = callback;
    }

    onStreamingEnded(callback) {
        this.onStreamingEnd = callback;
    }

    onVolumeLevelUpdate(callback) {
        this.onVolumeLevel = callback;
    }

    // Status and cleanup
    getStatus() {
        return {
            isStreaming: this.isStreaming,
            hasAudioStream: !!this.audioStream,
            hasAudioContext: !!this.audioContext,
            chunksInBuffer: this.audioChunks.length,
            speechDetected: this.speechDetected,
            timeSinceLastSpeech: this.lastSpeechTime > 0 ? Date.now() - this.lastSpeechTime : null
        };
    }

    destroy() {
        this.stopStreaming();

        // Close audio stream
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }

        // Close audio context
        if (this.audioContext && this.audioContext.state !== 'closed') {
            this.audioContext.close();
            this.audioContext = null;
        }

        // Clear data
        this.audioChunks = [];
        this.volumeData = null;

        console.log('🧹 Streaming recognition service destroyed');
    }
}

/**
 * Streaming Practice Session Manager
 * Manages streaming recognition integrated with phrase-based practice
 */
class StreamingPracticeSession {
    constructor(practiceEngine, streamingService, multiProviderService) {
        this.practiceEngine = practiceEngine;
        this.streamingService = streamingService;
        this.multiProviderService = multiProviderService;
        
        this.isActive = false;
        this.currentPhrase = null;
        this.interimTranscript = '';
        
        // Setup event handlers
        this._setupEventHandlers();
    }

    _setupEventHandlers() {
        this.streamingService.onStreamingInterimResult((transcript, confidence) => {
            this.interimTranscript = transcript;
            this._handleInterimResult(transcript, confidence);
        });

        this.streamingService.onStreamingFinalResult((transcript, confidence) => {
            this._handleFinalResult(transcript, confidence);
        });

        this.streamingService.onStreamingError((error) => {
            console.error('Streaming error in practice session:', error);
        });

        this.streamingService.onVolumeLevelUpdate((level) => {
            this._handleVolumeLevel(level);
        });
    }

    async startSession(text, options = {}) {
        try {
            // Initialize practice engine
            this.practiceEngine.initializeSession(text, options);
            
            // Get first phrase
            this.currentPhrase = this.practiceEngine.getPracticePhrase();
            
            // Start streaming recognition
            const started = await this.streamingService.startStreaming(this.multiProviderService);
            
            if (started) {
                this.isActive = true;
                console.log('🚀 Streaming practice session started');
                console.log('📝 First phrase:', this.currentPhrase.phraseText);
                return {
                    success: true,
                    currentPhrase: this.currentPhrase
                };
            } else {
                return {
                    success: false,
                    error: 'Failed to start streaming recognition'
                };
            }
            
        } catch (error) {
            console.error('Error starting streaming practice session:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    stopSession() {
        this.isActive = false;
        this.streamingService.stopStreaming();
        
        const summary = this.practiceEngine.getSessionSummary();
        console.log('🏁 Streaming practice session ended');
        
        return summary;
    }

    _handleInterimResult(transcript, confidence) {
        if (!this.isActive || !this.currentPhrase) return;

        // Show live feedback during speech
        console.log(`⏳ Speaking: "${transcript}" (${(confidence * 100).toFixed(0)}%)`);
        
        // Could trigger live visual feedback here
    }

    async _handleFinalResult(transcript, confidence) {
        if (!this.isActive || !this.currentPhrase) return;

        console.log(`✅ Processing phrase: "${transcript}"`);

        try {
            // Process the spoken phrase
            const result = await this.practiceEngine.processPhraseeSpeech(
                transcript,
                this.currentPhrase.phraseText,
                `Streaming practice, phrase ${this.practiceEngine.currentSession.phrasesCompleted + 1}`
            );

            if (result.success) {
                console.log(`📊 Phrase accuracy: ${result.accuracy.toFixed(1)}%`);
                
                // Handle advancement
                if (result.phraseCorrect) {
                    console.log('✨ Advancing to next phrase...');
                    
                    // Add missed words to review bank
                    if (result.missedWords && result.missedWords.length > 0) {
                        this.practiceEngine.addMissedWords(result.missedWords, this.currentPhrase.phraseText);
                    }
                    
                    // Get next phrase
                    this.currentPhrase = this.practiceEngine.advanceToNextPhrase();
                    
                    if (this.currentPhrase) {
                        console.log('📝 Next phrase:', this.currentPhrase.phraseText);
                    } else {
                        console.log('🎉 Practice session complete!');
                        this.stopSession();
                    }
                } else {
                    console.log('🔄 Try the same phrase again');
                    console.log('💡', result.progressMessage);
                }

                return result;
            }

        } catch (error) {
            console.error('Error processing phrase in streaming session:', error);
        }
    }

    _handleVolumeLevel(level) {
        // Could trigger visual volume indicators
        if (level > 0.1) {
            // User is speaking
        }
    }

    getCurrentStatus() {
        return {
            isActive: this.isActive,
            currentPhrase: this.currentPhrase,
            interimTranscript: this.interimTranscript,
            streamingStatus: this.streamingService.getStatus(),
            sessionInfo: this.practiceEngine._getSessionInfo()
        };
    }
}

export { StreamingRecognitionService, StreamingPracticeSession };