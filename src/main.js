/**
 * Speech Memorization Platform - Modern Frontend
 * A complete practice application with Google Cloud Speech-to-Text, typing, and karaoke modes
 */

import UnifiedSpeechService from './services/speechService.js';

// Sample texts for practice
const SAMPLE_TEXTS = [
    {
        id: 1,
        title: "The Quick Brown Fox",
        content: "The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet and is perfect for typing practice."
    },
    {
        id: 2,
        title: "Inspirational Quote",
        content: "The only way to do great work is to love what you do. Stay hungry, stay foolish, and never stop learning."
    },
    {
        id: 3,
        title: "Technical Passage",
        content: "Machine learning algorithms enable computers to learn and make decisions from data without being explicitly programmed for every scenario."
    }
];

// Application state
class SpeechMemorizationApp {
    constructor() {
        this.currentMode = 'speech';
        this.currentText = SAMPLE_TEXTS[0];
        this.currentWordIndex = 0;
        this.words = [];
        this.isRecording = false;
        this.isPaused = false;
        this.startTime = null;
        this.completedWords = 0;
        this.totalAttempts = 0;
        this.correctAttempts = 0;
        this.speechService = null;
        this.karaokePlaying = false;
        this.karaokeInterval = null;
        this.typingInput = '';
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Speech Memorization Platform');
        
        // Parse current text into words
        this.parseText();
        
        // Set up Google Cloud speech recognition
        this.initSpeechService();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize UI
        this.updateUI();
        
        // Start with speech mode
        this.switchMode('speech');
        
        console.log('✅ App initialized successfully');
        console.log('🔑 Google Cloud API Key configured:', import.meta.env.VITE_GOOGLE_CLOUD_API_KEY ? 'Yes' : 'No');
        console.log('🎤 WebKit Speech Recognition available:', 'webkitSpeechRecognition' in window);
        
        // Test speech recognition availability immediately
        this.testSpeechRecognitionAvailability();
    }
    
    parseText() {
        this.words = this.currentText.content.split(' ').map((word, index) => ({
            text: word,
            index: index,
            completed: false,
            attempts: 0,
            correct: false
        }));
        this.currentWordIndex = 0;
        console.log(`📝 Parsed ${this.words.length} words from text`);
    }
    
    testSpeechRecognitionAvailability() {
        if ('webkitSpeechRecognition' in window) {
            console.log('✅ WebKit Speech Recognition is available');
            try {
                const test = new webkitSpeechRecognition();
                console.log('✅ Can create WebKit Speech Recognition instance');
            } catch (error) {
                console.error('❌ Error creating WebKit Speech Recognition:', error);
            }
        } else {
            console.error('❌ WebKit Speech Recognition not available');
            this.showFeedback('Speech recognition not supported in this browser. Please use Chrome, Edge, or Safari.', 'danger');
        }
    }
    
    async initSpeechService() {
        try {
            this.speechService = new UnifiedSpeechService();
            
            // Set up event handlers
            this.speechService.setOnStart(() => {
                console.log('🎤 Google Cloud Speech recognition started');
                this.isRecording = true;
                this.updateRecordButton();
            });
            
            this.speechService.setOnEnd(() => {
                console.log('🔇 Google Cloud Speech recognition ended');
                this.isRecording = false;
                this.updateRecordButton();
            });
            
            this.speechService.setOnResult((result) => {
                console.log('🗣️ Speech result:', result);
                if (result.isFinal) {
                    const transcript = result.transcript.trim().toLowerCase();
                    this.processSpokenWord(transcript, result.confidence);
                }
            });
            
            this.speechService.setOnError((error) => {
                console.error('Speech recognition error:', error);
                this.showFeedback(`Speech error: ${error}`, 'danger');
                this.isRecording = false;
                this.updateRecordButton();
            });
            
            // Initialize the service
            const initialized = await this.speechService.initialize();
            if (initialized) {
                const serviceInfo = this.speechService.getServiceInfo();
                console.log('🌟 Speech service initialized:', serviceInfo);
                
                const serviceType = serviceInfo.isGoogleCloud ? 'Google Cloud Speech-to-Text' : 'Browser Speech Recognition';
                this.showFeedback(`✅ ${serviceType} ready for high-accuracy speech recognition!`, 'success');
            } else {
                throw new Error('Failed to initialize speech service');
            }
            
        } catch (error) {
            console.error('❌ Failed to initialize speech service:', error);
            this.showFeedback('Speech recognition initialization failed. Please check your microphone permissions.', 'warning');
        }
    }
    
