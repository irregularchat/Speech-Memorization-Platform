/**
 * Enhanced Speech Memorization Platform
 * Integrates all advanced features from deployment-fixes branch
 * - Multi-provider speech recognition (OpenAI Whisper + Google + WebKit + Azure)
 * - Phrase-based natural speech processing
 * - Real-time streaming recognition
 * - AI-powered feedback and coaching
 */

import MultiProviderSpeechService from './services/multiProviderSpeechService.js';
import { PhraseBasedPracticeEngine } from './services/phraseBasedPracticeEngine.js';
import { StreamingRecognitionService, StreamingPracticeSession } from './services/streamingRecognitionService.js';

// Enhanced sample texts with metadata
const ENHANCED_SAMPLE_TEXTS = [
    {
        id: 1,
        title: "The Art of Public Speaking",
        content: "Public speaking is not just about delivering words to an audience. It is about connecting with people, sharing ideas that matter, and inspiring action through authentic communication. The best speakers understand that confidence comes from preparation, practice, and genuine passion for their message.",
        difficulty: "intermediate",
        tags: ["communication", "confidence", "practice"]
    },
    {
        id: 2, 
        title: "The Innovation Mindset",
        content: "Innovation begins with curiosity and the willingness to challenge conventional thinking. It requires us to ask better questions, explore new possibilities, and embrace failure as a stepping stone to breakthrough discoveries. Every great innovation started with someone who dared to imagine a different future.",
        difficulty: "advanced",
        tags: ["innovation", "creativity", "mindset"]
    },
    {
        id: 3,
        title: "The Power of Perseverance", 
        content: "Success is not final, failure is not fatal. It is the courage to continue that counts. Every setback is a setup for a comeback, and every challenge is an opportunity to grow stronger and more resilient.",
        difficulty: "beginner",
        tags: ["motivation", "resilience", "growth"]
    }
];

// Enhanced Application with Professional Features
class EnhancedSpeechMemorizationApp {
    constructor() {
        // Core state
        this.currentMode = 'phrase-practice'; // New default mode
        this.currentText = ENHANCED_SAMPLE_TEXTS[0];
        this.isActive = false;
        this.startTime = null;
        
        // Advanced services
        this.multiProviderService = null;
        this.practiceEngine = null;
        this.streamingService = null;
        this.streamingSession = null;
        
        // UI state
        this.currentPhrase = null;
        this.processingResult = null;
        this.providerStatus = {};
        this.volumeLevel = 0;
        this.interimTranscript = '';
        
        // Performance tracking
        this.sessionStats = {
            totalPhrases: 0,
            completedPhrases: 0,
            totalAttempts: 0,
            averageAccuracy: 0,
            startTime: null,
            endTime: null
        };
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Enhanced Speech Memorization Platform');
        console.log('🎯 New features: Multi-provider recognition, Phrase-based practice, AI feedback');
        
        try {
            // Initialize advanced services
            await this.initializeAdvancedServices();
            
            // Setup UI and event listeners
            this.setupEnhancedUI();
            this.setupEventListeners();
            
            // Update initial display
            this.updateUI();
            
            console.log('✅ Enhanced platform initialized successfully');
            this.showProviderStatus();
            
        } catch (error) {
            console.error('❌ Initialization error:', error);
            this.showFeedback(`Initialization failed: ${error.message}`, 'danger');
        }
    }

    async initializeAdvancedServices() {
        console.log('🔧 Initializing advanced speech services...');
        
        // Initialize multi-provider speech service
        this.multiProviderService = new MultiProviderSpeechService();
        const multiProviderReady = await this.multiProviderService.initialize();
        
        if (!multiProviderReady) {
            throw new Error('No speech recognition providers available');
        }

        // Initialize phrase-based practice engine
        this.practiceEngine = new PhraseBasedPracticeEngine();
        console.log('✅ Phrase-based practice engine initialized');

        // Initialize streaming recognition service
        this.streamingService = new StreamingRecognitionService();
        const streamingReady = await this.streamingService.initialize();
        
        if (streamingReady) {
            console.log('✅ Streaming recognition service initialized');
            
            // Create streaming practice session
            this.streamingSession = new StreamingPracticeSession(
                this.practiceEngine,
                this.streamingService, 
                this.multiProviderService
            );
        } else {
            console.warn('⚠️ Streaming recognition not available');
        }

        // Setup service callbacks
        this.setupServiceCallbacks();
    }

