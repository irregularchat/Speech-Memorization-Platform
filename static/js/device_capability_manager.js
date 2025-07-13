/**
 * Device Capability Manager
 * Detects device capabilities and optimizes speech processing accordingly
 */

class DeviceCapabilityManager {
    constructor() {
        this.capabilities = {};
        this.performanceProfile = 'unknown';
        this.recommendedSettings = {};
        
        this.detectCapabilities();
        this.benchmarkPerformance();
    }
    
    detectCapabilities() {
        this.capabilities = {
            // Browser and API capabilities
            webAudio: this.detectWebAudio(),
            mediaRecorder: this.detectMediaRecorder(),
            audioWorklet: this.detectAudioWorklet(),
            webAssembly: this.detectWebAssembly(),
            sharedArrayBuffer: this.detectSharedArrayBuffer(),
            offscreenCanvas: this.detectOffscreenCanvas(),
            
            // Device capabilities
            deviceMemory: this.detectDeviceMemory(),
            hardwareConcurrency: this.detectHardwareConcurrency(),
            connectionType: this.detectConnectionType(),
            batteryStatus: this.detectBatteryStatus(),
            
            // Performance indicators
            performanceObserver: this.detectPerformanceObserver(),
            requestIdleCallback: this.detectRequestIdleCallback(),
            
            // Mobile/touch capabilities
            isMobile: this.detectMobile(),
            isTablet: this.detectTablet(),
            hasTouch: this.detectTouch(),
            
            // Audio capabilities
            audioFormats: this.detectAudioFormats(),
            microphoneAccess: false, // Will be set when permission is granted
            audioContextLatency: 0,   // Will be measured
            
            // Network capabilities
            isOnline: navigator.onLine,
            effectiveType: this.getEffectiveConnectionType(),
            downlink: this.getDownlink(),
            rtt: this.getRTT()
        };
        
        console.log('Device capabilities detected:', this.capabilities);
        this.determinePerformanceProfile();
    }
    
    detectWebAudio() {
        return !!(window.AudioContext || window.webkitAudioContext);
    }
    
    detectMediaRecorder() {
        return typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported;
    }
    
    detectAudioWorklet() {
        return typeof AudioWorklet !== 'undefined';
    }
    
    detectWebAssembly() {
        return typeof WebAssembly !== 'undefined';
    }
    
    detectSharedArrayBuffer() {
        return typeof SharedArrayBuffer !== 'undefined';
    }
    
    detectOffscreenCanvas() {
        return typeof OffscreenCanvas !== 'undefined';
    }
    
    detectDeviceMemory() {
        return navigator.deviceMemory || 4; // Default to 4GB if unknown
    }
    
    detectHardwareConcurrency() {
        return navigator.hardwareConcurrency || 2; // Default to 2 cores
    }
    