    setupEventListeners() {
        // Mode switching (already handled by onclick in HTML)
        
        // Record button
        document.getElementById('record-btn').addEventListener('click', () => {
            this.toggleRecording();
        });
        
        // Play button (for karaoke mode)
        document.getElementById('play-btn').addEventListener('click', () => {
            this.toggleKaraoke();
        });
        
        // Pause button
        document.getElementById('pause-btn').addEventListener('click', () => {
            this.pausePractice();
        });
        
        // Hint button
        document.getElementById('hint-btn').addEventListener('click', () => {
            this.showHint();
        });
        
        // Next word button
        document.getElementById('next-btn').addEventListener('click', () => {
            this.nextWord();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case ' ':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.toggleRecording();
                    }
                    break;
                case 'ArrowRight':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.nextWord();
                    }
                    break;
                case 'h':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.showHint();
                    }
                    break;
            }
        });
        
        // Typing mode - create invisible input for typing
        this.createTypingInput();
    }
    
    createTypingInput() {
        // Create a hidden input for capturing typing
        const typingInput = document.createElement('input');
        typingInput.id = 'typing-input';
        typingInput.style.position = 'absolute';
        typingInput.style.left = '-9999px';
        typingInput.style.opacity = '0';
        document.body.appendChild(typingInput);
        
        typingInput.addEventListener('input', (e) => {
            if (this.currentMode === 'typing') {
                this.handleTypingInput(e.target.value);
            }
        });
        
        typingInput.addEventListener('keydown', (e) => {
            if (this.currentMode === 'typing' && e.key === ' ') {
                e.preventDefault();
                this.checkTypedWord();
            }
        });
    }
    
    switchMode(mode) {
        console.log(`🔄 Switching to ${mode} mode`);
        
        // Stop any active processes
        this.stopAllActivities();
        
        // Update mode
        this.currentMode = mode;
        
        // Reset practice state for new mode
        this.resetPractice();
        
        // Update UI
        this.updateModeUI();
        this.updateControlsForMode();
        this.displayText();
        
        // Mode-specific initialization
        switch(mode) {
            case 'speech':
                this.initSpeechMode();
                break;
            case 'typing':
                this.initTypingMode();
                break;
            case 'karaoke':
                this.initKaraokeMode();
                break;
            case 'enhanced':
                this.initEnhancedMode();
                break;
        }
    }
    
    updateModeUI() {
        // Update tab styling
        document.querySelectorAll('.mode-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-mode="${this.currentMode}"]`).classList.add('active');
    }
    
    updateControlsForMode() {
        const recordBtn = document.getElementById('record-btn');
        const playBtn = document.getElementById('play-btn');
        const pauseBtn = document.getElementById('pause-btn');
        
        // Reset all controls
        recordBtn.classList.remove('hidden');
        playBtn.classList.add('hidden');
        pauseBtn.classList.add('hidden');
        
        switch(this.currentMode) {
            case 'speech':
                recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Recording';
                break;
            case 'typing':
                recordBtn.innerHTML = '<i class="fas fa-keyboard"></i> Start Typing';
                break;
            case 'karaoke':
                recordBtn.classList.add('hidden');
                playBtn.classList.remove('hidden');
                pauseBtn.classList.remove('hidden');
                playBtn.innerHTML = '<i class="fas fa-play"></i> Start Karaoke';
                break;
            case 'enhanced':
                recordBtn.innerHTML = '<i class="fas fa-brain"></i> Smart Practice';
                break;
        }
    }
    
    initSpeechMode() {
        const isWebKit = 'webkitSpeechRecognition' in window;
        const message = isWebKit 
            ? '🎤 Speech Practice Mode: Click "Start Recording" and speak the highlighted word clearly. The current word is highlighted in yellow. Make sure to allow microphone access when prompted.'
            : '❌ Speech recognition not available in this browser. Please use Chrome, Edge, or Safari.';
        
        this.showFeedback(message, isWebKit ? 'success' : 'danger');
        
        if (isWebKit) {
            console.log('💡 Instructions: Click the blue "Start Recording" button, allow microphone access, then speak the highlighted yellow word clearly.');
        }
    }
    
    initTypingMode() {
        this.showFeedback('⌨️ Typing Mode: Type each highlighted word and press Space to submit. Focus is automatically set for typing.', 'success');
        // Focus the hidden typing input
        setTimeout(() => {
            document.getElementById('typing-input').focus();
        }, 100);
    }
    
    initKaraokeMode() {
        this.showFeedback('🎵 Karaoke Mode: Click "Start Karaoke" to begin automatic word progression. Speak along as words are highlighted!', 'success');
    }
    
    initEnhancedMode() {
        this.showFeedback('🧠 Enhanced Practice: Advanced mode with intelligent hints and adaptive difficulty. Only current and completed words are visible.', 'success');
    }
    
    stopAllActivities() {
        // Stop speech recognition
        if (this.recognition && this.isRecording) {
            this.recognition.stop();
        }
        
        // Stop karaoke
        if (this.karaokeInterval) {
            clearInterval(this.karaokeInterval);
            this.karaokeInterval = null;
        }
        this.karaokePlaying = false;
        
        // Clear typing input
        const typingInput = document.getElementById('typing-input');
        if (typingInput) {
            typingInput.value = '';
        }
        this.typingInput = '';
    }
    
    displayText() {
        const textDisplay = document.getElementById('text-display');
        
        if (!this.words || this.words.length === 0) {
            textDisplay.innerHTML = '<p>No text loaded. Please select a practice mode to begin!</p>';
            return;
        }
        
        let html = '';
        this.words.forEach((word, index) => {
            let classes = ['word'];
            
            if (index === this.currentWordIndex) {
                classes.push('current');
            }
            
            if (word.completed) {
                classes.push('completed');
            }
            
            // Special styling for different modes
            if (this.currentMode === 'enhanced' && !word.completed && index > this.currentWordIndex) {
                classes.push('hidden');
            }
            
            html += `<span class="${classes.join(' ')}" data-index="${index}">${word.text}</span>`;
            
            // Add space after each word, but not after the last one
            if (index < this.words.length - 1) {
                html += ' ';
            }
        });
        
        textDisplay.innerHTML = html;
        
        // Add click handlers for manual word selection
        textDisplay.querySelectorAll('.word').forEach(wordEl => {
            wordEl.addEventListener('click', () => {
                const index = parseInt(wordEl.dataset.index);
                if (index !== this.currentWordIndex) {
                    this.currentWordIndex = index;
                    this.displayText();
                    console.log(`Manually selected word ${index}: "${this.words[index].text}"`);
                }
            });
        });
        
        // Ensure current word is visible (scroll into view if needed)
        setTimeout(() => {
            const currentWordEl = textDisplay.querySelector('.word.current');
            if (currentWordEl) {
                currentWordEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 100);
    }
    
    async toggleRecording() {
        console.log('🔴 toggleRecording() called, isRecording:', this.isRecording);
        
        if (!this.speechService) {
            console.error('❌ Speech service not initialized');
            this.showFeedback('Speech recognition service not initialized', 'danger');
            return;
        }
        
        if (this.isRecording) {
            console.log('⏹️ Stopping recording...');
            this.speechService.stopRecording();
        } else {
            console.log('▶️ Starting recording...');
            this.startTime = this.startTime || Date.now();
            
            try {
                const started = await this.speechService.startRecording();
                console.log('🎤 Recording start result:', started);
                
                if (!started) {
                    console.error('❌ Failed to start recording');
                    this.showFeedback('Failed to start recording. Please check microphone permissions.', 'danger');
                } else {
                    console.log('✅ Recording started successfully');
                    this.showFeedback('🎤 Recording started! Speak clearly now.', 'info');
                }
            } catch (error) {
                console.error('❌ Error starting recording:', error);
                this.showFeedback(`Recording error: ${error.message}`, 'danger');
            }
        }
    }
    
    updateRecordButton() {
        const recordBtn = document.getElementById('record-btn');
        
        if (this.isRecording) {
            recordBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
            recordBtn.classList.remove('btn-primary');
            recordBtn.classList.add('btn-danger');
            recordBtn.classList.add('pulse');
        } else {
            const icon = this.currentMode === 'speech' ? 'microphone' : 
                        this.currentMode === 'typing' ? 'keyboard' : 
                        this.currentMode === 'enhanced' ? 'brain' : 'microphone';
            
            recordBtn.innerHTML = `<i class="fas fa-${icon}"></i> Start ${this.currentMode.charAt(0).toUpperCase() + this.currentMode.slice(1)}`;
            recordBtn.classList.remove('btn-danger');
            recordBtn.classList.add('btn-primary');
            recordBtn.classList.remove('pulse');
        }
    }
    
    processSpokenWord(transcript, confidence = 0.8) {
        console.log(`🗣️ Processing spoken word: "${transcript}" (confidence: ${(confidence * 100).toFixed(1)}%)`);
        
        const currentWord = this.words[this.currentWordIndex];
        if (!currentWord) return;
        
        const spokenWords = transcript.toLowerCase().split(' ');
        const targetWord = currentWord.text.toLowerCase().replace(/[^\w]/g, '');
        
        // Enhanced matching with confidence consideration
        let bestMatch = 0;
        let wordFound = false;
        
        spokenWords.forEach(spokenWord => {
            const cleanSpoken = spokenWord.replace(/[^\w]/g, '');
            
            // Exact match
            if (cleanSpoken === targetWord) {
                bestMatch = 1.0;
                wordFound = true;
            }
            // Partial matches (only if confidence is high enough)
            else if (confidence > 0.7) {
                if (cleanSpoken.includes(targetWord) || targetWord.includes(cleanSpoken)) {
                    const similarity = Math.max(cleanSpoken.length, targetWord.length) / 
                                     Math.min(cleanSpoken.length, targetWord.length);
                    if (similarity < 2) { // Words are reasonably similar in length
                        bestMatch = Math.max(bestMatch, 0.8);
                        wordFound = true;
                    }
                }
            }
        });
        
        this.totalAttempts++;
        currentWord.attempts++;
        
        if (wordFound && confidence > 0.5) {
            this.handleCorrectWord(confidence, bestMatch);
        } else {
            this.handleIncorrectWord(transcript, targetWord, confidence);
        }
    }
    
    handleCorrectWord(confidence = 1.0, matchScore = 1.0) {
        const currentWord = this.words[this.currentWordIndex];
        currentWord.completed = true;
        currentWord.correct = true;
        
        this.correctAttempts++;
        this.completedWords++;
        
        // Show confidence-based feedback
        const confidencePercent = (confidence * 100).toFixed(0);
        const matchPercent = (matchScore * 100).toFixed(0);
        
        let feedback = '✅ Correct!';
        if (confidence >= 0.9 && matchScore >= 0.9) {
            feedback = '🎯 Perfect! Excellent pronunciation!';
        } else if (confidence >= 0.8) {
            feedback = `✅ Correct! (${confidencePercent}% confidence)`;
        } else {
            feedback = `✅ Correct! Try speaking more clearly for better recognition.`;
        }
        
        this.showFeedback(feedback, 'success');
        
        // Move to next word
        setTimeout(() => {
            this.nextWord();
        }, 1200);
        
        this.updateStats();
        this.displayText();
    }
    
    handleIncorrectWord(spoken, expected, confidence = 0) {
        const confidencePercent = (confidence * 100).toFixed(0);
        
        let feedback = `❌ Expected: "${expected}" | You said: "${spoken}"`;
        
        if (confidence < 0.3) {
            feedback += ` | Try speaking more clearly (${confidencePercent}% confidence)`;
        } else if (confidence < 0.6) {
            feedback += ` | Good volume, but pronunciation needs work`;
        }
        
        this.showFeedback(feedback, 'warning');
        
        // If too many attempts, offer a hint
        if (this.words[this.currentWordIndex].attempts >= 3) {
            setTimeout(() => {
                this.showHint();
            }, 2500);
        }
        
        this.updateStats();
    }
    
    nextWord() {
        if (this.currentWordIndex < this.words.length - 1) {
            this.currentWordIndex++;
            this.displayText();
            
            // Clear typing input
            const typingInput = document.getElementById('typing-input');
            if (typingInput) {
                typingInput.value = '';
            }
            this.typingInput = '';
            
        } else {
            this.completePractice();
        }
    }
    
    showHint() {
        const currentWord = this.words[this.currentWordIndex];
        if (!currentWord) return;
        
        const word = currentWord.text;
        let hint = '';
        
        if (currentWord.attempts < 2) {
            // Show first letter
            hint = `💡 Hint: The word starts with "${word[0]}"`;
        } else if (currentWord.attempts < 4) {
            // Show first half of word
            const halfLength = Math.ceil(word.length / 2);
            hint = `💡 Hint: The word starts with "${word.substring(0, halfLength)}..."`;
        } else {
            // Show the full word
            hint = `💡 The word is: "${word}"`;
        }
        
        this.showFeedback(hint, 'info');
    }
    
    toggleKaraoke() {
        if (this.karaokePlaying) {
            this.stopKaraoke();
        } else {
            this.startKaraoke();
        }
    }
    
    startKaraoke() {
        this.karaokePlaying = true;
        this.currentWordIndex = 0;
        this.startTime = Date.now();
        
        const playBtn = document.getElementById('play-btn');
        playBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Karaoke';
        playBtn.classList.remove('btn-success');
        playBtn.classList.add('btn-danger');
        
        this.showFeedback('🎵 Karaoke started! Speak along with the highlighted words', 'success');
        
        // Advance words every 2 seconds
        this.karaokeInterval = setInterval(() => {
            if (this.currentWordIndex < this.words.length - 1) {
                this.currentWordIndex++;
                this.displayText();
                this.updateStats();
            } else {
                this.stopKaraoke();
                this.completePractice();
            }
        }, 2000);
        
        this.displayText();
    }
    
    stopKaraoke() {
        this.karaokePlaying = false;
        
        if (this.karaokeInterval) {
            clearInterval(this.karaokeInterval);
            this.karaokeInterval = null;
        }
        
        const playBtn = document.getElementById('play-btn');
        playBtn.innerHTML = '<i class="fas fa-play"></i> Start Karaoke';
        playBtn.classList.remove('btn-danger');
        playBtn.classList.add('btn-success');
        
        this.showFeedback('Karaoke stopped', 'info');
    }
    
    handleTypingInput(value) {
        this.typingInput = value;
        
        // Show real-time feedback
        const currentWord = this.words[this.currentWordIndex];
        if (!currentWord) return;
        
        const targetWord = currentWord.text.toLowerCase().replace(/[^\w]/g, '');
        const typedWord = value.toLowerCase().replace(/[^\w]/g, '');
        
        if (targetWord.startsWith(typedWord)) {
            this.showFeedback(`Typing: "${value}" ✅`, 'success');
        } else {
            this.showFeedback(`Typing: "${value}" ❌`, 'warning');
        }
    }
    
    checkTypedWord() {
        const currentWord = this.words[this.currentWordIndex];
        if (!currentWord) return;
        
        const targetWord = currentWord.text.toLowerCase().replace(/[^\w]/g, '');
        const typedWord = this.typingInput.toLowerCase().replace(/[^\w]/g, '');
        
        this.totalAttempts++;
        currentWord.attempts++;
        
        if (typedWord === targetWord) {
            this.handleCorrectWord();
        } else {
            this.handleIncorrectWord(this.typingInput, currentWord.text);
        }
        
        // Clear input
        document.getElementById('typing-input').value = '';
        this.typingInput = '';
    }
    
    pausePractice() {
        this.isPaused = !this.isPaused;
        
        if (this.isPaused) {
            this.stopAllActivities();
            this.showFeedback('Practice paused', 'info');
        } else {
            this.showFeedback('Practice resumed', 'success');
        }
    }
    
    completePractice() {
        this.stopAllActivities();
        
        const endTime = Date.now();
        const duration = this.startTime ? (endTime - this.startTime) / 1000 : 0;
        const accuracy = this.totalAttempts > 0 ? (this.correctAttempts / this.totalAttempts * 100) : 0;
        const wpm = duration > 0 ? (this.completedWords / (duration / 60)) : 0;
        
        const congratsMessage = `
            🎉 Practice Complete! 
            
            📊 Your Results:
            • Words Completed: ${this.completedWords}/${this.words.length}
            • Accuracy: ${accuracy.toFixed(1)}%
            • Time: ${this.formatTime(duration)}
            • Words Per Minute: ${wpm.toFixed(1)}
            
            Great job! Try another mode or practice again to improve your skills.
        `;
        
        this.showFeedback(congratsMessage, 'success');
        
        // Reset for new practice
        setTimeout(() => {
            this.resetPractice();
        }, 5000);
    }
    
    resetPractice() {
        this.currentWordIndex = 0;
        this.completedWords = 0;
        this.totalAttempts = 0;
        this.correctAttempts = 0;
        this.startTime = null;
        
        // Reset word states
        this.words.forEach(word => {
            word.completed = false;
            word.attempts = 0;
            word.correct = false;
        });
        
        this.updateStats();
        this.displayText();
        this.showFeedback('Ready for new practice session!', 'info');
    }
    
    updateStats() {
        const accuracy = this.totalAttempts > 0 ? (this.correctAttempts / this.totalAttempts * 100) : 0;
        const duration = this.startTime ? (Date.now() - this.startTime) / 1000 : 0;
        const wpm = duration > 0 ? (this.completedWords / (duration / 60)) : 0;
        
        document.getElementById('accuracy-stat').textContent = `${accuracy.toFixed(1)}%`;
        document.getElementById('words-completed-stat').textContent = `${this.completedWords}/${this.words.length}`;
        document.getElementById('time-stat').textContent = this.formatTime(duration);
        document.getElementById('wpm-stat').textContent = wpm.toFixed(1);
    }
    
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    showFeedback(message, type) {
        const feedbackArea = document.getElementById('feedback-area');
        feedbackArea.innerHTML = `
            <div class="feedback ${type} fade-in">
                ${message}
            </div>
        `;
        
        // Auto-hide after 5 seconds for non-critical messages
        if (type !== 'success' || !message.includes('Complete')) {
            setTimeout(() => {
                if (feedbackArea.innerHTML.includes(message)) {
                    feedbackArea.innerHTML = '';
                }
            }, 5000);
        }
    }
    
    updateUI() {
        this.updateStats();
        this.displayText();
    }
}

// Global function for HTML onclick handlers
window.switchMode = function(mode) {
    if (window.app) {
        window.app.switchMode(mode);
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SpeechMemorizationApp();
});

// Export for potential module use
export default SpeechMemorizationApp;