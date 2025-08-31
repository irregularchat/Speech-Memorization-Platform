/**
 * Phrase-Based Practice Engine
 * Natural speech processing for memorization practice
 * Ported from memorization/ai_speech_service.py
 */

class PhraseBasedSpeechAnalyzer {
    constructor() {
        this.client = null; // Will be set if OpenAI API is available
        this.initializeAI();
    }

    async initializeAI() {
        if (window.OPENAI_API_KEY) {
            this.client = {
                apiKey: window.OPENAI_API_KEY,
                baseURL: 'https://api.openai.com/v1'
            };
            console.log('✅ AI-powered feedback initialized');
        }
    }

    async analyzePhraseAccuracy(spokenText, expectedText, context = "") {
        try {
            // Clean and normalize text
            const spokenClean = this._normalizeText(spokenText);
            const expectedClean = this._normalizeText(expectedText);

            // Calculate similarity
            const similarity = this._calculateSimilarity(spokenClean, expectedClean);

            // Generate word-level diff
            const wordDiff = this._generateWordDiff(spokenClean, expectedClean);

            // Create highlighted HTML for display
            const highlightedHTML = this._createHighlightedDisplay(wordDiff, expectedClean);

            // Get AI-powered feedback for non-perfect matches
            let aiFeedback = null;
            if (similarity < 0.9 && this.client) {
                aiFeedback = await this._getAIPhraseFeedback(spokenClean, expectedClean, wordDiff, context);
            }

            // Calculate phrase-level accuracy
            const phraseAccuracy = this._calculatePhraseAccuracy(wordDiff);

            return {
                success: true,
                overallAccuracy: similarity * 100,
                phraseAccuracy: phraseAccuracy,
                similarityScore: similarity,
                wordDifferences: wordDiff,
                highlightedHTML: highlightedHTML,
                spokenText: spokenClean,
                expectedText: expectedClean,
                aiFeedback: aiFeedback,
                needsRetry: phraseAccuracy < 80,
                perfectMatch: similarity > 0.95
            };

        } catch (error) {
            console.error('Phrase analysis error:', error);
            return {
                success: false,
                error: error.message,
                overallAccuracy: 0
            };
        }
    }

    _calculateSimilarity(spoken, expected) {
        // Sequence matching algorithm
        return this._sequenceMatcher(spoken.toLowerCase(), expected.toLowerCase());
    }

