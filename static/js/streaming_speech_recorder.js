/**
 * Enhanced Real-time Streaming Speech Recorder for Speech Memorization
 * Processes audio in chunks with WebRTC VAD and adaptive processing
 */

class StreamingSpeechRecorder {
    constructor(options = {}) {
        this.options = {
            chunkDuration: 3000,      // 3 second chunks for natural speech
            sampleRate: 16000,
            channels: 1,
            bitsPerSample: 16,
            overlaps: 500,            // 500ms overlap between chunks
            minChunkSize: 1500,       // minimum 1.5s before processing
            maxSilence: 5000,         // stop after 5s of silence
            volumeThreshold: 0.005,   // lower silence threshold
            vadThreshold: 0.3,        // less aggressive voice activity detection
            adaptiveProcessing: false, // disable for better consistency
            confidenceThreshold: 0.4, // lower confidence threshold
            naturalSpeechMode: true,  // enable natural speech optimizations
            ...options
        };
        
        this.isStreaming = false;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.processor = null;
        this.source = null;
        this.vadProcessor = null;
        
        // Chunking system
        this.currentChunk = [];
        this.chunkTimer = null;
        this.silenceTimer = null;
        this.lastProcessTime = 0;
        this.chunkSequence = 0;
        
        // Audio buffer for overlap processing
        this.audioBuffer = [];
        this.bufferSize = Math.floor(this.options.sampleRate * (this.options.overlaps / 1000));
        
        // Voice Activity Detection
        this.vadBuffer = [];
        this.vadWindowSize = Math.floor(this.options.sampleRate * 0.03); // 30ms window
        this.speechProbability = 0;
        this.consecutiveSpeechFrames = 0;
        this.consecutiveSilenceFrames = 0;
        
        // Adaptive processing state
        this.recentConfidences = [];
        this.averageConfidence = 0;
        this.processingRate = 1.0; // 1.0 = process every chunk
        
        // Event callbacks
        this.onChunkReady = options.onChunkReady || (() => {});
        this.onStreamStart = options.onStreamStart || (() => {});
        this.onStreamStop = options.onStreamStop || (() => {});
        this.onVolumeChange = options.onVolumeChange || (() => {});
        this.onError = options.onError || console.error;
        this.onSilenceDetected = options.onSilenceDetected || (() => {});
        this.onSpeechDetected = options.onSpeechDetected || (() => {});
        
        this.setupAudioContext();
        this.initializeVAD();
        this.initializeCapabilityManagement();
    }
    
    initializeCapabilityManagement() {
        // Initialize device capability manager if available
        if (typeof DeviceCapabilityManager !== 'undefined') {
            this.capabilityManager = new DeviceCapabilityManager();
            
            // Apply optimal configuration
            const optimalConfig = this.capabilityManager.getOptimalConfiguration();
            
            // Override options with device-optimized settings
            Object.assign(this.options, optimalConfig.recommendedSettings);
            
            console.log('Applied device-optimized settings:', optimalConfig.recommendedSettings);
            console.log('Performance profile:', optimalConfig.performanceProfile);
            
            // Initialize audio processor if supported
            if (typeof AudioProcessor !== 'undefined' && 
                this.capabilityManager.shouldUseFeature('audioEnhancement')) {
                this.audioProcessor = new AudioProcessor();
                console.log('Audio enhancement enabled');
            }
        } else {
            console.log('Using default configuration - DeviceCapabilityManager not available');
        }
    }
    