    setupServiceCallbacks() {
        // Multi-provider service callbacks
        this.multiProviderService.onRecognitionResult((result) => {
            console.log('🎯 Recognition result:', result);
            this.handleRecognitionResult(result);
        });

        this.multiProviderService.onRecognitionError((error) => {
            console.error('❌ Recognition error:', error);
            this.showFeedback(`Recognition error: ${error}`, 'warning');
        });

        this.multiProviderService.onProviderSwitchEvent((provider, errorCount) => {
            console.warn(`⚡ Provider ${provider} failed (${errorCount} errors), switching...`);
            this.showFeedback(`Switched to backup speech provider`, 'info');
            this.updateProviderStatus();
        });

        // Streaming service callbacks (if available)
        if (this.streamingService) {
            this.streamingService.onStreamingInterimResult((transcript, confidence) => {
                this.interimTranscript = transcript;
                this.updateInterimDisplay(transcript, confidence);
            });

            this.streamingService.onStreamingFinalResult((transcript, confidence) => {
                this.processFinalTranscript(transcript, confidence);
            });

            this.streamingService.onVolumeLevelUpdate((level) => {
                this.volumeLevel = level;
                this.updateVolumeIndicator(level);
            });
        }
    }

    setupEnhancedUI() {
        console.log('🎨 Setting up enhanced UI...');
        
        // Add enhanced controls to the existing UI
        this.addAdvancedControls();
        this.addProviderStatusDisplay();
        this.addPhraseDisplay();
        this.addAIFeedbackDisplay();
        this.addStreamingControls();
    }

    addAdvancedControls() {
        const controlsContainer = document.querySelector('#controls');
        if (!controlsContainer) return;

        // Add mode selector
        const modeSelector = document.createElement('div');
        modeSelector.className = 'mode-selector mb-3';
        modeSelector.innerHTML = `
            <label class="form-label">Practice Mode:</label>
            <select id="practiceMode" class="form-select">
                <option value="phrase-practice">Phrase-based Practice (Recommended)</option>
                <option value="streaming-practice">Real-time Streaming Practice</option>
                <option value="classic-speech">Classic Word-by-Word</option>
                <option value="karaoke">Karaoke Mode</option>
                <option value="typing">Typing Mode</option>
                <option value="reading">Reading Mode</option>
            </select>
        `;
        controlsContainer.prepend(modeSelector);

        // Add phrase length control
        const phraseLengthControl = document.createElement('div');
        phraseLengthControl.className = 'phrase-length-control mb-3';
        phraseLengthControl.innerHTML = `
            <label for="phraseLength" class="form-label">Phrase Length (words):</label>
            <input type="range" id="phraseLength" class="form-range" min="5" max="20" value="10">
            <span id="phraseLengthValue">10 words</span>
        `;
        controlsContainer.appendChild(phraseLengthControl);
    }

    addProviderStatusDisplay() {
        const statusContainer = document.createElement('div');
        statusContainer.id = 'providerStatus';
        statusContainer.className = 'provider-status alert alert-info';
        statusContainer.style.display = 'none';
        
        document.querySelector('.container').appendChild(statusContainer);
    }

    addPhraseDisplay() {
        const phraseContainer = document.createElement('div');
        phraseContainer.id = 'currentPhrase';
        phraseContainer.className = 'current-phrase-display p-3 mb-3 border rounded bg-light';
        phraseContainer.innerHTML = `
            <h5>Current Phrase:</h5>
            <div id="phraseText" class="phrase-text fs-4"></div>
            <div id="phraseProgress" class="phrase-progress mt-2">
                <div class="progress">
                    <div id="phraseProgressBar" class="progress-bar" style="width: 0%"></div>
                </div>
                <small id="phraseStats" class="text-muted"></small>
            </div>
        `;
        
        const textDisplay = document.querySelector('#text-display');
        textDisplay.parentNode.insertBefore(phraseContainer, textDisplay.nextSibling);
    }