    _sequenceMatcher(a, b) {
        const matrix = [];
        const aLen = a.length;
        const bLen = b.length;

        // Initialize matrix
        for (let i = 0; i <= aLen; i++) {
            matrix[i] = [];
            matrix[i][0] = i;
        }
        for (let j = 0; j <= bLen; j++) {
            matrix[0][j] = j;
        }

        // Fill matrix
        for (let i = 1; i <= aLen; i++) {
            for (let j = 1; j <= bLen; j++) {
                if (a[i - 1] === b[j - 1]) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j - 1] + 1
                    );
                }
            }
        }

        const distance = matrix[aLen][bLen];
        const maxLen = Math.max(aLen, bLen);
        return maxLen === 0 ? 1 : (maxLen - distance) / maxLen;
    }

    _normalizeText(text) {
        // Remove extra whitespace and punctuation for comparison
        return text.replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim().toLowerCase();
    }

    _generateWordDiff(spoken, expected) {
        const spokenWords = spoken.split(' ');
        const expectedWords = expected.split(' ');
        const differences = [];

        // Simple word-by-word comparison with basic alignment
        const maxLength = Math.max(spokenWords.length, expectedWords.length);

        for (let i = 0; i < maxLength; i++) {
            const expectedWord = i < expectedWords.length ? expectedWords[i] : '';
            const spokenWord = i < spokenWords.length ? spokenWords[i] : '';

            if (expectedWord === spokenWord) {
                differences.push({
                    position: i,
                    expectedWord: expectedWord,
                    spokenWord: spokenWord,
                    type: 'correct',
                    status: 'correct'
                });
            } else if (expectedWord && spokenWord) {
                // Check for pronunciation similarity
                const similarity = this._calculateWordSimilarity(expectedWord, spokenWord);
                const type = similarity > 0.7 ? 'pronunciation' : 'substitution';
                
                differences.push({
                    position: i,
                    expectedWord: expectedWord,
                    spokenWord: spokenWord,
                    type: type,
                    status: 'error',
                    similarity: similarity
                });
            } else if (expectedWord && !spokenWord) {
                differences.push({
                    position: i,
                    expectedWord: expectedWord,
                    spokenWord: '[MISSING]',
                    type: 'missing',
                    status: 'error'
                });
            } else if (!expectedWord && spokenWord) {
                differences.push({
                    position: i,
                    expectedWord: '[EXTRA]',
                    spokenWord: spokenWord,
                    type: 'extra',
                    status: 'error'
                });
            }
        }

        return differences;
    }

    _calculateWordSimilarity(word1, word2) {
        // Simple phonetic similarity check
        if (Math.abs(word1.length - word2.length) > 2) return 0;
        
        let matches = 0;
        const minLength = Math.min(word1.length, word2.length);
        
        for (let i = 0; i < minLength; i++) {
            if (word1[i] === word2[i]) matches++;
        }
        
        return matches / Math.max(word1.length, word2.length);
    }

    _createHighlightedDisplay(wordDiff, expectedText) {
        const htmlParts = [];
        const expectedWords = expectedText.split(' ');

        for (const diff of wordDiff) {
            if (diff.position < expectedWords.length) {
                if (diff.type === 'correct') {
                    htmlParts.push(`<span class="word-correct">${diff.expectedWord}</span>`);
                } else if (['substitution', 'missing', 'pronunciation'].includes(diff.type)) {
                    const tooltipText = diff.spokenWord === '[MISSING]' 
                        ? 'This word was not spoken' 
                        : `You said: "${diff.spokenWord}"`;
                    htmlParts.push(`<span class="word-error" title="${tooltipText}">${diff.expectedWord}</span>`);
                }
            }
        }

        return htmlParts.join(' ');
    }

    _calculatePhraseAccuracy(wordDiff) {
        if (!wordDiff || wordDiff.length === 0) return 0;

        const correctWords = wordDiff.filter(diff => diff.status === 'correct').length;
        const totalWords = wordDiff.filter(diff => diff.type !== 'extra').length;

        return totalWords > 0 ? (correctWords / totalWords) * 100 : 0;
    }

    async _getAIPhraseFeedback(spoken, expected, wordDiff, context) {
        if (!this.client) return null;

        try {
            const errors = wordDiff.filter(diff => diff.status === 'error');
            const errorSummary = errors.slice(0, 5).map(diff => 
                `${diff.expectedWord} (said: ${diff.spokenWord})`
            ).join(', ');

            const prompt = `Analyze this speech memorization attempt for a full phrase/sentence:

Expected: "${expected}"
User spoke: "${spoken}"
Word-level errors: ${errorSummary || "None - perfect match!"}
Context: ${context || "Speech memorization practice"}

Provide specific, encouraging feedback focusing on:
1. Overall phrase flow and natural speech
2. Specific word corrections needed
3. Memory vs pronunciation issues
4. Tips for improvement

Keep feedback constructive and encouraging. 2-3 sentences max.`;

            const response = await fetch(`${this.client.baseURL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.client.apiKey}`
                },
                body: JSON.stringify({
                    model: 'gpt-4o-mini',
                    messages: [
                        {
                            role: 'system',
                            content: 'You are a helpful speech coach providing feedback for natural phrase-based speech practice. Focus on helping users speak naturally while memorizing text.'
                        },
                        {
                            role: 'user',
                            content: prompt
                        }
                    ],
                    max_tokens: 200,
                    temperature: 0.7
                })
            });

            if (!response.ok) {
                throw new Error(`OpenAI API error: ${response.status}`);
            }

            const data = await response.json();
            const feedback = data.choices[0].message.content.trim();

            return {
                aiAnalysis: feedback,
                errorCount: errors.length,
                hasFeedback: true
            };

        } catch (error) {
            console.warn('AI phrase feedback generation failed:', error);
            return null;
        }
    }
}

