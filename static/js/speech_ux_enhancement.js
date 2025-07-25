/**
 * Speech UX Enhancement Layer
 * Transforms speech recognition into an intuitive, delightful experience
 */

class SpeechUXEnhancer {
    constructor(speechManager) {
        this.speechManager = speechManager;
        this.isListening = false;
        this.confidenceVisualizer = null;
        this.breathingIndicator = null;
        this.feedbackEngine = null;
        
        this.initializeVisualFeedback();
        this.setupHapticFeedback();
        this.initializeAudioCues();
    }
    
    initializeVisualFeedback() {
        // Create floating microphone indicator
        this.createMicrophoneIndicator();
        
        // Real-time confidence meter
        this.createConfidenceVisualizer();
        
        // Breathing/rhythm guide
        this.createBreathingIndicator();
        
        // Word-by-word progress visualization
        this.createWordProgressVisualizer();
    }
    
    createMicrophoneIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'speech-microphone-indicator';
        indicator.innerHTML = `
            <div class="mic-container">
                <div class="mic-icon">
                    <i class="fas fa-microphone"></i>
                </div>
                <div class="sound-waves">
                    <div class="wave wave-1"></div>
                    <div class="wave wave-2"></div>
                    <div class="wave wave-3"></div>
                    <div class="wave wave-4"></div>
                </div>
                <div class="listening-status">
                    <span class="status-text">Ready to listen</span>
                    <div class="pulse-ring"></div>
                </div>
            </div>
        `;
        
        // Position as floating overlay
        indicator.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            transform: translateY(100px);
            opacity: 0;
        `;
        
        document.body.appendChild(indicator);
        this.micIndicator = indicator;
        
        // Animate in when speech starts
        setTimeout(() => {
            indicator.style.transform = 'translateY(0)';
            indicator.style.opacity = '1';
        }, 100);
    }
    
    createConfidenceVisualizer() {
        const visualizer = document.createElement('div');
        visualizer.className = 'confidence-visualizer';
        visualizer.innerHTML = `
            <div class="confidence-label">Speech Clarity</div>
            <div class="confidence-bar-container">
                <div class="confidence-bar" id="confidence-fill"></div>
                <div class="confidence-markers">
                    <span class="marker poor">Poor</span>
                    <span class="marker good">Good</span>
                    <span class="marker excellent">Excellent</span>
                </div>
            </div>
            <div class="confidence-tips" id="confidence-tips">
                Speak clearly and at a steady pace
            </div>
        `;
        
        // Style the visualizer
        visualizer.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 15px 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            z-index: 999;
            min-width: 300px;
            text-align: center;
            transition: all 0.3s ease;
            opacity: 0;
            transform: translateX(-50%) translateY(-50px);
        `;
        
