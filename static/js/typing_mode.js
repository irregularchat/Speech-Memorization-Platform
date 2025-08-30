/**
 * Typing Practice Mode for Speech Memorization Platform
 * Allows users to practice memorization through typing
 */

class TypingMode {
    constructor(textContent, options = {}) {
        this.originalText = textContent;
        this.words = textContent.split(/\s+/);
        this.currentWordIndex = 0;
        this.typedText = '';
        this.mistakes = [];
        this.startTime = null;
        this.endTime = null;
        this.isActive = false;
        
        // Options
        this.options = {
            showFullText: options.showFullText || false,
            highlightErrors: options.highlightErrors !== false,
            allowBackspace: options.allowBackspace !== false,
            progressiveReveal: options.progressiveReveal || false,
            wordsPerLine: options.wordsPerLine || 10,
            difficulty: options.difficulty || 'normal', // easy, normal, hard
            ...options
        };
        
        // Statistics
        this.stats = {
            totalKeystrokes: 0,
            correctKeystrokes: 0,
            incorrectKeystrokes: 0,
            wordsCompleted: 0,
            accuracy: 100,
            wpm: 0,
            corrections: 0
        };
        
        // UI Elements
        this.displayElement = null;
        this.inputElement = null;
        this.statsElement = null;
        this.progressElement = null;
    }
    
    initialize(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Container element not found');
            return false;
        }
        
        // Create UI structure
        this.createUI(container);
        this.setupEventListeners();
        this.renderText();
        