class PhraseBasedPracticeEngine {
    constructor() {
        this.speechAnalyzer = new PhraseBasedSpeechAnalyzer();
        this.missedWordsBank = [];
        this.attemptCounts = new Map();
        this.currentSession = null;
    }

    initializeSession(text, options = {}) {
        this.currentSession = {
            textContent: text,
            currentPosition: 0,
            phrasesCompleted: 0,
            totalAttempts: 0,
            phraseLength: options.phraseLength || 10,
            startTime: Date.now(),
            totalWords: text.split(' ').length
        };
        
        console.log('📝 Practice session initialized:', {
            totalWords: this.currentSession.totalWords,
            phraseLength: this.currentSession.phraseLength
        });
    }

    getPracticePhrase(startPos = null, phraseLength = null) {
        if (!this.currentSession) {
            throw new Error('No active practice session');
        }

        const position = startPos !== null ? startPos : this.currentSession.currentPosition;
        const length = phraseLength || this.currentSession.phraseLength;
        
        const words = this.currentSession.textContent.split(' ');
        const endPos = Math.min(position + length, words.length);
        const phraseWords = words.slice(position, endPos);
        const phraseText = phraseWords.join(' ');

        return {
            phraseText: phraseText,
            startPosition: position,
            endPosition: endPos,
            wordCount: phraseWords.length,
            isComplete: endPos >= words.length,
            progressPercentage: (endPos / words.length) * 100
        };
    }

    async processPhraseeSpeech(spokenText, expectedPhrase, context = "") {
        if (!this.currentSession) {
            throw new Error('No active practice session');
        }

        try {
            // Analyze the full phrase
            const analysis = await this.speechAnalyzer.analyzePhraseAccuracy(
                spokenText, expectedPhrase, context
            );

            if (!analysis.success) {
                return analysis;
            }

            this.currentSession.totalAttempts += 1;

            // Smart progression logic
            const accuracy = analysis.phraseAccuracy;
            const advancementResult = this._determineAdvancement(
                analysis.wordDifferences,
                accuracy,
                expectedPhrase
            );

            const phraseId = `${this.currentSession.currentPosition}_${expectedPhrase.substring(0, 20)}`;
            const attemptCount = this._incrementAttemptCount(phraseId);

            return {
                success: true,
                phraseCorrect: advancementResult.shouldAdvance,
                advancementType: advancementResult.type,
                accuracy: accuracy,
                similarityScore: analysis.similarityScore,
                highlightedHTML: analysis.highlightedHTML,
                wordDifferences: analysis.wordDifferences,
                missedWords: advancementResult.missedWords,
                aiFeedback: analysis.aiFeedback,
                needsRetry: advancementResult.needsRetry,
                perfectMatch: analysis.perfectMatch,
                spokenText: analysis.spokenText,
                expectedText: analysis.expectedText,
                progressMessage: advancementResult.message,
                attemptCount: attemptCount,
                sessionInfo: this._getSessionInfo()
            };

        } catch (error) {
            console.error('Phrase processing error:', error);
            return {
                success: false,
                error: error.message,
                phraseCorrect: false
            };
        }
    }