        document.body.appendChild(visualizer);
        this.confidenceVisualizer = visualizer;
    }
    
    createBreathingIndicator() {
        const breathing = document.createElement('div');
        breathing.className = 'breathing-guide';
        breathing.innerHTML = `
            <div class="breathing-circle">
                <div class="breathing-text">Breathe</div>
                <div class="breathing-instruction">Inhale... Exhale...</div>
            </div>
        `;
        
        breathing.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 1001;
            display: none;
        `;
        
        document.body.appendChild(breathing);
        this.breathingIndicator = breathing;
    }
    
    startListening() {
        this.isListening = true;
        this.showSpeechInterface();
        this.startVisualFeedback();
        this.playStartSound();
    }
    
    stopListening() {
        this.isListening = false;
        this.hideSpeechInterface();
        this.stopVisualFeedback();
        this.playStopSound();
    }
    
    showSpeechInterface() {
        // Show microphone indicator
        if (this.micIndicator) {
            this.micIndicator.style.transform = 'translateY(0)';
            this.micIndicator.style.opacity = '1';
            this.micIndicator.querySelector('.status-text').textContent = 'Listening...';
            this.micIndicator.classList.add('listening');
        }
        
        // Show confidence visualizer
        if (this.confidenceVisualizer) {
            this.confidenceVisualizer.style.opacity = '1';
            this.confidenceVisualizer.style.transform = 'translateX(-50%) translateY(0)';
        }
        
        // Dim background content
        document.body.style.transition = 'filter 0.3s ease';
        document.querySelector('.container').style.filter = 'blur(2px) brightness(0.7)';
        
        // Add speech mode overlay
        const overlay = document.createElement('div');
        overlay.className = 'speech-mode-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.1);
            z-index: 998;
            backdrop-filter: blur(1px);
        `;
        document.body.appendChild(overlay);
    }
    
    updateConfidence(confidence) {
        if (!this.confidenceVisualizer) return;
        
        const fill = this.confidenceVisualizer.querySelector('#confidence-fill');
        const tips = this.confidenceVisualizer.querySelector('#confidence-tips');
        
        if (fill) {
            fill.style.width = `${confidence * 100}%`;
            fill.style.backgroundColor = this.getConfidenceColor(confidence);
        }
        
        if (tips) {
            tips.textContent = this.getConfidenceTip(confidence);
        }
    }
    
    getConfidenceColor(confidence) {
        if (confidence < 0.3) return '#e74c3c'; // Red
        if (confidence < 0.7) return '#f39c12'; // Orange  
        return '#27ae60'; // Green
    }
    
    getConfidenceTip(confidence) {
        if (confidence < 0.3) return 'Speak louder and more clearly';
        if (confidence < 0.5) return 'Good! Try speaking a bit slower';
        if (confidence < 0.8) return 'Excellent clarity!';
        return 'Perfect! You\'re doing great!';
    }
    
    playStartSound() {
        // Subtle audio cue for speech start
        this.playTone(800, 100); // High tone
    }
    
    playStopSound() {
        // Subtle audio cue for speech end
        this.playTone(400, 100); // Lower tone
    }
    
    playTone(frequency, duration) {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration / 1000);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration / 1000);
    }
    
    hideSpeechInterface() {
        // Hide indicators
        if (this.micIndicator) {
            this.micIndicator.style.transform = 'translateY(100px)';
            this.micIndicator.style.opacity = '0';
        }
        
        if (this.confidenceVisualizer) {
            this.confidenceVisualizer.style.opacity = '0';
            this.confidenceVisualizer.style.transform = 'translateX(-50%) translateY(-50px)';
        }
        
        // Remove overlay
        const overlay = document.querySelector('.speech-mode-overlay');
        if (overlay) {
            overlay.remove();
        }
        
        // Restore background
        document.querySelector('.container').style.filter = 'none';
    }
    
    setupHapticFeedback() {
        // Vibration feedback for mobile devices
        this.vibrate = (pattern) => {
            if ('vibrate' in navigator) {
                navigator.vibrate(pattern);
            }
        };
    }
    
    showWordFeedback(word, isCorrect, confidence) {
        // Create floating word feedback
        const feedback = document.createElement('div');
        feedback.className = `word-feedback ${isCorrect ? 'correct' : 'incorrect'}`;
        feedback.innerHTML = `
            <div class="word-text">${word}</div>
            <div class="word-status">
                <i class="fas fa-${isCorrect ? 'check' : 'times'}"></i>
                <span class="confidence">${Math.round(confidence * 100)}%</span>
            </div>
        `;
        
        // Position near the current word
        const currentWord = document.querySelector('.word-current');
        if (currentWord) {
            const rect = currentWord.getBoundingClientRect();
            feedback.style.cssText = `
                position: fixed;
                left: ${rect.left}px;
                top: ${rect.top - 60}px;
                z-index: 1002;
                background: ${isCorrect ? '#27ae60' : '#e74c3c'};
                color: white;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 0.9rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                animation: wordFeedbackSlide 2s ease-out forwards;
            `;
        }
        
        document.body.appendChild(feedback);
        
        // Remove after animation
        setTimeout(() => feedback.remove(), 2000);
        
        // Haptic feedback
        if (isCorrect) {
            this.vibrate([50]); // Short vibration for correct
        } else {
            this.vibrate([100, 50, 100]); // Pattern for incorrect
        }
    }
}

// CSS Styles for Speech UX
const speechUXStyles = `
<style>
@keyframes wordFeedbackSlide {
    0% { transform: translateY(0); opacity: 1; }
    100% { transform: translateY(-20px); opacity: 0; }
}

.speech-microphone-indicator.listening .sound-waves .wave {
    animation: soundWave 1s ease-in-out infinite;
}

.speech-microphone-indicator.listening .pulse-ring {
    animation: pulseRing 2s ease-out infinite;
}

@keyframes soundWave {
    0%, 100% { transform: scaleY(1); }
    50% { transform: scaleY(2); }
}

@keyframes pulseRing {
    0% { transform: scale(1); opacity: 1; }
    100% { transform: scale(2); opacity: 0; }
}

.confidence-bar-container {
    width: 200px;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    margin: 10px auto;
    position: relative;
    overflow: hidden;
}

.confidence-bar {
    height: 100%;
    width: 0%;
    border-radius: 4px;
    transition: width 0.3s ease, background-color 0.3s ease;
}

.confidence-markers {
    display: flex;
    justify-content: space-between;
    margin-top: 5px;
    font-size: 0.7rem;
    color: #666;
}

.breathing-circle {
    width: 200px;
    height: 200px;
    border: 3px solid #3498db;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: breathingPulse 4s ease-in-out infinite;
}

@keyframes breathingPulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

.word-feedback {
    pointer-events: none;
    display: flex;
    align-items: center;
    gap: 8px;
}

.word-feedback .word-text {
    font-weight: bold;
}

.word-feedback .word-status {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.8rem;
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', speechUXStyles);

// Export for global use
window.SpeechUXEnhancer = SpeechUXEnhancer;