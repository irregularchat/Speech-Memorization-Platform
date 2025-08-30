/**
 * Karaoke Mode for Speech Memorization Platform
 * Provides synchronized text highlighting with audio playback
 */

class KaraokeMode {
    constructor(textContent, wordTimings) {
        this.textContent = textContent;
        this.words = textContent.split(/\s+/);
        this.wordTimings = wordTimings || this.generateDefaultTimings();
        this.currentWordIndex = 0;
        this.isPlaying = false;
        this.startTime = null;
        this.animationFrame = null;
        this.playbackSpeed = 1.0;
        
        // Audio elements
        this.audioContext = null;
        this.audioBuffer = null;
        this.sourceNode = null;
        
        // UI elements
        this.displayElement = null;
        this.progressBar = null;
        this.speedControl = null;
    }
    
    generateDefaultTimings() {
        // Generate default timings based on word length (approx 150 words per minute)
        const timings = [];
        let currentTime = 0;
        const baseWordDuration = 400; // milliseconds
        
        this.words.forEach(word => {
            const duration = baseWordDuration + (word.length * 20);
            timings.push({
                word: word,
                start: currentTime,
                end: currentTime + duration
            });
            currentTime += duration + 100; // Add small pause between words
        });
        
        return timings;
    }
    
    initialize(displayElementId) {
        this.displayElement = document.getElementById(displayElementId);
        if (!this.displayElement) {
            console.error('Display element not found');
            return false;
        }
        
        this.renderText();
        this.setupAudioContext();
        return true;
    }
    
    renderText() {
        this.displayElement.innerHTML = '';
        
        this.words.forEach((word, index) => {
            const wordSpan = document.createElement('span');
            wordSpan.className = 'karaoke-word';
            wordSpan.dataset.wordIndex = index;
            wordSpan.textContent = word + ' ';
            this.displayElement.appendChild(wordSpan);
        });
    }
    
