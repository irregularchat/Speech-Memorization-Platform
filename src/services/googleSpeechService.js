/**
 * Google Cloud Speech-to-Text API Service
 * Handles real-time speech recognition with superior accuracy
 */

class GoogleSpeechService {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseURL = 'https://speech.googleapis.com/v1/speech';
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioChunks = [];
        this.onResult = null;
        this.onError = null;
        this.onStart = null;
        this.onEnd = null;
        
        // Speech recognition configuration
        this.config = {
            encoding: 'WEBM_OPUS',
            sampleRateHertz: 48000,
            languageCode: 'en-US',
            enableAutomaticPunctuation: true,
            enableWordTimeOffsets: true,
            model: 'latest_long', // Better for longer audio
            useEnhanced: true
        };
    }
    
    async initialize() {
        try {
            // Request microphone permission
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 48000
                }
            });
            
            console.log('✅ Google Cloud Speech Service initialized');
            return true;
        } catch (error) {
            console.error('❌ Failed to initialize Google Speech Service:', error);
            if (this.onError) {
                this.onError(`Microphone access denied: ${error.message}`);
            }
            return false;
        }
    }
    
    async startRecording() {
        if (!this.audioStream) {
            const initialized = await this.initialize();
            if (!initialized) return false;
        }
        
        try {
            this.audioChunks = [];
            
            // Create MediaRecorder with optimal settings for speech
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                await this.processAudio();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            if (this.onStart) {
                this.onStart();
            }
            
            console.log('🎤 Started recording with Google Cloud Speech');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            if (this.onError) {
                this.onError(`Recording failed: ${error.message}`);
            }
            return false;
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            if (this.onEnd) {
                this.onEnd();
            }
            
            console.log('🛑 Stopped recording');
        }
    }
    
    async processAudio() {
        if (this.audioChunks.length === 0) {
            console.warn('⚠️ No audio data to process');
            return;
        }
        
        try {
            // Combine audio chunks into single blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm;codecs=opus' });
            
            // Convert to base64 for API
            const audioBase64 = await this.blobToBase64(audioBlob);
            
            // Send to Google Cloud Speech API
            const result = await this.recognizeSpeech(audioBase64);
            
            if (this.onResult && result) {
                this.onResult(result);
            }
            
        } catch (error) {
            console.error('❌ Failed to process audio:', error);
            if (this.onError) {
                this.onError(`Speech processing failed: ${error.message}`);
            }
        }
    }
    
    async recognizeSpeech(audioBase64) {
        const requestBody = {
            config: this.config,
            audio: {
                content: audioBase64
            }
        };
        
        try {
            console.log('🌐 Sending request to Google Cloud Speech API...');
            
            const response = await fetch(`${this.baseURL}:recognize?key=${this.apiKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Error Response:', errorText);
                
                if (response.status === 403) {
                    throw new Error('Google Cloud API access denied. Please check your API key and billing settings.');
                } else if (response.status === 400) {
                    throw new Error('Invalid request format. Please check audio encoding.');
                } else if (response.status === 429) {
                    throw new Error('API quota exceeded. Please try again later.');
                } else {
                    throw new Error(`Google Speech API error: ${response.status} - ${errorText}`);
                }
            }
            
            const data = await response.json();
            console.log('✅ Google Cloud Speech API response received:', data);
            
            if (data.results && data.results.length > 0) {
                const result = data.results[0];
                const alternative = result.alternatives[0];
                
                return {
                    transcript: alternative.transcript,
                    confidence: alternative.confidence || 0.8,
                    words: alternative.words || [],
                    isFinal: true
                };
            } else {
                console.warn('⚠️ No speech recognized in audio');
                return {
                    transcript: '',
                    confidence: 0,
                    words: [],
                    isFinal: true
                };
            }
            
        } catch (error) {
            console.error('❌ Google Speech API request failed:', error);
            
            // Provide specific error messages for common issues
            if (error.message.includes('CORS')) {
                throw new Error('CORS error: Speech API requires server-side proxy for web browsers');
            } else if (error.message.includes('Failed to fetch')) {
                throw new Error('Network error: Unable to reach Google Speech API');
            } else {
                throw error;
            }
        }
    }
    
    // Streaming recognition for real-time results
    async startStreamingRecognition() {
        if (!this.audioStream) {
            const initialized = await this.initialize();
            if (!initialized) return false;
        }
        
        try {
            // For streaming, we'll use a different approach with websockets or Server-Sent Events
            // This is a simplified version - in production, you'd want to use the streaming API
            
            this.audioChunks = [];
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            // Process audio in chunks for pseudo-streaming
            this.mediaRecorder.ondataavailable = async (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                    
                    // Process every few seconds for near real-time results
                    if (this.audioChunks.length >= 3) {
                        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm;codecs=opus' });
                        const audioBase64 = await this.blobToBase64(audioBlob);
                        
                        try {
                            const result = await this.recognizeSpeech(audioBase64);
                            if (this.onResult && result) {
                                this.onResult({
                                    ...result,
                                    isFinal: false // Indicate this is interim result
                                });
                            }
                        } catch (error) {
                            console.warn('Interim recognition failed:', error);
                        }
                        
                        // Keep only recent chunks to avoid memory issues
                        this.audioChunks = this.audioChunks.slice(-2);
                    }
                }
            };
            
            this.mediaRecorder.start(1000); // 1-second chunks
            this.isRecording = true;
            
            if (this.onStart) {
                this.onStart();
            }
            
            return true;
            
        } catch (error) {
            console.error('❌ Failed to start streaming recognition:', error);
            if (this.onError) {
                this.onError(`Streaming failed: ${error.message}`);
            }
            return false;
        }
    }
    
    async blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                // Remove the data URL prefix to get just the base64 content
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    // Event handlers
    onRecognitionResult(callback) {
        this.onResult = callback;
    }
    
    onRecognitionError(callback) {
        this.onError = callback;
    }
    
    onRecognitionStart(callback) {
        this.onStart = callback;
    }
    
    onRecognitionEnd(callback) {
        this.onEnd = callback;
    }
    
    // Cleanup
    destroy() {
        this.stopRecording();
        
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
        
        console.log('🧹 Google Speech Service destroyed');
    }
}

export default GoogleSpeechService;