        return true;
    }
    
    createUI(container) {
        container.innerHTML = `
            <div class="typing-mode-container">
                <div class="typing-header">
                    <div class="typing-stats">
                        <span class="stat-item">
                            <i class="fas fa-tachometer-alt"></i>
                            <span id="wpm-display">0</span> WPM
                        </span>
                        <span class="stat-item">
                            <i class="fas fa-bullseye"></i>
                            <span id="accuracy-display">100</span>%
                        </span>
                        <span class="stat-item">
                            <i class="fas fa-clock"></i>
                            <span id="time-display">0:00</span>
                        </span>
                    </div>
                    <div class="typing-controls">
                        <button class="btn btn-sm btn-primary" onclick="typingMode.start()">
                            <i class="fas fa-play"></i> Start
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="typingMode.pause()">
                            <i class="fas fa-pause"></i> Pause
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="typingMode.reset()">
                            <i class="fas fa-redo"></i> Reset
                        </button>
                    </div>
                </div>
                
                <div class="typing-progress">
                    <div class="progress">
                        <div id="typing-progress-bar" class="progress-bar" style="width: 0%"></div>
                    </div>
                    <div class="progress-text">
                        <span id="words-completed">0</span> / <span id="total-words">${this.words.length}</span> words
                    </div>
                </div>
                
                <div class="typing-display" id="typing-display"></div>
                
                <div class="typing-input-container">
                    <textarea 
                        id="typing-input" 
                        class="typing-input" 
                        placeholder="Start typing here..."
                        disabled
                    ></textarea>
                    <div class="typing-hints">
                        <div id="next-word-hint" class="hint-box"></div>
                        <div id="current-position" class="position-indicator"></div>
                    </div>
                </div>
                
                <div class="typing-feedback" id="typing-feedback"></div>
            </div>
        `;
        
        this.displayElement = document.getElementById('typing-display');
        this.inputElement = document.getElementById('typing-input');
        this.statsElement = {
            wpm: document.getElementById('wpm-display'),
            accuracy: document.getElementById('accuracy-display'),
            time: document.getElementById('time-display'),
            wordsCompleted: document.getElementById('words-completed'),
            progressBar: document.getElementById('typing-progress-bar')
        };
    }
    
    setupEventListeners() {
        this.inputElement.addEventListener('input', (e) => this.handleInput(e));
        this.inputElement.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Prevent paste
        this.inputElement.addEventListener('paste', (e) => {
            e.preventDefault();
            this.showFeedback('Pasting is not allowed in typing practice', 'warning');
        });
    }
    
    renderText() {
        this.displayElement.innerHTML = '';
        
        if (this.options.difficulty === 'hard') {
            // Hard mode: Show only blanks
            this.renderBlanksMode();
        } else if (this.options.progressiveReveal) {
            // Progressive reveal mode
            this.renderProgressiveMode();
        } else {
            // Normal mode: Show full text with highlighting
            this.renderNormalMode();
        }
    }
    
    renderNormalMode() {
        let charIndex = 0;
        
        this.words.forEach((word, wordIndex) => {
            const wordSpan = document.createElement('span');
            wordSpan.className = 'typing-word';
            wordSpan.dataset.wordIndex = wordIndex;
            
            // Add each character as a separate span
            for (let char of word) {
                const charSpan = document.createElement('span');
                charSpan.className = 'typing-char';
                charSpan.dataset.charIndex = charIndex++;
                charSpan.textContent = char;
                wordSpan.appendChild(charSpan);
            }
            
            // Add space after word (except last word)
            if (wordIndex < this.words.length - 1) {
                const spaceSpan = document.createElement('span');
                spaceSpan.className = 'typing-space';
                spaceSpan.dataset.charIndex = charIndex++;
                spaceSpan.textContent = ' ';
                wordSpan.appendChild(spaceSpan);
            }
            
            this.displayElement.appendChild(wordSpan);
        });
    }
    
    renderProgressiveMode() {
        // Show only current line of words
        const startIndex = Math.floor(this.currentWordIndex / this.options.wordsPerLine) * this.options.wordsPerLine;
        const endIndex = Math.min(startIndex + this.options.wordsPerLine, this.words.length);
        
        this.displayElement.innerHTML = '';
        
        for (let i = startIndex; i < endIndex; i++) {
            const wordSpan = document.createElement('span');
            wordSpan.className = 'typing-word';
            wordSpan.dataset.wordIndex = i;
            
            if (i < this.currentWordIndex) {
                wordSpan.classList.add('completed');
                wordSpan.textContent = this.words[i];
            } else if (i === this.currentWordIndex) {
                wordSpan.classList.add('current');
                wordSpan.textContent = this.words[i];
            } else {
                wordSpan.classList.add('upcoming');
                wordSpan.textContent = this.words[i];
            }
            
            if (i < endIndex - 1) {
                wordSpan.textContent += ' ';
            }
            
            this.displayElement.appendChild(wordSpan);
        }
    }
    
    renderBlanksMode() {
        // Show underscores for each word
        this.displayElement.innerHTML = '';
        
        this.words.forEach((word, index) => {
            const wordSpan = document.createElement('span');
            wordSpan.className = 'typing-word typing-blank';
            wordSpan.dataset.wordIndex = index;
            
            if (index < this.currentWordIndex) {
                wordSpan.classList.add('completed');
                wordSpan.textContent = word;
            } else if (index === this.currentWordIndex) {
                wordSpan.classList.add('current');
                wordSpan.textContent = '_'.repeat(word.length);
            } else {
                wordSpan.textContent = '_'.repeat(word.length);
            }
            
            if (index < this.words.length - 1) {
                wordSpan.textContent += ' ';
            }
            
            this.displayElement.appendChild(wordSpan);
        });
    }
    
    handleInput(event) {
        if (!this.isActive) return;
        
        const inputValue = event.target.value;
        const lastChar = inputValue[inputValue.length - 1];
        
        this.stats.totalKeystrokes++;
        
        // Check if word is completed (space or punctuation)
        if (lastChar === ' ' || this.isWordComplete(inputValue)) {
            this.checkWord(inputValue.trim());
        } else {
            this.updateDisplay(inputValue);
        }
        
        this.updateStats();
    }
    
    handleKeyDown(event) {
        if (!this.isActive) return;
        
        if (event.key === 'Backspace') {
            if (!this.options.allowBackspace) {
                event.preventDefault();
                this.showFeedback('Backspace is disabled in this mode', 'info');
            } else {
                this.stats.corrections++;
            }
        }
        
        // Tab to skip word (if enabled)
        if (event.key === 'Tab' && this.options.allowSkip) {
            event.preventDefault();
            this.skipWord();
        }
        
        // Escape to pause
        if (event.key === 'Escape') {
            this.pause();
        }
    }
    
    checkWord(typedWord) {
        const expectedWord = this.words[this.currentWordIndex];
        const isCorrect = typedWord === expectedWord;
        
        if (isCorrect) {
            this.stats.correctKeystrokes += typedWord.length;
            this.stats.wordsCompleted++;
            this.markWordComplete(true);
            this.showFeedback('Correct!', 'success');
        } else {
            this.stats.incorrectKeystrokes += Math.abs(typedWord.length - expectedWord.length);
            this.mistakes.push({
                expected: expectedWord,
                typed: typedWord,
                index: this.currentWordIndex
            });
            this.markWordComplete(false);
            this.showFeedback(`Expected: "${expectedWord}"`, 'error');
        }
        
        this.currentWordIndex++;
        this.inputElement.value = '';
        
        if (this.currentWordIndex >= this.words.length) {
            this.complete();
        } else {
            this.updateNextWordHint();
            if (this.options.progressiveReveal) {
                this.renderText();
            }
        }
    }
    
    markWordComplete(isCorrect) {
        const wordElement = this.displayElement.querySelector(
            `[data-word-index="${this.currentWordIndex}"]`
        );
        
        if (wordElement) {
            wordElement.classList.remove('current');
            wordElement.classList.add(isCorrect ? 'correct' : 'incorrect');
            
            if (this.options.difficulty === 'hard') {
                wordElement.textContent = this.words[this.currentWordIndex];
            }
        }
    }
    
    updateDisplay(currentInput) {
        const expectedWord = this.words[this.currentWordIndex];
        const wordElement = this.displayElement.querySelector(
            `[data-word-index="${this.currentWordIndex}"]`
        );
        
        if (!wordElement || this.options.difficulty === 'hard') return;
        
        // Highlight current word
        wordElement.classList.add('current');
        
        // Character-by-character comparison for normal mode
        if (!this.options.progressiveReveal) {
            const charElements = wordElement.querySelectorAll('.typing-char');
            charElements.forEach((charEl, index) => {
                charEl.classList.remove('correct', 'incorrect');
                
                if (index < currentInput.length) {
                    if (currentInput[index] === expectedWord[index]) {
                        charEl.classList.add('correct');
                    } else {
                        charEl.classList.add('incorrect');
                    }
                }
            });
        }
    }
    
    updateStats() {
        // Calculate WPM
        if (this.startTime) {
            const timeElapsed = (Date.now() - this.startTime) / 1000 / 60; // in minutes
            this.stats.wpm = Math.round(this.stats.wordsCompleted / timeElapsed);
        }
        
        // Calculate accuracy
        if (this.stats.totalKeystrokes > 0) {
            this.stats.accuracy = Math.round(
                (this.stats.correctKeystrokes / this.stats.totalKeystrokes) * 100
            );
        }
        
        // Update UI
        this.statsElement.wpm.textContent = this.stats.wpm;
        this.statsElement.accuracy.textContent = this.stats.accuracy;
        this.statsElement.wordsCompleted.textContent = this.stats.wordsCompleted;
        
        // Update progress bar
        const progress = (this.currentWordIndex / this.words.length) * 100;
        this.statsElement.progressBar.style.width = progress + '%';
        
        // Update timer
        if (this.startTime) {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            this.statsElement.time.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }
    
    updateNextWordHint() {
        const hintElement = document.getElementById('next-word-hint');
        if (hintElement && this.currentWordIndex < this.words.length) {
            const nextWord = this.words[this.currentWordIndex];
            
            if (this.options.difficulty === 'easy') {
                // Show full next word
                hintElement.textContent = `Next: ${nextWord}`;
            } else if (this.options.difficulty === 'normal') {
                // Show first letter and length
                hintElement.textContent = `Next: ${nextWord[0]}... (${nextWord.length} letters)`;
            } else {
                // Hard mode: no hints
                hintElement.textContent = '';
            }
        }
    }
    
    showFeedback(message, type) {
        const feedbackElement = document.getElementById('typing-feedback');
        if (feedbackElement) {
            feedbackElement.className = `typing-feedback ${type}`;
            feedbackElement.textContent = message;
            
            setTimeout(() => {
                feedbackElement.classList.add('fade-out');
            }, 2000);
        }
    }
    
    start() {
        this.isActive = true;
        this.startTime = Date.now();
        this.inputElement.disabled = false;
        this.inputElement.focus();
        this.updateNextWordHint();
        
        // Start timer update
        this.timerInterval = setInterval(() => this.updateStats(), 100);
    }
    
    pause() {
        this.isActive = false;
        this.inputElement.disabled = true;
        
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
    }
    
    reset() {
        this.pause();
        
        // Reset state
        this.currentWordIndex = 0;
        this.typedText = '';
        this.mistakes = [];
        this.startTime = null;
        this.endTime = null;
        
        // Reset stats
        this.stats = {
            totalKeystrokes: 0,
            correctKeystrokes: 0,
            incorrectKeystrokes: 0,
            wordsCompleted: 0,
            accuracy: 100,
            wpm: 0,
            corrections: 0
        };
        
        // Reset UI
        this.inputElement.value = '';
        this.renderText();
        this.updateStats();
    }
    
    complete() {
        this.endTime = Date.now();
        this.isActive = false;
        this.pause();
        
        const totalTime = (this.endTime - this.startTime) / 1000;
        const finalWPM = Math.round((this.words.length / totalTime) * 60);
        
        // Show completion dialog
        this.showCompletionDialog({
            wpm: finalWPM,
            accuracy: this.stats.accuracy,
            time: totalTime,
            mistakes: this.mistakes.length,
            corrections: this.stats.corrections
        });
        
        // Send completion event
        if (window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('typingComplete', {
                detail: {
                    stats: this.stats,
                    mistakes: this.mistakes,
                    duration: totalTime
                }
            }));
        }
    }
    
    showCompletionDialog(results) {
        const modalHtml = `
            <div class="modal fade" id="typingCompleteModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Typing Practice Complete!</h5>
                        </div>
                        <div class="modal-body">
                            <div class="results-grid">
                                <div class="result-item">
                                    <i class="fas fa-tachometer-alt fa-2x text-primary"></i>
                                    <h3>${results.wpm} WPM</h3>
                                    <p>Words Per Minute</p>
                                </div>
                                <div class="result-item">
                                    <i class="fas fa-bullseye fa-2x text-success"></i>
                                    <h3>${results.accuracy}%</h3>
                                    <p>Accuracy</p>
                                </div>
                                <div class="result-item">
                                    <i class="fas fa-clock fa-2x text-info"></i>
                                    <h3>${Math.floor(results.time / 60)}:${Math.floor(results.time % 60).toString().padStart(2, '0')}</h3>
                                    <p>Time Taken</p>
                                </div>
                                <div class="result-item">
                                    <i class="fas fa-times-circle fa-2x text-danger"></i>
                                    <h3>${results.mistakes}</h3>
                                    <p>Mistakes</p>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="typingMode.reset()">Try Again</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page if not exists
        if (!document.getElementById('typingCompleteModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('typingCompleteModal'));
        modal.show();
    }
    
    skipWord() {
        this.mistakes.push({
            expected: this.words[this.currentWordIndex],
            typed: '[SKIPPED]',
            index: this.currentWordIndex
        });
        
        this.currentWordIndex++;
        this.inputElement.value = '';
        
        if (this.currentWordIndex >= this.words.length) {
            this.complete();
        } else {
            this.renderText();
            this.updateNextWordHint();
        }
    }
    
    isWordComplete(input) {
        const expectedWord = this.words[this.currentWordIndex];
        return input.trim().length >= expectedWord.length;
    }
}

// CSS for typing mode
const typingStyles = `
<style>
.typing-mode-container {
    padding: 20px;
    background: #f8f9fa;
    border-radius: 10px;
}

.typing-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.typing-stats {
    display: flex;
    gap: 20px;
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 1.1rem;
    font-weight: bold;
}

.typing-display {
    background: white;
    padding: 30px;
    border-radius: 10px;
    font-size: 1.3rem;
    line-height: 2;
    margin-bottom: 20px;
    min-height: 200px;
    font-family: 'Courier New', monospace;
}

.typing-word {
    display: inline;
    margin: 0 2px;
}

.typing-word.current {
    background: #ffc107;
    padding: 2px 4px;
    border-radius: 3px;
}

.typing-word.completed {
    color: #28a745;
}

.typing-word.correct {
    color: #28a745;
    background: #d4edda;
}

.typing-word.incorrect {
    color: #dc3545;
    background: #f8d7da;
}

.typing-char.correct {
    color: #28a745;
}

.typing-char.incorrect {
    color: #dc3545;
    background: #f8d7da;
}

.typing-blank {
    letter-spacing: 2px;
}

.typing-input {
    width: 100%;
    padding: 15px;
    font-size: 1.2rem;
    border: 2px solid #dee2e6;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
}

.typing-input:focus {
    border-color: #007bff;
    outline: none;
}

.typing-hints {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
}

.hint-box {
    padding: 10px;
    background: #e9ecef;
    border-radius: 5px;
    font-style: italic;
}

.typing-feedback {
    margin-top: 15px;
    padding: 10px;
    border-radius: 5px;
    text-align: center;
    transition: all 0.3s ease;
}

.typing-feedback.success {
    background: #d4edda;
    color: #155724;
}

.typing-feedback.error {
    background: #f8d7da;
    color: #721c24;
}

.typing-feedback.warning {
    background: #fff3cd;
    color: #856404;
}

.typing-feedback.info {
    background: #d1ecf1;
    color: #0c5460;
}

.typing-feedback.fade-out {
    opacity: 0;
}

.results-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    text-align: center;
}

.result-item {
    padding: 15px;
}

.result-item h3 {
    margin: 10px 0 5px;
}

.result-item p {
    margin: 0;
    color: #6c757d;
    font-size: 0.9rem;
}
</style>
`;

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TypingMode;
}