    _determineAdvancement(wordDifferences, accuracy, expectedPhrase) {
        const totalWords = expectedPhrase.split(' ').length;
        const correctWords = wordDifferences.filter(diff => diff.status === 'correct').length;
        const errorWords = wordDifferences.filter(diff => diff.status === 'error');

        // Perfect or near-perfect
        if (accuracy >= 95) {
            return {
                shouldAdvance: true,
                type: 'perfect',
                message: 'Perfect! Moving to next phrase.',
                missedWords: [],
                needsRetry: false
            };
        }

        // Very good - minor mistakes allowed
        if (accuracy >= 80) {
            return {
                shouldAdvance: true,
                type: 'good',
                message: `Great job! ${accuracy.toFixed(0)}% accuracy - continuing.`,
                missedWords: errorWords.map(diff => diff.expectedWord),
                needsRetry: false
            };
        }

        // Decent - but check if it's mostly correct with just a few key misses
        if (accuracy >= 60) {
            if (errorWords.length <= 2 && correctWords >= totalWords * 0.6) {
                return {
                    shouldAdvance: true,
                    type: 'partial_with_skips',
                    message: "Good progress! We'll review the missed words later.",
                    missedWords: errorWords.map(diff => diff.expectedWord),
                    needsRetry: false
                };
            } else {
                return {
                    shouldAdvance: false,
                    type: 'needs_improvement',
                    message: `Getting there! ${accuracy.toFixed(0)}% - try again focusing on the highlighted words.`,
                    missedWords: errorWords.map(diff => diff.expectedWord),
                    needsRetry: true
                };
            }
        }

        // Struggling - offer more chances but eventually allow skip
        if (accuracy >= 40) {
            return {
                shouldAdvance: false,
                type: 'struggling',
                message: `Keep trying! ${accuracy.toFixed(0)}% accuracy. Focus on the red highlighted words.`,
                missedWords: errorWords.map(diff => diff.expectedWord),
                needsRetry: true
            };
        }

        // Very low accuracy - definitely needs retry
        return {
            shouldAdvance: false,
            type: 'retry_needed',
            message: "Let's try that again. Focus on speaking clearly.",
            missedWords: errorWords.map(diff => diff.expectedWord),
            needsRetry: true
        };
    }

    advanceToNextPhrase() {
        if (!this.currentSession) return null;

        const currentPhrase = this.getPracticePhrase();
        
        if (currentPhrase.isComplete) {
            return null; // Session complete
        }

        this.currentSession.currentPosition = currentPhrase.endPosition;
        this.currentSession.phrasesCompleted += 1;

        return this.getPracticePhrase();
    }

    addMissedWords(words, phraseContext) {
        const timestamp = Date.now();
        
        for (const word of words) {
            const existingIndex = this.missedWordsBank.findIndex(item => item.word === word);
            
            if (existingIndex === -1) {
                this.missedWordsBank.push({
                    word: word,
                    context: phraseContext,
                    missedCount: 1,
                    timestamp: timestamp
                });
            } else {
                this.missedWordsBank[existingIndex].missedCount += 1;
                this.missedWordsBank[existingIndex].timestamp = timestamp;
            }
        }
    }

    getMissedWordsForReview() {
        // Sort by miss count and recency
        return [...this.missedWordsBank].sort((a, b) => {
            if (a.missedCount !== b.missedCount) {
                return b.missedCount - a.missedCount; // Higher miss count first
            }
            return b.timestamp - a.timestamp; // More recent first
        });
    }

    shouldAllowSkip(phraseId, attemptCount) {
        return attemptCount >= 3;
    }

    _incrementAttemptCount(phraseId) {
        const current = this.attemptCounts.get(phraseId) || 0;
        const newCount = current + 1;
        this.attemptCounts.set(phraseId, newCount);
        return newCount;
    }

    _getSessionInfo() {
        if (!this.currentSession) return null;

        return {
            phrasesCompleted: this.currentSession.phrasesCompleted,
            totalAttempts: this.currentSession.totalAttempts,
            currentPosition: this.currentSession.currentPosition,
            progressPercentage: (this.currentSession.currentPosition / this.currentSession.totalWords) * 100,
            missedWordsCount: this.missedWordsBank.length,
            sessionDuration: Date.now() - this.currentSession.startTime
        };
    }

    getSessionSummary() {
        const sessionInfo = this._getSessionInfo();
        if (!sessionInfo) return null;

        const accuracy = sessionInfo.totalAttempts > 0 
            ? (sessionInfo.phrasesCompleted / sessionInfo.totalAttempts) * 100 
            : 0;

        return {
            ...sessionInfo,
            overallAccuracy: accuracy,
            averageAttemptsPerPhrase: sessionInfo.phrasesCompleted > 0 
                ? sessionInfo.totalAttempts / sessionInfo.phrasesCompleted 
                : 0,
            missedWords: this.getMissedWordsForReview()
        };
    }
}

export { PhraseBasedSpeechAnalyzer, PhraseBasedPracticeEngine };