/**
 * Real-time Streaming Speech Recorder for Speech Memorization
 * Processes audio in chunks for immediate speech recognition
 */

class StreamingSpeechRecorder {
    constructor(options = {}) {
        this.options = {
            chunkDuration: 1000,      // 1 second chunks
            sampleRate: 16000,
            channels: 1,
            bitsPerSample: 16,
            overlaps: 200,            // 200ms overlap between chunks
            minChunkSize: 500,        // minimum 0.5s before processing
            maxSilence: 3000,         // stop after 3s of silence
            volumeThreshold: 0.01,    // silence threshold
            ...options
        };
        
        this.isStreaming = false;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.processor = null;
        this.source = null;
        
        // Chunking system
        this.currentChunk = [];
        this.chunkTimer = null;
        this.silenceTimer = null;
        this.lastProcessTime = 0;
        this.chunkSequence = 0;
        
        // Audio buffer for overlap processing
        this.audioBuffer = [];
        this.bufferSize = Math.floor(this.options.sampleRate * (this.options.overlaps / 1000));
        
        // Event callbacks
        this.onChunkReady = options.onChunkReady || (() => {});
        this.onStreamStart = options.onStreamStart || (() => {});
        this.onStreamStop = options.onStreamStop || (() => {});
        this.onVolumeChange = options.onVolumeChange || (() => {});
        this.onError = options.onError || console.error;
        this.onSilenceDetected = options.onSilenceDetected || (() => {});
        
        this.setupAudioContext();
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
        
        // Convert float32 to int16 and add to current chunk
        for (let i = 0; i < inputData.length; i++) {
            const sample = Math.max(-1, Math.min(1, inputData[i]));
            this.currentChunk.push(Math.floor(sample * 32767));
        }
        
        // Add to rolling buffer for overlap processing
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
        
        // Add overlap from previous chunk
        let chunkData = [...this.currentChunk];
        if (this.audioBuffer.length > 0) {
            const overlapSamples = Math.min(this.audioBuffer.length, this.bufferSize);
            const overlapData = this.audioBuffer.slice(-overlapSamples).map(sample => 
                Math.floor(Math.max(-1, Math.min(1, sample)) * 32767)
            );
            chunkData = [...overlapData, ...chunkData];
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
                hasOverlap: this.audioBuffer.length > 0
            };
            
            console.log(`Processing chunk ${chunkInfo.sequence}: ${chunkData.length} samples, ${chunkDuration}ms`);
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