    async setupAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: this.options.sampleRate
            });
            
            // Create analyser for volume detection
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.3;
            
        } catch (error) {
            console.warn('AudioContext setup failed:', error);
            this.onError('AudioContext not available: ' + error.message);
        }
    }
    
    initializeVAD() {
        // Initialize Voice Activity Detection
        try {
            // Check for WebRTC VAD support
            if (typeof webrtcvad !== 'undefined') {
                this.vadProcessor = new webrtcvad.VAD();
                console.log('WebRTC VAD initialized');
            } else {
                console.log('Using fallback VAD implementation');
            }
        } catch (error) {
            console.warn('VAD initialization failed, using energy-based detection:', error);
        }
    }
    
    detectVoiceActivity(audioData) {
        // Enhanced voice activity detection
        if (!audioData || audioData.length === 0) return false;
        
        // Calculate energy-based features
        const energy = this.calculateEnergy(audioData);
        const zeroCrossingRate = this.calculateZeroCrossingRate(audioData);
        const spectralCentroid = this.calculateSpectralCentroid(audioData);
        
        // Combine features for voice activity decision
        const energyThreshold = 0.01;
        const zcrThreshold = 0.1;
        
        const hasEnergy = energy > energyThreshold;
        const hasVariation = zeroCrossingRate > zcrThreshold && zeroCrossingRate < 0.8;
        const hasSpectralContent = spectralCentroid > 500; // Hz
        
        // Voice activity if at least 1 of 3 conditions are met (less aggressive)
        const voiceActivity = [hasEnergy, hasVariation, hasSpectralContent].filter(Boolean).length >= 1;
        
        // Update speech probability with more smoothing for natural speech
        this.speechProbability = this.speechProbability * 0.9 + (voiceActivity ? 1.0 : 0.0) * 0.1;
        
        // Track consecutive frames
        if (voiceActivity) {
            this.consecutiveSpeechFrames++;
            this.consecutiveSilenceFrames = 0;
        } else {
            this.consecutiveSilenceFrames++;
            this.consecutiveSpeechFrames = 0;
        }
        
        return this.speechProbability > this.options.vadThreshold;
    }
    
    calculateEnergy(audioData) {
        let sum = 0;
        for (let i = 0; i < audioData.length; i++) {
            sum += audioData[i] * audioData[i];
        }
        return Math.sqrt(sum / audioData.length);
    }
    
    calculateZeroCrossingRate(audioData) {
        let crossings = 0;
        for (let i = 1; i < audioData.length; i++) {
            if ((audioData[i] >= 0) !== (audioData[i - 1] >= 0)) {
                crossings++;
            }
        }
        return crossings / (audioData.length - 1);
    }
    
    calculateSpectralCentroid(audioData) {
        // Simplified spectral centroid calculation
        const fftSize = Math.min(audioData.length, 512);
        const fft = this.simpleFFT(audioData.slice(0, fftSize));
        
        let weightedSum = 0;
        let magnitudeSum = 0;
        
        for (let i = 0; i < fft.length / 2; i++) {
            const magnitude = Math.sqrt(fft[i * 2] ** 2 + fft[i * 2 + 1] ** 2);
            const frequency = i * this.options.sampleRate / fftSize;
            
            weightedSum += frequency * magnitude;
            magnitudeSum += magnitude;
        }
        
        return magnitudeSum > 0 ? weightedSum / magnitudeSum : 0;
    }
    
    simpleFFT(audioData) {
        // Simple DFT implementation for spectral analysis
        const N = audioData.length;
        const result = new Array(N * 2).fill(0);
        
        for (let k = 0; k < N; k++) {
            let real = 0, imag = 0;
            for (let n = 0; n < N; n++) {
                const angle = -2 * Math.PI * k * n / N;
                real += audioData[n] * Math.cos(angle);
                imag += audioData[n] * Math.sin(angle);
            }
            result[k * 2] = real;
            result[k * 2 + 1] = imag;
        }
        
        return result;
    }
    
    updateAdaptiveProcessing(confidence) {
        // Update confidence history
        this.recentConfidences.push(confidence);
        if (this.recentConfidences.length > 10) {
            this.recentConfidences.shift();
        }
        
        // Calculate average confidence
        this.averageConfidence = this.recentConfidences.reduce((a, b) => a + b, 0) / this.recentConfidences.length;
        
        // Adjust processing rate based on performance
        if (this.averageConfidence > 0.8) {
            this.processingRate = Math.max(0.5, this.processingRate - 0.1); // Process less frequently
        } else if (this.averageConfidence < 0.4) {
            this.processingRate = Math.min(1.0, this.processingRate + 0.1); // Process more frequently
        }
        
        console.log(`Adaptive processing: rate=${this.processingRate.toFixed(2)}, avgConf=${this.averageConfidence.toFixed(2)}`);
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
            
            this.audioStream = stream;
            return true;
        } catch (error) {
            console.error('Microphone permission denied:', error);
            this.onError('Microphone access denied: ' + error.message);
            return false;
        }
    }
    
    async startStreaming() {
        if (this.isStreaming) {
            console.warn('Already streaming');
            return;
        }
        
        if (!this.audioStream) {
            const hasPermission = await this.requestMicrophonePermission();
            if (!hasPermission) return false;
        }
        
        try {
            // Resume audio context if suspended
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }
            
            this.isStreaming = true;
            this.chunkSequence = 0;
            this.currentChunk = [];
            this.audioBuffer = [];
            this.lastProcessTime = Date.now();
            
            // Setup audio processing pipeline
            this.source = this.audioContext.createMediaStreamSource(this.audioStream);
            this.source.connect(this.analyser);
            
            // Create script processor for real-time audio processing
            this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
            this.processor.onaudioprocess = this.processAudioChunk.bind(this);
            
            this.analyser.connect(this.processor);
            this.processor.connect(this.audioContext.destination);
            
            // Start chunk timer
            this.startChunkTimer();
            
            // Start volume monitoring
            this.startVolumeMonitoring();
            
            console.log('Streaming started');
            this.onStreamStart();
            
            return true;
            
        } catch (error) {
            console.error('Failed to start streaming:', error);
            this.onError('Failed to start streaming: ' + error.message);
            this.isStreaming = false;
            return false;
        }
    }
    
    processAudioChunk(event) {
        if (!this.isStreaming) return;
        
        const inputData = event.inputBuffer.getChannelData(0);
        
        // Voice Activity Detection
        const hasVoiceActivity = this.detectVoiceActivity(inputData);
        
        // Always capture audio in natural speech mode, use VAD for guidance only
        if (this.options.naturalSpeechMode || hasVoiceActivity) {
            // Convert float32 to int16 and add to current chunk
            for (let i = 0; i < inputData.length; i++) {
                const sample = Math.max(-1, Math.min(1, inputData[i]));
                this.currentChunk.push(Math.floor(sample * 32767));
            }
            
            // Trigger speech detected event
            if (this.consecutiveSpeechFrames === 5) { // More frames for natural speech
                this.onSpeechDetected();
            }
        }
        
        // Handle silence detection (more lenient)
        if (this.consecutiveSilenceFrames > 100) { // About 2 seconds of silence
            if (this.silenceTimer === null) {
                this.onSilenceDetected();
            }
        }
        
        // Add to rolling buffer for overlap processing (regardless of VAD)
        this.audioBuffer.push(...inputData);
        if (this.audioBuffer.length > this.bufferSize * 2) {
            this.audioBuffer = this.audioBuffer.slice(-this.bufferSize);
        }
    }
    
    startChunkTimer() {
        this.chunkTimer = setInterval(() => {
            if (this.currentChunk.length > 0) {
                this.processCurrentChunk();
            }
        }, this.options.chunkDuration);
    }
    
    processCurrentChunk() {
        const now = Date.now();
        const chunkDuration = now - this.lastProcessTime;
        
        // Only process if we have minimum chunk size
        if (this.currentChunk.length < this.options.minChunkSize * (this.options.sampleRate / 1000)) {
            return;
        }
        
        // Skip adaptive processing in natural speech mode for consistency
        if (this.options.adaptiveProcessing && !this.options.naturalSpeechMode && Math.random() > this.processingRate) {
            console.log(`Skipping chunk due to adaptive processing (rate: ${this.processingRate.toFixed(2)})`);
            this.currentChunk = [];
            this.lastProcessTime = now;
            return;
        }
        
        // Add overlap from previous chunk
        let chunkData = [...this.currentChunk];
        if (this.audioBuffer.length > 0) {
            const overlapSamples = Math.min(this.audioBuffer.length, this.bufferSize);
            const overlapData = this.audioBuffer.slice(-overlapSamples).map(sample => 
                Math.floor(Math.max(-1, Math.min(1, sample)) * 32767)
            );
            chunkData = [...overlapData, ...chunkData];
        }
        
        // Apply audio enhancement if available
        if (this.audioProcessor) {
            try {
                const floatData = chunkData.map(sample => sample / 32767);
                const enhancedData = this.audioProcessor.processAudioBuffer(floatData);
                chunkData = enhancedData.map(sample => Math.floor(sample * 32767));
                console.log('Audio enhancement applied');
            } catch (error) {
                console.warn('Audio enhancement failed, using original audio:', error);
            }
        }
        
        // Convert to base64
        const audioBlob = this.createAudioBlob(chunkData);
        this.convertBlobToBase64(audioBlob).then(base64Data => {
            const chunkInfo = {
                sequence: this.chunkSequence++,
                base64Data: base64Data,
                format: 'wav',
                duration: chunkDuration,
                sampleRate: this.options.sampleRate,
                channels: this.options.channels,
                timestamp: now,
                isRealtime: true,
                hasOverlap: this.audioBuffer.length > 0,
                speechProbability: this.speechProbability,
                processingRate: this.processingRate,
                averageConfidence: this.averageConfidence
            };
            
            console.log(`Processing chunk ${chunkInfo.sequence}: ${chunkData.length} samples, ${chunkDuration}ms, speech: ${this.speechProbability.toFixed(2)}`);
            this.onChunkReady(chunkInfo);
        }).catch(error => {
            console.error('Error processing chunk:', error);
            this.onError('Chunk processing error: ' + error.message);
        });
        
        // Reset for next chunk
        this.currentChunk = [];
        this.lastProcessTime = now;
    }
    
    createAudioBlob(audioData) {
        const buffer = new ArrayBuffer(44 + audioData.length * 2);
        const view = new DataView(buffer);
        
        // WAV header
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + audioData.length * 2, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, this.options.channels, true);
        view.setUint32(24, this.options.sampleRate, true);
        view.setUint32(28, this.options.sampleRate * this.options.channels * 2, true);
        view.setUint16(32, this.options.channels * 2, true);
        view.setUint16(34, 16, true);
        writeString(36, 'data');
        view.setUint32(40, audioData.length * 2, true);
        
        // Audio data
        for (let i = 0; i < audioData.length; i++) {
            view.setInt16(44 + i * 2, audioData[i], true);
        }
        
        return new Blob([buffer], { type: 'audio/wav' });
    }
    
    convertBlobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    startVolumeMonitoring() {
        const monitorVolume = () => {
            if (!this.isStreaming || !this.analyser) return;
            
            const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
            this.analyser.getByteFrequencyData(dataArray);
            
            // Calculate RMS volume
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i] * dataArray[i];
            }
            const rms = Math.sqrt(sum / dataArray.length) / 255;
            
            this.onVolumeChange(rms);
            
            // Check for silence
            if (rms < this.options.volumeThreshold) {
                if (!this.silenceTimer) {
                    this.silenceTimer = setTimeout(() => {
                        console.log('Silence detected');
                        this.onSilenceDetected();
                    }, this.options.maxSilence);
                }
            } else {
                if (this.silenceTimer) {
                    clearTimeout(this.silenceTimer);
                    this.silenceTimer = null;
                }
            }
            
            if (this.isStreaming) {
                requestAnimationFrame(monitorVolume);
            }
        };
        
        requestAnimationFrame(monitorVolume);
    }
    
    stopStreaming() {
        if (!this.isStreaming) return;
        
        console.log('Stopping streaming...');
        this.isStreaming = false;
        
        // Clear timers
        if (this.chunkTimer) {
            clearInterval(this.chunkTimer);
            this.chunkTimer = null;
        }
        
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }
        
        // Process final chunk if any
        if (this.currentChunk.length > 0) {
            this.processCurrentChunk();
        }
        
        // Cleanup audio processing
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }
        
        if (this.source) {
            this.source.disconnect();
            this.source = null;
        }
        
        // Stop media stream
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
        
        console.log('Streaming stopped');
        this.onStreamStop();
    }
    
    pauseStreaming() {
        if (this.isStreaming) {
            this.isStreaming = false;
            console.log('Streaming paused');
        }
    }
    
    resumeStreaming() {
        if (!this.isStreaming && this.processor) {
            this.isStreaming = true;
            this.lastProcessTime = Date.now();
            console.log('Streaming resumed');
        }
    }
    
    getStreamingStatus() {
        return {
            isStreaming: this.isStreaming,
            chunkSequence: this.chunkSequence,
            bufferSize: this.audioBuffer.length,
            currentChunkSize: this.currentChunk.length
        };
    }
}

// Export for use in other scripts
window.StreamingSpeechRecorder = StreamingSpeechRecorder;