    addAIFeedbackDisplay() {
        const feedbackContainer = document.createElement('div');
        feedbackContainer.id = 'aiFeedback';
        feedbackContainer.className = 'ai-feedback-display';
        feedbackContainer.innerHTML = `
            <div id="speechAnalysis" class="speech-analysis p-3 mb-3 border rounded" style="display: none;">
                <h6>🤖 AI Speech Analysis</h6>
                <div id="accuracyMetrics" class="accuracy-metrics mb-2"></div>
                <div id="highlightedText" class="highlighted-text mb-2"></div>
                <div id="aiFeedbackText" class="ai-feedback-text alert alert-primary"></div>
            </div>
        `;
        
        document.querySelector('#currentPhrase').appendChild(feedbackContainer);
    }

    addStreamingControls() {
        const streamingContainer = document.createElement('div');
        streamingContainer.id = 'streamingControls';
        streamingContainer.className = 'streaming-controls p-3 mb-3 border rounded bg-info-subtle';
        streamingContainer.style.display = 'none';
        streamingContainer.innerHTML = `
            <h6>🎙️ Live Recognition</h6>
            <div id="interimResults" class="interim-results text-muted fst-italic mb-2"></div>
            <div id="volumeMeter" class="volume-meter mb-2">
                <label class="form-label">Microphone Level:</label>
                <div class="progress">
                    <div id="volumeBar" class="progress-bar bg-success" style="width: 0%"></div>
                </div>
            </div>
            <div id="speechDetection" class="speech-detection">
                <span id="speechStatus" class="badge bg-secondary">Ready</span>
            </div>
        `;
        
        document.querySelector('#controls').appendChild(streamingContainer);
    }

