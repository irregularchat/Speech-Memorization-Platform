/**
 * Enhanced Practice JavaScript Module
 * Handles advanced memorization features including word reveal, delayed recall, and adaptive practice
 */

class EnhancedPracticeManager {
    constructor() {
        this.currentSession = null;
        this.audioRecorder = null;
        this.currentWordIndex = 0;
        this.sessionTimer = null;
        this.wordTimingTrackers = new Map();
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }
    
    initialize() {
        console.log('Enhanced Practice Manager initialized');
        this.setupEventListeners();
        this.loadRecommendations();
        this.initializeAudioSystem();
    }
    
    setupEventListeners() {
        // Volume monitoring
        window.addEventListener('speechVolumeUpdate', (event) => {
            this.updateVolumeIndicator(event.detail.volume);
        });
        
        // Microphone test results
        window.addEventListener('microphoneTestComplete', (event) => {
            this.handleMicrophoneTestResults(event.detail);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            this.handleKeyboardShortcuts(event);
        });
    }
    
    async initializeAudioSystem() {
        try {
            if (typeof AISpeechRecorder !== 'undefined') {
                this.audioRecorder = new AISpeechRecorder({
                    onRecordingStart: () => this.onRecordingStart(),
                    onRecordingStop: (data) => this.onRecordingStop(data),
                    onVolumeChange: (volume) => this.updateVolumeIndicator(volume),
                    onError: (error) => this.handleAudioError(error)
                });
                
                // Test microphone permissions
                const hasPermission = await this.audioRecorder.requestMicrophonePermission();
                if (!hasPermission) {
                    this.showAlert('Microphone permission required for speech practice', 'warning');
                }
            } else {
                console.warn('AISpeechRecorder not available - enhanced features may be limited');
            }
        } catch (error) {
            console.error('Audio system initialization failed:', error);
            this.showAlert('Audio system initialization failed', 'error');
        }
    }
    
    onRecordingStart() {
        this.updateRecordingStatus('listening', 'Listening...');
        this.trackWordStartTime();
    }
    
    onRecordingStop(recordingData) {
        this.updateRecordingStatus('processing', 'Processing speech...');
        this.processRecordingData(recordingData);
    }
    
    updateRecordingStatus(status, message) {
        const statusElement = document.getElementById('recording-status');
        if (statusElement) {
            statusElement.className = `recording-status ${status}`;
            statusElement.textContent = message;
        }
    }
    
    trackWordStartTime() {
        const currentTime = Date.now();
        this.wordTimingTrackers.set(this.currentWordIndex, currentTime);
    }
    
    calculateResponseTime() {
        const startTime = this.wordTimingTrackers.get(this.currentWordIndex);
        if (startTime) {
            return (Date.now() - startTime) / 1000; // seconds
        }
        return 0;
    }
    
    updateVolumeIndicator(volume) {
        const volumeBar = document.getElementById('volume-bar');
        if (volumeBar) {
            const percentage = Math.min(volume * 100, 100);
            volumeBar.style.width = `${percentage}%`;
        }
    }
    
    handleAudioError(error) {
        console.error('Audio error:', error);
        this.updateRecordingStatus('error', 'Audio error occurred');
        this.showAlert(`Audio error: ${error}`, 'error');
    }
    
    handleKeyboardShortcuts(event) {
        if (event.ctrlKey || event.metaKey) {
            switch (event.key) {
                case ' ':
                    event.preventDefault();
                    this.toggleRecording();
                    break;
                case 'h':
                    event.preventDefault();
                    this.requestHint();
                    break;
                case 'r':
                    event.preventDefault();
                    this.restartSession();
                    break;
            }
        }
    }
    
    async toggleRecording() {
        if (!this.audioRecorder) {
            this.showAlert('Audio recorder not available', 'error');
            return;
        }
        
        if (this.audioRecorder.isRecording) {
            this.audioRecorder.stopRecording();
        } else {
            await this.audioRecorder.startRecording();
        }
    }
    
