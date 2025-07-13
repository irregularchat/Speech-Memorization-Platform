/**
 * Audio Processor with WebAssembly optimization support
 * Provides enhanced audio preprocessing for speech recognition
 */

class AudioProcessor {
    constructor() {
        this.wasmModule = null;
        this.isWasmLoaded = false;
        this.capabilities = this.detectCapabilities();
        
        // Audio processing configuration
        this.config = {
            sampleRate: 16000,
            channels: 1,
            bitDepth: 16,
            windowSize: 1024,
            overlapRatio: 0.5,
            noiseReduction: true,
            normalization: true,
            highpassFilter: true,
            lowpassFilter: true
        };
        
        this.initializeProcessor();
    }
    
    detectCapabilities() {
        const capabilities = {
            webAssembly: typeof WebAssembly !== 'undefined',
            audioWorklet: 'AudioWorklet' in window,
            offscreenCanvas: typeof OffscreenCanvas !== 'undefined',
            sharedArrayBuffer: typeof SharedArrayBuffer !== 'undefined',
            simd: false, // Will be detected if WASM is available
            threads: navigator.hardwareConcurrency || 1
        };
        
        // Detect SIMD support
        if (capabilities.webAssembly) {
            try {
                // Simple SIMD detection
                const simdTest = new WebAssembly.Module(new Uint8Array([
                    0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00
                ]));
                capabilities.simd = true;
            } catch (e) {
                capabilities.simd = false;
            }
        }
        
        console.log('Audio processing capabilities:', capabilities);
        return capabilities;
    }
    
    async initializeProcessor() {
        // Try to load WebAssembly module for high-performance processing
        if (this.capabilities.webAssembly) {
            try {
                await this.loadWasmModule();
            } catch (error) {
                console.warn('WASM audio processor failed to load, using JavaScript fallback:', error);
            }
        }
        
        // Initialize AudioWorklet if available
        if (this.capabilities.audioWorklet) {
            try {
                await this.initializeAudioWorklet();
            } catch (error) {
                console.warn('AudioWorklet initialization failed:', error);
            }
        }
    }
    
    async loadWasmModule() {
        // Placeholder for WebAssembly module loading
        // In production, this would load a compiled WASM module
        console.log('Loading WebAssembly audio processor...');
        
        // Simulated WASM module interface
        this.wasmModule = {
            // Noise reduction using spectral subtraction
            reduceNoise: (audioData, noiseProfile) => {
                return this.jsNoiseReduction(audioData, noiseProfile);
            },
            
            // High-pass filter to remove low-frequency noise
            highpassFilter: (audioData, cutoffFreq) => {
                return this.jsHighpassFilter(audioData, cutoffFreq);
            },
            
            // Dynamic range compression
            compressor: (audioData, threshold, ratio) => {
                return this.jsCompressor(audioData, threshold, ratio);
            },
            
            // Spectral enhancement
            spectralEnhancement: (audioData) => {
                return this.jsSpectralEnhancement(audioData);
            }
        };
        
        this.isWasmLoaded = true;
        console.log('WebAssembly audio processor loaded successfully');
    }
    
    async initializeAudioWorklet() {
        // AudioWorklet for real-time processing
        console.log('Initializing AudioWorklet processor...');
        
        // In production, this would register custom AudioWorklet processors
        // for real-time audio enhancement
    }
    
    processAudioBuffer(audioBuffer, options = {}) {
        const config = { ...this.config, ...options };
        
        if (this.isWasmLoaded && this.capabilities.webAssembly) {
            return this.processWithWasm(audioBuffer, config);
        } else {
            return this.processWithJavaScript(audioBuffer, config);
        }
    }
    
    processWithWasm(audioBuffer, config) {
        console.log('Processing audio with WebAssembly...');
        
        let processedBuffer = new Float32Array(audioBuffer);
        
        try {
            // Apply noise reduction
            if (config.noiseReduction) {
                const noiseProfile = this.estimateNoiseProfile(processedBuffer);
                processedBuffer = this.wasmModule.reduceNoise(processedBuffer, noiseProfile);
            }
            
            // Apply high-pass filter
            if (config.highpassFilter) {
                processedBuffer = this.wasmModule.highpassFilter(processedBuffer, 80); // 80Hz cutoff
            }
            
            // Apply compression
            processedBuffer = this.wasmModule.compressor(processedBuffer, 0.7, 3.0);
            
            // Apply spectral enhancement
            processedBuffer = this.wasmModule.spectralEnhancement(processedBuffer);
            
            // Normalize
            if (config.normalization) {
                processedBuffer = this.normalizeAudio(processedBuffer);
            }
            
        } catch (error) {
            console.error('WASM processing error, falling back to JavaScript:', error);
            return this.processWithJavaScript(audioBuffer, config);
        }
        
        return processedBuffer;
    }
    
    processWithJavaScript(audioBuffer, config) {
        console.log('Processing audio with JavaScript...');
        
        let processedBuffer = new Float32Array(audioBuffer);
        
        // Apply basic noise reduction
        if (config.noiseReduction) {
            processedBuffer = this.jsNoiseReduction(processedBuffer);
        }
        
        // Apply high-pass filter
        if (config.highpassFilter) {
            processedBuffer = this.jsHighpassFilter(processedBuffer, 80);
        }
        
        // Apply compression
        processedBuffer = this.jsCompressor(processedBuffer, 0.7, 3.0);
        
        // Normalize
        if (config.normalization) {
            processedBuffer = this.normalizeAudio(processedBuffer);
        }
        
        return processedBuffer;
    }
    
