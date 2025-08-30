/**
 * Google Cloud Speech Streaming Client
 * WebSocket-based real-time speech recognition
 */

class GoogleSpeechStreamingClient {
    constructor(sessionKey, options = {}) {
        this.sessionKey = sessionKey;
        this.options = {
            autoReconnect: true,
            maxReconnectAttempts: 5,
            reconnectDelay: 2000,
            ...options
        };
        
        this.websocket = null;
        this.isConnected = false;
        this.isListening = false;
        this.reconnectAttempts = 0;
        
        // Callbacks
        this.onInterimResult = options.onInterimResult || (() => {});
        this.onFinalResult = options.onFinalResult || (() => {});
        this.onPhraseResult = options.onPhraseResult || (() => {});
        this.onError = options.onError || console.error;
        this.onStatusChange = options.onStatusChange || (() => {});
        this.onConnect = options.onConnect || (() => {});
        this.onDisconnect = options.onDisconnect || (() => {});
        
        // State tracking
        this.currentTranscript = '';
        this.lastFinalResult = '';
        this.sessionStartTime = null;
    }
    
    async connect() {
        try {
            // Get WebSocket URL
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            const wsUrl = `${protocol}//${host}/ws/speech/${this.sessionKey}/`;
            
            console.log('Connecting to Google Speech WebSocket:', wsUrl);
            
            this.websocket = new WebSocket(wsUrl);
            this.sessionStartTime = Date.now();
            
            this.websocket.onopen = () => {
                console.log('Google Speech WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.onConnect();
                this.onStatusChange('connected', 'Connected to speech recognition');
            };
            
            this.websocket.onmessage = (event) => {
                this.handleMessage(event.data);
            };
            
            this.websocket.onclose = (event) => {
                console.log('Google Speech WebSocket closed:', event.code, event.reason);
                this.isConnected = false;
                this.isListening = false;
                this.onDisconnect();
                this.onStatusChange('disconnected', 'Disconnected from speech recognition');
                
                // Auto-reconnect if enabled
                if (this.options.autoReconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
                    this.scheduleReconnect();
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('Google Speech WebSocket error:', error);
                this.onError('WebSocket connection error');
                this.onStatusChange('error', 'Connection error');
            };
            
            return true;
            
        } catch (error) {
            console.error('Failed to connect to Google Speech WebSocket:', error);
            this.onError(`Connection failed: ${error.message}`);
            return false;
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.options.reconnectDelay * this.reconnectAttempts;
        
        console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
        this.onStatusChange('reconnecting', `Reconnecting in ${delay/1000}s...`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }
    
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case 'interim_result':
                    this.currentTranscript = message.transcript;
                    this.onInterimResult(message.transcript, message.confidence);
                    this.onStatusChange('listening', `Hearing: \"${message.transcript}\"`);
                    break;
                
                case 'final_result':
                    this.lastFinalResult = message.transcript;
                    this.onFinalResult(message.transcript, message.confidence);
                    this.onStatusChange('processing', 'Processing your speech...');
                    break;
                
                case 'phrase_result':
                    this.onPhraseResult(message.result, message.session_info);
                    break;
                
                case 'status':
                    this.onStatusChange(message.status, message.message);
                    if (message.status === 'listening') {\n                        this.isListening = true;\n                    } else if (message.status === 'stopped') {\n                        this.isListening = false;\n                    }\n                    break;\n                \n                case 'error':\n                    this.onError(message.message);\n                    this.onStatusChange('error', message.message);\n                    break;\n                \n                default:\n                    console.log('Unknown message type:', message.type, message);\n            }\n            \n        } catch (error) {\n            console.error('Error parsing WebSocket message:', error);\n            this.onError('Message parsing error');\n        }\n    }\n    \n    startListening() {\n        if (!this.isConnected) {\n            this.onError('Not connected to speech recognition service');\n            return false;\n        }\n        \n        if (this.isListening) {\n            console.warn('Already listening');\n            return true;\n        }\n        \n        try {\n            this.websocket.send(JSON.stringify({\n                type: 'start_listening'\n            }));\n            \n            console.log('Started Google Speech listening');\n            return true;\n            \n        } catch (error) {\n            console.error('Failed to start listening:', error);\n            this.onError(`Failed to start listening: ${error.message}`);\n            return false;\n        }\n    }\n    \n    stopListening() {\n        if (!this.isConnected || !this.isListening) {\n            return;\n        }\n        \n        try {\n            this.websocket.send(JSON.stringify({\n                type: 'stop_listening'\n            }));\n            \n            console.log('Stopped Google Speech listening');\n            \n        } catch (error) {\n            console.error('Failed to stop listening:', error);\n            this.onError(`Failed to stop listening: ${error.message}`);\n        }\n    }\n    \n    processPhrase(transcript) {\n        if (!this.isConnected) {\n            this.onError('Not connected to speech recognition service');\n            return;\n        }\n        \n        try {\n            this.websocket.send(JSON.stringify({\n                type: 'process_phrase',\n                transcript: transcript\n            }));\n            \n        } catch (error) {\n            console.error('Failed to process phrase:', error);\n            this.onError(`Failed to process phrase: ${error.message}`);\n        }\n    }\n    \n    disconnect() {\n        this.options.autoReconnect = false; // Disable auto-reconnect\n        \n        if (this.websocket) {\n            this.websocket.close();\n            this.websocket = null;\n        }\n        \n        this.isConnected = false;\n        this.isListening = false;\n        console.log('Google Speech client disconnected');\n    }\n    \n    getStatus() {\n        return {\n            isConnected: this.isConnected,\n            isListening: this.isListening,\n            currentTranscript: this.currentTranscript,\n            lastFinalResult: this.lastFinalResult,\n            sessionDuration: this.sessionStartTime ? Date.now() - this.sessionStartTime : 0,\n            reconnectAttempts: this.reconnectAttempts\n        };\n    }\n}\n\n\n/**\n * Google Speech Integration Manager\n * Integrates Google Cloud Speech with the existing practice system\n */\nclass GoogleSpeechIntegration {\n    constructor(options = {}) {\n        this.options = {\n            fallbackToExisting: true,\n            preferGoogleSpeech: true,\n            ...options\n        };\n        \n        this.client = null;\n        this.isAvailable = false;\n        this.sessionKey = null;\n        \n        // Callbacks from existing system\n        this.onResult = options.onResult || (() => {});\n        this.onInterimResult = options.onInterimResult || (() => {});\n        this.onError = options.onError || (() => {});\n        this.onStatusChange = options.onStatusChange || (() => {});\n    }\n    \n    async initialize(sessionKey) {\n        this.sessionKey = sessionKey;\n        \n        try {\n            // Check if Google Speech streaming is available\n            const response = await fetch('/memorization/api/streaming/check-availability/');\n            const data = await response.json();\n            \n            this.isAvailable = data.available;\n            \n            if (this.isAvailable) {\n                console.log('Google Cloud Speech streaming is available');\n                \n                // Initialize streaming client\n                this.client = new GoogleSpeechStreamingClient(sessionKey, {\n                    onInterimResult: (transcript, confidence) => {\n                        this.onInterimResult({\n                            transcript: transcript,\n                            confidence: confidence,\n                            method: 'google_streaming',\n                            isFinal: false\n                        });\n                    },\n                    onFinalResult: (transcript, confidence) => {\n                        this.onResult({\n                            transcript: transcript,\n                            confidence: confidence,\n                            method: 'google_streaming',\n                            isFinal: true\n                        });\n                    },\n                    onPhraseResult: (result, sessionInfo) => {\n                        // Handle phrase processing results\n                        if (window.handlePhraseResult) {\n                            result.session_info = sessionInfo;\n                            window.handlePhraseResult(result);\n                        }\n                    },\n                    onError: (error) => {\n                        console.error('Google Speech error:', error);\n                        this.onError({\n                            method: 'google_streaming',\n                            error: 'streaming_error',\n                            message: error,\n                            fatal: false\n                        });\n                    },\n                    onStatusChange: (status, message) => {\n                        this.onStatusChange(status, message);\n                    }\n                });\n                \n                // Connect to WebSocket\n                const connected = await this.client.connect();\n                if (!connected) {\n                    this.isAvailable = false;\n                    throw new Error('Failed to connect to Google Speech service');\n                }\n                \n                return true;\n                \n            } else {\n                console.log('Google Cloud Speech streaming not available, using fallback');\n                return false;\n            }\n            \n        } catch (error) {\n            console.error('Failed to initialize Google Speech integration:', error);\n            this.isAvailable = false;\n            \n            if (this.options.fallbackToExisting) {\n                console.log('Falling back to existing speech recognition system');\n                return false;\n            } else {\n                throw error;\n            }\n        }\n    }\n    \n    async startRecognition() {\n        if (!this.isAvailable || !this.client) {\n            throw new Error('Google Speech integration not available');\n        }\n        \n        return this.client.startListening();\n    }\n    \n    stopRecognition() {\n        if (this.client) {\n            this.client.stopListening();\n        }\n    }\n    \n    disconnect() {\n        if (this.client) {\n            this.client.disconnect();\n        }\n        this.isAvailable = false;\n    }\n    \n    getStatus() {\n        if (this.client) {\n            return {\n                ...this.client.getStatus(),\n                integration: 'google_streaming',\n                available: this.isAvailable\n            };\n        }\n        \n        return {\n            integration: 'google_streaming',\n            available: this.isAvailable,\n            isConnected: false,\n            isListening: false\n        };\n    }\n}\n\n// Export for use in other scripts\nwindow.GoogleSpeechStreamingClient = GoogleSpeechStreamingClient;\nwindow.GoogleSpeechIntegration = GoogleSpeechIntegration;