    setupEventListeners() {
        // Mode selector
        document.getElementById('practiceMode')?.addEventListener('change', (e) => {
            this.switchMode(e.target.value);
        });

        // Phrase length control
        const phraseLengthSlider = document.getElementById('phraseLength');
        if (phraseLengthSlider) {
            phraseLengthSlider.addEventListener('input', (e) => {
                document.getElementById('phraseLengthValue').textContent = `${e.target.value} words`;
            });
        }

        // Enhanced microphone button
        const micButton = document.getElementById('mic-btn');
        if (micButton) {
            micButton.addEventListener('click', () => this.toggleAdvancedRecording());
        }

        // Text selector
        document.getElementById('text-select')?.addEventListener('change', (e) => {
            const textId = parseInt(e.target.value);
            this.currentText = ENHANCED_SAMPLE_TEXTS.find(t => t.id === textId) || ENHANCED_SAMPLE_TEXTS[0];
            this.resetSession();
            this.updateUI();
        });

        // Show/hide provider status
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'i') {
                this.toggleProviderStatus();
            }
        });
    }

    async switchMode(mode) {
        console.log(`🔄 Switching to ${mode} mode`);
        
        // Stop any active sessions
        this.stopCurrentSession();
        
        this.currentMode = mode;
        
        // Update UI based on mode
        this.updateModeDisplay();
        
        // Initialize mode-specific features
        switch (mode) {
            case 'phrase-practice':
                this.initPhrasePractice();
                break;
            case 'streaming-practice':
                this.initStreamingPractice();
                break;
            case 'classic-speech':
                // Use existing speech mode logic
                break;
            default:
                console.log(`Mode ${mode} uses existing implementation`);
        }
        
        this.updateUI();
    }

    initPhrasePractice() {
        console.log('🎯 Initializing phrase-based practice...');
        
        const phraseLength = parseInt(document.getElementById('phraseLength')?.value || '10');
        
        // Initialize practice session
        this.practiceEngine.initializeSession(this.currentText.content, {
            phraseLength: phraseLength
        });
        
        // Get first phrase
        this.currentPhrase = this.practiceEngine.getPracticePhrase();
        
        console.log('📝 First phrase:', this.currentPhrase.phraseText);
    }

    initStreamingPractice() {
        console.log('🌊 Initializing streaming practice...');
        
        if (!this.streamingSession) {
            this.showFeedback('Streaming practice not available - microphone access required', 'warning');
            return;
        }
        
        document.getElementById('streamingControls').style.display = 'block';
    }

    async toggleAdvancedRecording() {
        if (this.isActive) {
            await this.stopAdvancedRecording();
        } else {
            await this.startAdvancedRecording();
        }
    }

    async startAdvancedRecording() {
        console.log('🎤 Starting advanced recording...');
        
        try {
            if (this.currentMode === 'streaming-practice') {
                // Start streaming session
                const result = await this.streamingSession.startSession(this.currentText.content, {
                    phraseLength: parseInt(document.getElementById('phraseLength')?.value || '10')
                });
                
                if (result.success) {
                    this.isActive = true;
                    this.currentPhrase = result.currentPhrase;
                    this.updateRecordingState(true);
                    this.showFeedback('🌊 Streaming practice started - speak naturally!', 'success');
                } else {
                    throw new Error(result.error);
                }
                
            } else if (this.currentMode === 'phrase-practice') {
                // Regular phrase practice
                this.isActive = true;
                this.updateRecordingState(true);
                this.showFeedback('🎯 Say the current phrase when ready', 'info');
                
            } else {
                // Classic modes - use existing logic
                this.isActive = true;
                this.updateRecordingState(true);
            }
            
        } catch (error) {
            console.error('❌ Failed to start recording:', error);
            this.showFeedback(`Failed to start: ${error.message}`, 'danger');
        }
    }

    async stopAdvancedRecording() {
        console.log('🛑 Stopping advanced recording...');
        
        if (this.currentMode === 'streaming-practice' && this.streamingSession) {
            const summary = this.streamingSession.stopSession();
            this.showSessionSummary(summary);
        }
        
        this.isActive = false;
        this.updateRecordingState(false);
        this.showFeedback('Recording stopped', 'info');
    }

    stopCurrentSession() {
        if (this.streamingSession && this.isActive) {
            this.streamingSession.stopSession();
        }
        this.isActive = false;
        this.updateRecordingState(false);
    }

    async handleRecognitionResult(result) {
        if (!this.isActive || !result.success) return;
        
        console.log('🎯 Processing recognition result:', result.transcript);
        
        if (this.currentMode === 'phrase-practice' && this.currentPhrase) {
            // Process with phrase-based engine
            const analysis = await this.practiceEngine.processPhraseeSpeech(
                result.transcript,
                this.currentPhrase.phraseText,
                'Enhanced phrase practice'
            );
            
            this.displayPhraseAnalysis(analysis);
            
            if (analysis.phraseCorrect) {
                // Advance to next phrase
                this.currentPhrase = this.practiceEngine.advanceToNextPhrase();
                
                if (this.currentPhrase) {
                    this.updatePhraseDisplay();
                    this.showFeedback('✅ Great! Continue with the next phrase', 'success');
                } else {
                    this.completeSession();
                }
            }
        }
    }

    displayPhraseAnalysis(analysis) {
        const analysisContainer = document.getElementById('speechAnalysis');
        if (!analysisContainer || !analysis.success) return;
        
        analysisContainer.style.display = 'block';
        
        // Update accuracy metrics
        const metricsContainer = document.getElementById('accuracyMetrics');
        metricsContainer.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <strong>Accuracy:</strong> ${analysis.accuracy?.toFixed(1)}%
                </div>
                <div class="col-md-4">
                    <strong>Similarity:</strong> ${(analysis.similarityScore * 100)?.toFixed(1)}%
                </div>
                <div class="col-md-4">
                    <strong>Status:</strong> 
                    <span class="badge ${analysis.phraseCorrect ? 'bg-success' : 'bg-warning'}">
                        ${analysis.phraseCorrect ? 'Correct' : 'Try Again'}
                    </span>
                </div>
            </div>
        `;
        
        // Update highlighted text
        if (analysis.highlightedHTML) {
            document.getElementById('highlightedText').innerHTML = `
                <strong>Word Analysis:</strong><br>
                ${analysis.highlightedHTML}
            `;
        }
        
        // Update AI feedback
        const feedbackContainer = document.getElementById('aiFeedbackText');
        if (analysis.aiFeedback && analysis.aiFeedback.aiAnalysis) {
            feedbackContainer.innerHTML = `
                <strong>🤖 AI Coach:</strong> ${analysis.aiFeedback.aiAnalysis}
            `;
            feedbackContainer.style.display = 'block';
        } else {
            feedbackContainer.style.display = 'none';
        }
    }

    updatePhraseDisplay() {
        if (!this.currentPhrase) return;
        
        document.getElementById('phraseText').textContent = this.currentPhrase.phraseText;
        
        const progressBar = document.getElementById('phraseProgressBar');
        progressBar.style.width = `${this.currentPhrase.progressPercentage}%`;
        
        const sessionInfo = this.practiceEngine._getSessionInfo();
        if (sessionInfo) {
            document.getElementById('phraseStats').textContent = 
                `Phrase ${sessionInfo.phrasesCompleted + 1} • ${sessionInfo.progressPercentage.toFixed(1)}% complete`;
        }
    }

    updateInterimDisplay(transcript, confidence) {
        const interimContainer = document.getElementById('interimResults');
        if (interimContainer) {
            interimContainer.textContent = transcript;
            interimContainer.className = `interim-results text-muted fst-italic mb-2 ${confidence > 0.7 ? 'text-success' : 'text-warning'}`;
        }
    }

    updateVolumeIndicator(level) {
        const volumeBar = document.getElementById('volumeBar');
        if (volumeBar) {
            const percentage = Math.min(level * 100, 100);
            volumeBar.style.width = `${percentage}%`;
            
            // Update color based on level
            volumeBar.className = `progress-bar ${
                level > 0.6 ? 'bg-success' :
                level > 0.3 ? 'bg-warning' : 'bg-secondary'
            }`;
        }
        
        // Update speech detection status
        const speechStatus = document.getElementById('speechStatus');
        if (speechStatus) {
            if (level > 0.1) {
                speechStatus.textContent = 'Speaking';
                speechStatus.className = 'badge bg-success';
            } else {
                speechStatus.textContent = 'Listening';
                speechStatus.className = 'badge bg-primary';
            }
        }
    }

    updateProviderStatus() {
        this.providerStatus = this.multiProviderService.getProviderStatus();
        
        const statusContainer = document.getElementById('providerStatus');
        if (statusContainer) {
            const statusHTML = Object.entries(this.providerStatus).map(([name, status]) => `
                <span class="badge ${status.healthy ? 'bg-success' : 'bg-danger'} me-2">
                    ${name.toUpperCase()}: ${status.enabled ? (status.healthy ? 'Ready' : `Errors: ${status.errorCount}`) : 'Disabled'}
                </span>
            `).join('');
            
            statusContainer.innerHTML = `
                <strong>🔧 Speech Providers:</strong><br>
                ${statusHTML}
                <br><small>Press Ctrl+I to toggle this display</small>
            `;
        }
    }

    showProviderStatus() {
        this.updateProviderStatus();
        
        const availableProviders = Object.entries(this.providerStatus).filter(([, status]) => status.enabled).length;
        console.log(`🔧 Speech providers initialized: ${availableProviders} available`);
        
        if (availableProviders === 0) {
            this.showFeedback('⚠️ No speech providers available', 'danger');
        } else {
            this.showFeedback(`✅ ${availableProviders} speech providers ready`, 'success');
        }
    }

    toggleProviderStatus() {
        const statusContainer = document.getElementById('providerStatus');
        if (statusContainer) {
            statusContainer.style.display = statusContainer.style.display === 'none' ? 'block' : 'none';
        }
    }

    updateModeDisplay() {
        // Show/hide mode-specific UI elements
        const phrasePracticeElements = ['currentPhrase', 'aiFeedback'];
        const streamingElements = ['streamingControls'];
        
        phrasePracticeElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = ['phrase-practice', 'streaming-practice'].includes(this.currentMode) ? 'block' : 'none';
            }
        });
        
        streamingElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = this.currentMode === 'streaming-practice' ? 'block' : 'none';
            }
        });
    }

    updateRecordingState(recording) {
        const micButton = document.getElementById('mic-btn');
        if (micButton) {
            if (recording) {
                micButton.innerHTML = '<i class="fas fa-stop"></i> Stop';
                micButton.className = 'btn btn-danger btn-lg';
            } else {
                micButton.innerHTML = '<i class="fas fa-microphone"></i> Start Practice';
                micButton.className = 'btn btn-primary btn-lg';
            }
        }
    }

    completeSession() {
        const summary = this.practiceEngine.getSessionSummary();
        this.showSessionSummary(summary);
        this.resetSession();
    }

    showSessionSummary(summary) {
        if (!summary) return;
        
        const summaryHTML = `
            <div class="session-summary alert alert-success">
                <h5>🎉 Session Complete!</h5>
                <div class="row">
                    <div class="col-md-3">
                        <strong>Phrases:</strong> ${summary.phrasesCompleted}
                    </div>
                    <div class="col-md-3">
                        <strong>Attempts:</strong> ${summary.totalAttempts}
                    </div>
                    <div class="col-md-3">
                        <strong>Accuracy:</strong> ${summary.overallAccuracy?.toFixed(1)}%
                    </div>
                    <div class="col-md-3">
                        <strong>Time:</strong> ${Math.round(summary.sessionDuration / 1000)}s
                    </div>
                </div>
                ${summary.missedWords?.length > 0 ? `
                    <div class="mt-2">
                        <strong>Words to Review:</strong> ${summary.missedWords.slice(0, 5).map(w => w.word).join(', ')}
                        ${summary.missedWords.length > 5 ? `... and ${summary.missedWords.length - 5} more` : ''}
                    </div>
                ` : ''}
            </div>
        `;
        
        document.getElementById('currentPhrase').innerHTML = summaryHTML;
        
        setTimeout(() => this.updateUI(), 5000); // Reset after 5 seconds
    }

    resetSession() {
        this.stopCurrentSession();
        this.currentPhrase = null;
        this.processingResult = null;
        this.sessionStats = {
            totalPhrases: 0,
            completedPhrases: 0,
            totalAttempts: 0,
            averageAccuracy: 0,
            startTime: null,
            endTime: null
        };
    }

    updateUI() {
        // Update text selector
        const textSelect = document.getElementById('text-select');
        if (textSelect && textSelect.children.length === 0) {
            ENHANCED_SAMPLE_TEXTS.forEach(text => {
                const option = document.createElement('option');
                option.value = text.id;
                option.textContent = `${text.title} (${text.difficulty})`;
                textSelect.appendChild(option);
            });
        }
        
        // Update text display
        const textDisplay = document.getElementById('text-display');
        if (textDisplay) {
            textDisplay.innerHTML = `
                <h4>${this.currentText.title}</h4>
                <p class="lead">${this.currentText.content}</p>
                <div class="text-metadata">
                    <span class="badge bg-secondary">${this.currentText.difficulty}</span>
                    ${this.currentText.tags.map(tag => `<span class="badge bg-outline-primary">#${tag}</span>`).join(' ')}
                </div>
            `;
        }
        
        // Update phrase display if in phrase mode
        if (this.currentPhrase && ['phrase-practice', 'streaming-practice'].includes(this.currentMode)) {
            this.updatePhraseDisplay();
        }
        
        // Update provider status
        this.updateProviderStatus();
    }

    showFeedback(message, type = 'info') {
        console.log(`📢 ${message}`);
        
        // You could add a toast notification system here
        const alertClass = {
            'success': 'alert-success',
            'danger': 'alert-danger', 
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        // Simple feedback display
        let feedbackContainer = document.getElementById('feedback-container');
        if (!feedbackContainer) {
            feedbackContainer = document.createElement('div');
            feedbackContainer.id = 'feedback-container';
            feedbackContainer.className = 'position-fixed top-0 end-0 p-3';
            feedbackContainer.style.zIndex = '1050';
            document.body.appendChild(feedbackContainer);
        }
        
        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        feedbackContainer.appendChild(alert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }
}

// Initialize the enhanced application
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌟 Loading Enhanced Speech Memorization Platform...');
    
    // Set API keys from environment
    window.OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY;
    window.GOOGLE_CLOUD_API_KEY = import.meta.env.VITE_GOOGLE_CLOUD_API_KEY;
    window.AZURE_SPEECH_KEY = import.meta.env.VITE_AZURE_SPEECH_KEY;
    window.AZURE_SPEECH_REGION = import.meta.env.VITE_AZURE_SPEECH_REGION;
    
    console.log('🔑 API Keys configured:');
    console.log('  - OpenAI:', window.OPENAI_API_KEY ? '✅' : '❌');
    console.log('  - Google Cloud:', window.GOOGLE_CLOUD_API_KEY ? '✅' : '❌');
    console.log('  - Azure Speech:', window.AZURE_SPEECH_KEY ? '✅' : '❌');
    
    // Initialize enhanced app
    window.app = new EnhancedSpeechMemorizationApp();
});

export default EnhancedSpeechMemorizationApp;