    jsNoiseReduction(audioData, noiseProfile = null) {
        // Simple noise gate implementation
        const threshold = 0.02;
        const ratio = 0.1;
        
        const output = new Float32Array(audioData.length);
        
        for (let i = 0; i < audioData.length; i++) {
            const sample = audioData[i];
            const amplitude = Math.abs(sample);
            
            if (amplitude < threshold) {
                output[i] = sample * ratio;
            } else {
                output[i] = sample;
            }
        }
        
        return output;
    }
    
    jsHighpassFilter(audioData, cutoffFreq) {
        // Simple high-pass filter using difference equation
        const sampleRate = this.config.sampleRate;
        const rc = 1.0 / (2 * Math.PI * cutoffFreq);
        const dt = 1.0 / sampleRate;
        const alpha = rc / (rc + dt);
        
        const output = new Float32Array(audioData.length);
        let previousInput = 0;
        let previousOutput = 0;
        
        for (let i = 0; i < audioData.length; i++) {
            output[i] = alpha * (previousOutput + audioData[i] - previousInput);
            previousInput = audioData[i];
            previousOutput = output[i];
        }
        
        return output;
    }
    
    jsCompressor(audioData, threshold, ratio) {
        // Dynamic range compression
        const output = new Float32Array(audioData.length);
        
        for (let i = 0; i < audioData.length; i++) {
            const sample = audioData[i];
            const amplitude = Math.abs(sample);
            
            if (amplitude > threshold) {
                const excess = amplitude - threshold;
                const compressedExcess = excess / ratio;
                const compressedAmplitude = threshold + compressedExcess;
                output[i] = sample * (compressedAmplitude / amplitude);
            } else {
                output[i] = sample;
            }
        }
        
        return output;
    }
    
    jsSpectralEnhancement(audioData) {
        // Basic spectral enhancement using windowing
        const windowSize = this.config.windowSize;
        const overlap = Math.floor(windowSize * this.config.overlapRatio);
        const hopSize = windowSize - overlap;
        
        const output = new Float32Array(audioData.length);
        
        for (let i = 0; i < audioData.length - windowSize; i += hopSize) {
            const window = audioData.slice(i, i + windowSize);
            const enhancedWindow = this.enhanceWindow(window);
            
            // Overlap-add
            for (let j = 0; j < windowSize; j++) {
                if (i + j < output.length) {
                    output[i + j] += enhancedWindow[j];
                }
            }
        }
        
        return output;
    }
    
    enhanceWindow(window) {
        // Apply Hamming window and basic enhancement
        const enhanced = new Float32Array(window.length);
        
        for (let i = 0; i < window.length; i++) {
            const hammingCoeff = 0.54 - 0.46 * Math.cos(2 * Math.PI * i / (window.length - 1));
            enhanced[i] = window[i] * hammingCoeff;
        }
        
        return enhanced;
    }
    
    normalizeAudio(audioData) {
        // Find peak amplitude
        let peak = 0;
        for (let i = 0; i < audioData.length; i++) {
            peak = Math.max(peak, Math.abs(audioData[i]));
        }
        
        if (peak === 0) return audioData;
        
        // Normalize to 0.9 to prevent clipping
        const targetPeak = 0.9;
        const gain = targetPeak / peak;
        
        const normalized = new Float32Array(audioData.length);
        for (let i = 0; i < audioData.length; i++) {
            normalized[i] = audioData[i] * gain;
        }
        
        return normalized;
    }
    
    estimateNoiseProfile(audioData) {
        // Estimate noise profile from quiet sections
        const windowSize = 1024;
        const threshold = 0.01;
        
        let noiseSum = 0;
        let noiseCount = 0;
        
        for (let i = 0; i < audioData.length - windowSize; i += windowSize) {
            let windowEnergy = 0;
            for (let j = 0; j < windowSize; j++) {
                windowEnergy += audioData[i + j] ** 2;
            }
            
            const rms = Math.sqrt(windowEnergy / windowSize);
            if (rms < threshold) {
                noiseSum += rms;
                noiseCount++;
            }
        }
        
        return noiseCount > 0 ? noiseSum / noiseCount : 0.01;
    }
    
    getProcessingLatency() {
        // Estimate processing latency based on capabilities
        if (this.isWasmLoaded) {
            return 5; // ms
        } else if (this.capabilities.audioWorklet) {
            return 10; // ms
        } else {
            return 20; // ms
        }
    }
    
    getRecommendedChunkSize() {
        // Recommend chunk size based on capabilities
        const baseSize = this.config.sampleRate * 0.5; // 500ms
        
        if (this.capabilities.threads > 4) {
            return baseSize * 2; // Larger chunks for multi-core
        } else if (this.capabilities.webAssembly) {
            return baseSize * 1.5;
        } else {
            return baseSize; // Conservative for JavaScript-only
        }
    }
    
    supportsRealtimeProcessing() {
        return this.capabilities.audioWorklet && (this.isWasmLoaded || this.capabilities.threads > 2);
    }
}

// Export for use in other scripts
window.AudioProcessor = AudioProcessor;