    detectConnectionType() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        return connection ? connection.effectiveType : 'unknown';
    }
    
    detectBatteryStatus() {
        // Battery API is deprecated, return conservative estimate
        return { charging: true, level: 0.5 };
    }
    
    detectPerformanceObserver() {
        return typeof PerformanceObserver !== 'undefined';
    }
    
    detectRequestIdleCallback() {
        return typeof requestIdleCallback !== 'undefined';
    }
    
    detectMobile() {
        return /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    detectTablet() {
        return /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent);
    }
    
    detectTouch() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    detectAudioFormats() {
        const audio = document.createElement('audio');
        return {
            mp3: audio.canPlayType('audio/mpeg') !== '',
            wav: audio.canPlayType('audio/wav') !== '',
            ogg: audio.canPlayType('audio/ogg') !== '',
            webm: audio.canPlayType('audio/webm') !== '',
            m4a: audio.canPlayType('audio/mp4') !== ''
        };
    }
    
    getEffectiveConnectionType() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        return connection ? connection.effectiveType : '4g';
    }
    
    getDownlink() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        return connection ? connection.downlink : 10; // Default 10 Mbps
    }
    
    getRTT() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        return connection ? connection.rtt : 100; // Default 100ms
    }
    
    async benchmarkPerformance() {
        console.log('Running performance benchmarks...');
        
        const benchmarks = {
            memoryPerformance: await this.benchmarkMemory(),
            computePerformance: await this.benchmarkCompute(),
            audioLatency: await this.benchmarkAudioLatency(),
            networkLatency: await this.benchmarkNetwork()
        };
        
        this.capabilities.benchmarks = benchmarks;
        this.determinePerformanceProfile();
        this.generateRecommendedSettings();
    }
    
    async benchmarkMemory() {
        const startTime = performance.now();
        
        try {
            // Allocate and fill arrays to test memory performance
            const size = 1000000; // 1M elements
            const array1 = new Float32Array(size);
            const array2 = new Float32Array(size);
            
            for (let i = 0; i < size; i++) {
                array1[i] = Math.random();
                array2[i] = array1[i] * 2;
            }
            
            const endTime = performance.now();
            return endTime - startTime;
        } catch (error) {
            console.warn('Memory benchmark failed:', error);
            return 1000; // Conservative fallback
        }
    }
    
    async benchmarkCompute() {
        const startTime = performance.now();
        
        try {
            // CPU-intensive task
            let result = 0;
            for (let i = 0; i < 1000000; i++) {
                result += Math.sin(i) * Math.cos(i);
            }
            
            const endTime = performance.now();
            return endTime - startTime;
        } catch (error) {
            console.warn('Compute benchmark failed:', error);
            return 500; // Conservative fallback
        }
    }
    
    async benchmarkAudioLatency() {
        if (!this.capabilities.webAudio) {
            return 100; // Default latency for non-WebAudio browsers
        }
        
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const latency = audioContext.baseLatency || audioContext.outputLatency || 0.02; // 20ms default
            this.capabilities.audioContextLatency = latency * 1000; // Convert to ms
            audioContext.close();
            
            return this.capabilities.audioContextLatency;
        } catch (error) {
            console.warn('Audio latency benchmark failed:', error);
            return 50; // Conservative fallback
        }
    }
    
    async benchmarkNetwork() {
        try {
            const startTime = performance.now();
            
            // Small network request to measure actual latency
            const response = await fetch('/static/js/device_capability_manager.js?benchmark=' + Date.now(), {
                method: 'HEAD',
                cache: 'no-cache'
            });
            
            const endTime = performance.now();
            return endTime - startTime;
        } catch (error) {
            console.warn('Network benchmark failed:', error);
            return this.capabilities.rtt || 100;
        }
    }
    
    determinePerformanceProfile() {
        const { deviceMemory, hardwareConcurrency, benchmarks } = this.capabilities;
        
        let score = 0;
        
        // Memory score (0-30 points)
        if (deviceMemory >= 8) score += 30;
        else if (deviceMemory >= 4) score += 20;
        else if (deviceMemory >= 2) score += 10;
        
        // CPU score (0-30 points)
        if (hardwareConcurrency >= 8) score += 30;
        else if (hardwareConcurrency >= 4) score += 20;
        else if (hardwareConcurrency >= 2) score += 10;
        
        // API support score (0-20 points)
        if (this.capabilities.webAssembly) score += 5;
        if (this.capabilities.audioWorklet) score += 5;
        if (this.capabilities.sharedArrayBuffer) score += 5;
        if (this.capabilities.offscreenCanvas) score += 5;
        
        // Benchmark score (0-20 points)
        if (benchmarks) {
            if (benchmarks.memoryPerformance < 100) score += 5;
            if (benchmarks.computePerformance < 100) score += 5;
            if (benchmarks.audioLatency < 20) score += 5;
            if (benchmarks.networkLatency < 50) score += 5;
        }
        
        // Mobile penalty
        if (this.capabilities.isMobile) score -= 15;
        
        // Determine profile
        if (score >= 70) {
            this.performanceProfile = 'high';
        } else if (score >= 40) {
            this.performanceProfile = 'medium';
        } else {
            this.performanceProfile = 'low';
        }
        
        console.log(`Performance profile: ${this.performanceProfile} (score: ${score})`);
    }
    
    generateRecommendedSettings() {
        const base = {
            chunkDuration: 1000,
            sampleRate: 16000,
            channels: 1,
            overlaps: 200,
            vadThreshold: 0.5,
            confidenceThreshold: 0.6,
            adaptiveProcessing: true,
            audioProcessing: false,
            wasmProcessing: false,
            streamingMode: 'batch'
        };
        
        switch (this.performanceProfile) {
            case 'high':
                this.recommendedSettings = {
                    ...base,
                    chunkDuration: 500,        // Smaller chunks for responsiveness
                    overlaps: 100,             // Less overlap needed
                    vadThreshold: 0.3,         // More sensitive VAD
                    confidenceThreshold: 0.7,  // Higher confidence threshold
                    audioProcessing: true,     // Enable audio enhancement
                    wasmProcessing: this.capabilities.webAssembly,
                    streamingMode: 'realtime',
                    maxConcurrentRequests: 3,
                    enableAdvancedFeatures: true
                };
                break;
                
            case 'medium':
                this.recommendedSettings = {
                    ...base,
                    chunkDuration: 750,
                    overlaps: 150,
                    vadThreshold: 0.4,
                    confidenceThreshold: 0.65,
                    audioProcessing: this.capabilities.webAssembly,
                    streamingMode: 'adaptive',
                    maxConcurrentRequests: 2,
                    enableAdvancedFeatures: !this.capabilities.isMobile
                };
                break;
                
            case 'low':
                this.recommendedSettings = {
                    ...base,
                    chunkDuration: 1500,       // Larger chunks
                    overlaps: 300,             // More overlap for accuracy
                    vadThreshold: 0.6,         // Less sensitive VAD
                    confidenceThreshold: 0.5,  // Lower confidence threshold
                    adaptiveProcessing: false, // Disable to save CPU
                    audioProcessing: false,
                    streamingMode: 'batch',
                    maxConcurrentRequests: 1,
                    enableAdvancedFeatures: false
                };
                break;
        }
        
        // Network-specific adjustments
        if (this.capabilities.effectiveType === 'slow-2g' || this.capabilities.effectiveType === '2g') {
            this.recommendedSettings.chunkDuration *= 2; // Larger chunks for slow networks
            this.recommendedSettings.maxConcurrentRequests = 1;
        }
        
        // Battery-aware adjustments
        if (this.capabilities.isMobile) {
            this.recommendedSettings.adaptiveProcessing = true; // Always enable for battery savings
            this.recommendedSettings.confidenceThreshold -= 0.1; // Lower threshold to reduce retries
        }
        
        console.log('Recommended settings:', this.recommendedSettings);
    }
    
    getOptimalConfiguration() {
        return {
            performanceProfile: this.performanceProfile,
            capabilities: this.capabilities,
            recommendedSettings: this.recommendedSettings,
            canUseRealtimeProcessing: this.canUseRealtimeProcessing(),
            suggestedProviders: this.getSuggestedProviders()
        };
    }
    
    canUseRealtimeProcessing() {
        return this.performanceProfile === 'high' && 
               this.capabilities.webAudio && 
               this.capabilities.audioContextLatency < 30 &&
               !this.capabilities.isMobile;
    }
    
    getSuggestedProviders() {
        const providers = ['openai']; // Always include primary
        
        if (this.capabilities.effectiveType === '4g' || this.capabilities.effectiveType === '5g') {
            providers.push('google', 'azure');
        }
        
        // Add local provider for offline capability or privacy
        if (this.performanceProfile !== 'low') {
            providers.push('local');
        }
        
        return providers;
    }
    
    shouldUseFeature(featureName) {
        const features = {
            'webAssembly': this.capabilities.webAssembly && this.performanceProfile !== 'low',
            'audioWorklet': this.capabilities.audioWorklet && this.performanceProfile === 'high',
            'adaptiveProcessing': this.performanceProfile !== 'low',
            'realtimeStreaming': this.canUseRealtimeProcessing(),
            'audioEnhancement': this.performanceProfile === 'high' && !this.capabilities.isMobile,
            'multipleProviders': this.capabilities.effectiveType !== 'slow-2g',
            'backgroundProcessing': this.capabilities.requestIdleCallback && this.performanceProfile !== 'low'
        };
        
        return features[featureName] || false;
    }
    
    adaptToConnectionChange() {
        // Re-evaluate settings when network conditions change
        navigator.connection?.addEventListener('change', () => {
            console.log('Network conditions changed, re-evaluating...');
            this.capabilities.effectiveType = this.getEffectiveConnectionType();
            this.capabilities.downlink = this.getDownlink();
            this.capabilities.rtt = this.getRTT();
            this.capabilities.isOnline = navigator.onLine;
            
            this.generateRecommendedSettings();
        });
    }
    
    getPerformanceReport() {
        return {
            profile: this.performanceProfile,
            capabilities: Object.keys(this.capabilities).filter(key => this.capabilities[key] === true),
            limitations: Object.keys(this.capabilities).filter(key => this.capabilities[key] === false),
            benchmarks: this.capabilities.benchmarks,
            recommendedSettings: this.recommendedSettings,
            warnings: this.getPerformanceWarnings()
        };
    }
    
    getPerformanceWarnings() {
        const warnings = [];
        
        if (this.capabilities.deviceMemory < 2) {
            warnings.push('Low device memory may affect performance');
        }
        
        if (this.capabilities.hardwareConcurrency < 2) {
            warnings.push('Single-core processor detected - reduced concurrency');
        }
        
        if (!this.capabilities.webAudio) {
            warnings.push('Web Audio API not supported - limited audio processing');
        }
        
        if (this.capabilities.effectiveType === 'slow-2g' || this.capabilities.effectiveType === '2g') {
            warnings.push('Slow network connection detected - may affect real-time features');
        }
        
        if (this.capabilities.isMobile) {
            warnings.push('Mobile device detected - battery optimization enabled');
        }
        
        return warnings;
    }
}

// Export for use in other scripts
window.DeviceCapabilityManager = DeviceCapabilityManager;