    setupAudioContext() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
    }
    
    async loadAudio(audioUrl) {
        try {
            const response = await fetch(audioUrl);
            const arrayBuffer = await response.arrayBuffer();
            this.audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            return true;
        } catch (error) {
            console.error('Error loading audio:', error);
            return false;
        }
    }
    
    play() {
        if (this.isPlaying) return;
        
        this.isPlaying = true;
        this.startTime = Date.now() - (this.currentWordIndex > 0 ? this.wordTimings[this.currentWordIndex].start : 0);
        
        // Start audio playback if available
        if (this.audioBuffer) {
            this.sourceNode = this.audioContext.createBufferSource();
            this.sourceNode.buffer = this.audioBuffer;
            this.sourceNode.playbackRate.value = this.playbackSpeed;
            this.sourceNode.connect(this.audioContext.destination);
            
            const startOffset = this.currentWordIndex > 0 ? 
                this.wordTimings[this.currentWordIndex].start / 1000 : 0;
            this.sourceNode.start(0, startOffset);
            
            this.sourceNode.onended = () => {
                if (this.currentWordIndex >= this.words.length - 1) {
                    this.stop();
                }
            };
        }
        
        this.animate();
    }
    
    pause() {
        this.isPlaying = false;
        
        if (this.sourceNode) {
            this.sourceNode.stop();
            this.sourceNode = null;
        }
        
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
    }
    
    stop() {
        this.pause();
        this.currentWordIndex = 0;
        this.clearHighlights();
    }
    
    animate() {
        if (!this.isPlaying) return;
        
        const currentTime = (Date.now() - this.startTime) * this.playbackSpeed;
        
        // Find current word based on timing
        let foundIndex = -1;
        for (let i = 0; i < this.wordTimings.length; i++) {
            if (currentTime >= this.wordTimings[i].start && 
                currentTime < this.wordTimings[i].end) {
                foundIndex = i;
                break;
            }
        }
        
        if (foundIndex !== -1 && foundIndex !== this.currentWordIndex) {
            this.highlightWord(foundIndex);
            this.currentWordIndex = foundIndex;
        }
        
        // Check if we've reached the end
        if (currentTime > this.wordTimings[this.wordTimings.length - 1].end) {
            this.stop();
            this.onComplete();
            return;
        }
        
        // Update progress bar if exists
        if (this.progressBar) {
            const totalDuration = this.wordTimings[this.wordTimings.length - 1].end;
            const progress = (currentTime / totalDuration) * 100;
            this.progressBar.style.width = progress + '%';
        }
        
        this.animationFrame = requestAnimationFrame(() => this.animate());
    }
    
    highlightWord(index) {
        this.clearHighlights();
        
        const wordElements = this.displayElement.querySelectorAll('.karaoke-word');
        
        // Highlight current word
        if (wordElements[index]) {
            wordElements[index].classList.add('karaoke-current');
            
            // Scroll into view if needed
            wordElements[index].scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'center'
            });
        }
        
        // Mark previous words as completed
        for (let i = 0; i < index; i++) {
            if (wordElements[i]) {
                wordElements[i].classList.add('karaoke-completed');
            }
        }
        
        // Mark upcoming words
        for (let i = index + 1; i < Math.min(index + 5, wordElements.length); i++) {
            if (wordElements[i]) {
                wordElements[i].classList.add('karaoke-upcoming');
            }
        }
    }
    
    clearHighlights() {
        const wordElements = this.displayElement.querySelectorAll('.karaoke-word');
        wordElements.forEach(element => {
            element.classList.remove('karaoke-current', 'karaoke-completed', 'karaoke-upcoming');
        });
    }
    
    setSpeed(speed) {
        this.playbackSpeed = speed;
        
        if (this.sourceNode) {
            this.sourceNode.playbackRate.value = speed;
        }
    }
    
    skipToWord(index) {
        if (index < 0 || index >= this.words.length) return;
        
        const wasPlaying = this.isPlaying;
        
        if (wasPlaying) {
            this.pause();
        }
        
        this.currentWordIndex = index;
        this.highlightWord(index);
        
        if (wasPlaying) {
            this.play();
        }
    }
    
    onComplete() {
        // Override this method to handle completion
        console.log('Karaoke playback completed');
        
        // Send completion event
        if (window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('karaokeComplete', {
                detail: {
                    totalWords: this.words.length,
                    duration: this.wordTimings[this.wordTimings.length - 1].end
                }
            }));
        }
    }
    
    // Practice mode: User follows along with karaoke
    enablePracticeMode() {
        this.practiceMode = true;
        this.userProgress = [];
        
        // Add speech recognition to check if user is speaking along
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[event.results.length - 1][0].transcript;
                this.checkUserProgress(transcript);
            };
        }
    }
    
    checkUserProgress(spokenText) {
        // Check if user is speaking the current word
        const currentWord = this.words[this.currentWordIndex];
        if (currentWord && spokenText.toLowerCase().includes(currentWord.toLowerCase())) {
            this.userProgress.push({
                wordIndex: this.currentWordIndex,
                word: currentWord,
                timestamp: Date.now(),
                correct: true
            });
            
            // Visual feedback
            const wordElement = this.displayElement.querySelector(
                `[data-word-index="${this.currentWordIndex}"]`
            );
            if (wordElement) {
                wordElement.classList.add('user-spoken');
            }
        }
    }
}

// CSS for karaoke mode
const karaokeStyles = `
<style>
.karaoke-word {
    display: inline-block;
    padding: 2px 4px;
    margin: 2px;
    transition: all 0.3s ease;
    cursor: pointer;
}

.karaoke-current {
    background: linear-gradient(45deg, #ffc107, #ff9800);
    color: white;
    font-weight: bold;
    transform: scale(1.2);
    box-shadow: 0 4px 8px rgba(255, 152, 0, 0.3);
    animation: karaoke-pulse 1s infinite;
}

.karaoke-completed {
    color: #28a745;
    opacity: 0.7;
}

.karaoke-upcoming {
    opacity: 0.5;
    font-style: italic;
}

.user-spoken {
    border-bottom: 3px solid #28a745;
}

@keyframes karaoke-pulse {
    0% { transform: scale(1.2); }
    50% { transform: scale(1.3); }
    100% { transform: scale(1.2); }
}

.karaoke-controls {
    display: flex;
    gap: 10px;
    align-items: center;
    margin: 20px 0;
}

.karaoke-progress-bar {
    width: 100%;
    height: 6px;
    background: #e9ecef;
    border-radius: 3px;
    overflow: hidden;
    margin: 10px 0;
}

.karaoke-progress {
    height: 100%;
    background: linear-gradient(90deg, #28a745, #20c997);
    transition: width 0.1s linear;
}

.speed-control {
    display: flex;
    align-items: center;
    gap: 10px;
}

.speed-control input[type="range"] {
    width: 100px;
}
</style>
`;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KaraokeMode;
}