    async processRecordingData(recordingData) {
        if (!this.currentSession) {
            this.showAlert('No active practice session', 'error');
            return;
        }
        
        try {
            // First, transcribe the audio
            const transcriptionResponse = await fetch('/api/practice/speech/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    session_key: this.currentSession.session_key,
                    audio_data: recordingData.base64Data,
                    audio_format: recordingData.format
                })
            });
            
            const transcriptionData = await transcriptionResponse.json();
            
            if (transcriptionData.success && transcriptionData.ai_analysis?.transcription) {
                // Process with enhanced features
                await this.processTranscribedText(transcriptionData.ai_analysis.transcription);
            } else {
                this.handleTranscriptionError(transcriptionData);
            }
        } catch (error) {
            console.error('Speech processing error:', error);
            this.showAlert('Failed to process speech', 'error');
        } finally {
            this.updateRecordingStatus('ready', 'Ready to listen...');
        }
    }
    
    async processTranscribedText(spokenText) {
        try {
            const response = await fetch('/api/enhanced/process-speech/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    session_key: this.currentSession.session_key,
                    spoken_text: spokenText,
                    word_index: this.currentWordIndex,
                    response_time: this.calculateResponseTime()
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.handleSuccessfulRecognition(result);
            } else {
                this.handleFailedRecognition(result, spokenText);
            }
        } catch (error) {
            console.error('Enhanced processing error:', error);
            this.showAlert('Failed to process speech with enhanced features', 'error');
        }
    }
    
    handleSuccessfulRecognition(result) {
        if (result.word_found) {
            this.showAlert('Correct!', 'success');
            this.currentWordIndex = result.next_word_index || this.currentWordIndex + 1;
            this.updateDisplayText(result.display_text);
            this.updateProgress();
            
            // Check if session is complete
            if (result.session_complete) {
                this.completeSession();
            }
        } else {
            this.showAlert('Word not found in expected position', 'warning');
        }
    }
    
    handleFailedRecognition(result, spokenText) {
        const expectedWord = result.expected_word || 'unknown';
        this.showAlert(`Expected: "${expectedWord}" | You said: "${spokenText}"`, 'warning');
        
        // Show additional feedback if available
        if (result.ai_analysis?.suggestions) {
            this.showSuggestions(result.ai_analysis.suggestions);
        }
    }
    
    handleTranscriptionError(data) {
        if (data.quality_issues) {
            this.showAlert('Audio quality too low: ' + data.quality_issues.join(', '), 'warning');
        } else {
            this.showAlert('Speech recognition failed. Please try again.', 'error');
        }
    }
    
    updateDisplayText(htmlContent) {
        const textDisplay = document.getElementById('text-display');
        if (textDisplay && htmlContent) {
            textDisplay.innerHTML = htmlContent;
            this.highlightCurrentWord();
        }
    }
    
    highlightCurrentWord() {
        // Remove previous highlights
        document.querySelectorAll('.word.highlighted').forEach(word => {
            word.classList.remove('highlighted');
        });
        
        // Highlight current word
        const currentWord = document.querySelector(`[data-index="${this.currentWordIndex}"]`);
        if (currentWord) {
            currentWord.classList.add('highlighted');
            currentWord.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    updateProgress() {
        const totalWords = document.querySelectorAll('[data-index]').length;
        const completedWords = document.querySelectorAll('.word.completed').length;
        const progress = totalWords > 0 ? (completedWords / totalWords) * 100 : 0;
        
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}% Complete (${completedWords}/${totalWords} words)`;
        }
    }
    
    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('feedback-area');
        if (!alertContainer) return;
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type} alert-dismissible fade show feedback-alert`;
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alertElement);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertElement.parentNode) {
                alertElement.remove();
            }
        }, 5000);
        
        // Scroll alert into view
        alertElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    showSuggestions(suggestions) {
        if (!Array.isArray(suggestions) || suggestions.length === 0) return;
        
        const suggestionHtml = suggestions.map(suggestion => 
            `<li class="small">${suggestion}</li>`
        ).join('');
        
        this.showAlert(`
            <strong>Suggestions:</strong>
            <ul class="mb-0 mt-2">${suggestionHtml}</ul>
        `, 'info');
    }
    
    async requestHint() {
        if (!this.currentSession) return;
        
        try {
            const response = await fetch('/api/enhanced/apply-hint/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    session_key: this.currentSession.session_key,
                    word_index: this.currentWordIndex,
                    hint_type: 'auto'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateDisplayText(result.display_text);
                this.showAlert(`Hint applied: ${result.hint_type}`, 'info');
            } else {
                this.showAlert('Failed to apply hint', 'error');
            }
        } catch (error) {
            console.error('Hint request error:', error);
            this.showAlert('Failed to request hint', 'error');
        }
    }
    
    async loadRecommendations() {
        const textId = this.getTextIdFromUrl();
        if (!textId) return;
        
        try {
            const response = await fetch(`/api/enhanced/recommendations/${textId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.displayRecommendations(data.recommendations);
            }
        } catch (error) {
            console.error('Failed to load recommendations:', error);
        }
    }
    
    displayRecommendations(recommendations) {
        const container = document.getElementById('recommendations-container');
        if (!container) return;
        
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p class="text-muted small">No specific recommendations available. Keep practicing!</p>';
            return;
        }
        
        const html = recommendations.map(rec => {
            const priorityClass = rec.priority === 'high' ? 'border-primary' : 'border-secondary';
            return `
                <div class="card ${priorityClass} mb-2">
                    <div class="card-body p-3">
                        <h6 class="card-title mb-1">${rec.title}</h6>
                        <p class="card-text small mb-0">${rec.description}</p>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = html;
    }
    
    async completeSession() {
        if (!this.currentSession) return;
        
        try {
            const response = await fetch('/api/enhanced/complete-session/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    session_key: this.currentSession.session_key
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSessionResults(result);
            } else {
                this.showAlert('Failed to complete session', 'error');
            }
        } catch (error) {
            console.error('Session completion error:', error);
            this.showAlert('Failed to complete session', 'error');
        }
    }
    
    showSessionResults(results) {
        const practiceDisplay = document.getElementById('practice-display');
        if (!practiceDisplay) return;
        
        const stats = results.statistics || {};
        const analysis = results.analysis || {};
        
        const html = `
            <div class="card">
                <div class="card-header">
                    <h5>🎉 Session Complete!</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Performance</h6>
                            <ul class="list-unstyled">
                                <li><strong>Words Completed:</strong> ${stats.completed_words || 0}/${stats.total_words || 0}</li>
                                <li><strong>Accuracy:</strong> ${Math.round(stats.accuracy || 0)}%</li>
                                <li><strong>Words per Minute:</strong> ${Math.round(stats.words_per_minute || 0)}</li>
                                <li><strong>Duration:</strong> ${Math.round((stats.duration_seconds || 0) / 60)} minutes</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Analysis</h6>
                            <ul class="list-unstyled">
                                <li><strong>Hints Used:</strong> ${stats.hints_used || 0}</li>
                                <li><strong>Problem Areas:</strong> ${(analysis.problem_areas || []).length}</li>
                                <li><strong>Patterns Detected:</strong> ${analysis.patterns_detected || 0}</li>
                            </ul>
                        </div>
                    </div>
                    
                    ${(analysis.recommendations || []).length > 0 ? `
                        <div class="mt-3">
                            <h6>Recommendations</h6>
                            <ul>
                                ${(analysis.recommendations || []).map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    <div class="mt-4 text-center">
                        <button class="btn btn-primary me-2" onclick="location.reload()">Start New Session</button>
                        <button class="btn btn-secondary" onclick="window.location.href='/texts/'">Back to Texts</button>
                    </div>
                </div>
            </div>
        `;
        
        practiceDisplay.innerHTML = html;
        this.currentSession = null;
    }
    
    restartSession() {
        if (confirm('Are you sure you want to restart the current session?')) {
            this.currentSession = null;
            this.currentWordIndex = 0;
            this.wordTimingTrackers.clear();
            location.reload();
        }
    }
    
    getTextIdFromUrl() {
        const pathParts = window.location.pathname.split('/');
        const practiceIndex = pathParts.indexOf('practice');
        return practiceIndex !== -1 && pathParts[practiceIndex + 1] ? 
               parseInt(pathParts[practiceIndex + 1]) : null;
    }
    
    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    // Session management methods
    setCurrentSession(sessionData) {
        this.currentSession = sessionData;
        this.currentWordIndex = 0;
        this.wordTimingTrackers.clear();
    }
    
    getCurrentSession() {
        return this.currentSession;
    }
    
    // Utility method for external access
    static getInstance() {
        if (!window.enhancedPracticeManager) {
            window.enhancedPracticeManager = new EnhancedPracticeManager();
        }
        return window.enhancedPracticeManager;
    }
}

// Initialize the enhanced practice manager
const enhancedPracticeManager = EnhancedPracticeManager.getInstance();

// Export for global access
window.EnhancedPracticeManager = EnhancedPracticeManager;
window.enhancedPracticeManager = enhancedPracticeManager;