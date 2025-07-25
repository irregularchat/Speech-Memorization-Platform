/**
 * Gamification System for Speech Memorization
 * Adds achievements, streaks, levels, and motivational elements
 */

class GamificationSystem {
    constructor() {
        this.achievements = [];
        this.currentStreak = 0;
        this.totalPracticeTime = 0;
        this.level = 1;
        this.experience = 0;
        this.badges = [];
        
        this.initializeSystem();
        this.setupEventListeners();
    }
    
    initializeSystem() {
        this.loadUserProgress();
        this.createProgressInterface();
        this.setupAchievements();
    }
    
    createProgressInterface() {
        // Create floating progress widget
        const progressWidget = document.createElement('div');
        progressWidget.className = 'gamification-widget';
        progressWidget.innerHTML = `
            <div class="widget-header" onclick="this.parentElement.classList.toggle('expanded')">
                <div class="level-info">
                    <span class="level-badge">Level ${this.level}</span>
                    <div class="xp-bar">
                        <div class="xp-fill" style="width: ${this.getXPProgress()}%"></div>
                    </div>
                </div>
                <div class="streak-info">
                    <i class="fas fa-fire"></i>
                    <span class="streak-count">${this.currentStreak}</span>
                </div>
            </div>
            
            <div class="widget-content">
                <div class="daily-goal">
                    <h4>Today's Goal</h4>
                    <div class="goal-progress">
                        <div class="goal-icon">🎯</div>
                        <div class="goal-text">Practice 3 texts</div>
                        <div class="goal-bar">
                            <div class="goal-fill" style="width: 33%"></div>
                        </div>
                    </div>
                </div>
                
                <div class="recent-achievements">
                    <h4>Recent Achievements</h4>
                    <div class="achievement-list" id="recent-achievements">
                        <!-- Populated dynamically -->
                    </div>
                </div>
                
                <div class="leaderboard-preview">
                    <h4>This Week's Leaders</h4>
                    <div class="leader-list">
                        <div class="leader-item me">
                            <span class="rank">#5</span>
                            <span class="name">You</span>
                            <span class="score">1,250 XP</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        progressWidget.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 280px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            z-index: 1000;
            transition: all 0.3s ease;
            max-height: 80px;
            overflow: hidden;
        `;
        
        document.body.appendChild(progressWidget);
        this.progressWidget = progressWidget;
    }
    
    setupAchievements() {
        this.achievementTypes = [
            {
                id: 'first_speech',
                title: 'First Steps',
                description: 'Complete your first speech',
                icon: '🎤',
                xp: 100,
                condition: (stats) => stats.speechesCompleted >= 1
            },
            {
                id: 'perfect_delivery',
                title: 'Perfect Delivery',
                description: 'Complete a speech with 95%+ accuracy',
                icon: '⭐',
                xp: 200,
                condition: (stats) => stats.bestAccuracy >= 0.95
            },
            {
                id: 'streak_master',
                title: 'Streak Master',
                description: 'Practice for 7 days in a row',
                icon: '🔥',
                xp: 300,
                condition: (stats) => stats.longestStreak >= 7
            },
            {
                id: 'speed_demon',
                title: 'Speed Demon',
                description: 'Complete a speech in under target time',
                icon: '⚡',
                xp: 150,
                condition: (stats) => stats.fastestCompletion > 0
            },
            {
                id: 'dedication',
                title: 'Dedication',
                description: 'Practice for 30 total hours',
                icon: '🏆',
                xp: 500,
                condition: (stats) => stats.totalHours >= 30
            },
            {
                id: 'eloquent',
                title: 'Eloquent Speaker',
                description: 'Maintain 90%+ accuracy for 10 speeches',
                icon: '🎭',
                xp: 400,
                condition: (stats) => stats.consistentAccuracy >= 10
            }
        ];
    }
    
    checkAchievements(userStats) {
        const newAchievements = [];
        
        this.achievementTypes.forEach(achievement => {
            if (!this.achievements.includes(achievement.id) && 
                achievement.condition(userStats)) {
                
                this.achievements.push(achievement.id);
                newAchievements.push(achievement);
                this.awardXP(achievement.xp);
            }
        });
        
        if (newAchievements.length > 0) {
            this.showAchievementNotification(newAchievements);
        }
    }
    
    showAchievementNotification(achievements) {
        achievements.forEach((achievement, index) => {
            setTimeout(() => {
                this.displayAchievement(achievement);
            }, index * 1000);
        });
    }
    
    displayAchievement(achievement) {
        const notification = document.createElement('div');
        notification.className = 'achievement-notification';
        notification.innerHTML = `
            <div class="achievement-content">
                <div class="achievement-icon">${achievement.icon}</div>
                <div class="achievement-text">
                    <h3>Achievement Unlocked!</h3>
                    <h4>${achievement.title}</h4>
                    <p>${achievement.description}</p>
                    <div class="xp-reward">+${achievement.xp} XP</div>
                </div>
            </div>
            <button class="achievement-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            color: #333;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: achievementPop 0.5s ease-out;
            max-width: 400px;
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'achievementFadeOut 0.3s ease-in forwards';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
        
        // Play achievement sound
        this.playAchievementSound();
        
        // Confetti effect
        this.triggerConfetti();
    }
    
    awardXP(amount) {
        this.experience += amount;
        
        // Check for level up
        const newLevel = Math.floor(this.experience / 1000) + 1;
        if (newLevel > this.level) {
            this.level = newLevel;
            this.showLevelUpNotification();
        }
        
        this.updateProgressDisplay();
        this.saveProgress();
    }
    
    showLevelUpNotification() {
        const notification = document.createElement('div');
        notification.className = 'level-up-notification';
        notification.innerHTML = `
            <div class="level-up-content">
                <div class="level-up-icon">🎉</div>
                <h2>Level Up!</h2>
                <div class="level-display">Level ${this.level}</div>
                <p>You're becoming a master speaker!</p>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            z-index: 10001;
            animation: levelUpPulse 1s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
        this.playLevelUpSound();
    }
    
    updateStreakSystem() {
        const today = new Date().toDateString();
        const lastPractice = localStorage.getItem('lastPracticeDate');
        
        if (lastPractice === today) {
            // Already practiced today
            return;
        }
        
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        
        if (lastPractice === yesterday.toDateString()) {
            // Continuing streak
            this.currentStreak++;
        } else if (lastPractice !== today) {
            // Streak broken
            this.currentStreak = 1;
        }
        
        localStorage.setItem('lastPracticeDate', today);
        localStorage.setItem('currentStreak', this.currentStreak.toString());
        
        this.updateProgressDisplay();
    }
    
    getXPProgress() {
        const xpForCurrentLevel = (this.level - 1) * 1000;
        const xpIntoCurrentLevel = this.experience - xpForCurrentLevel;
        return (xpIntoCurrentLevel / 1000) * 100;
    }
    
    updateProgressDisplay() {
        if (this.progressWidget) {
            const levelBadge = this.progressWidget.querySelector('.level-badge');
            const xpFill = this.progressWidget.querySelector('.xp-fill');
            const streakCount = this.progressWidget.querySelector('.streak-count');
            
            if (levelBadge) levelBadge.textContent = `Level ${this.level}`;
            if (xpFill) xpFill.style.width = `${this.getXPProgress()}%`;
            if (streakCount) streakCount.textContent = this.currentStreak;
        }
    }
    
    playAchievementSound() {
        // Play success sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime); // C5
        oscillator.frequency.setValueAtTime(659.25, audioContext.currentTime + 0.1); // E5
        oscillator.frequency.setValueAtTime(783.99, audioContext.currentTime + 0.2); // G5
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    }
    
    playLevelUpSound() {
        // Play level up fanfare
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const frequencies = [261.63, 329.63, 392.00, 523.25]; // C-E-G-C major chord
        
        frequencies.forEach((freq, index) => {
            setTimeout(() => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(freq, audioContext.currentTime);
                gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.3);
            }, index * 100);
        });
    }
    
    triggerConfetti() {
        // Simple confetti animation
        for (let i = 0; i < 50; i++) {
            setTimeout(() => {
                const confetti = document.createElement('div');
                confetti.style.cssText = `
                    position: fixed;
                    width: 10px;
                    height: 10px;
                    background: ${['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24'][Math.floor(Math.random() * 5)]};
                    top: -10px;
                    left: ${Math.random() * 100}vw;
                    z-index: 10002;
                    animation: confettiFall 3s linear forwards;
                    border-radius: 50%;
                `;
                
                document.body.appendChild(confetti);
                setTimeout(() => confetti.remove(), 3000);
            }, Math.random() * 1000);
        }
    }
    
    saveProgress() {
        const progressData = {
            level: this.level,
            experience: this.experience,
            achievements: this.achievements,
            currentStreak: this.currentStreak,
            totalPracticeTime: this.totalPracticeTime
        };
        
        localStorage.setItem('gamificationProgress', JSON.stringify(progressData));
    }
    
    loadUserProgress() {
        const saved = localStorage.getItem('gamificationProgress');
        if (saved) {
            const data = JSON.parse(saved);
            this.level = data.level || 1;
            this.experience = data.experience || 0;
            this.achievements = data.achievements || [];
            this.currentStreak = data.currentStreak || 0;
            this.totalPracticeTime = data.totalPracticeTime || 0;
        }
    }
    
    setupEventListeners() {
        // Listen for practice completion events
        document.addEventListener('practiceCompleted', (event) => {
            const stats = event.detail;
            this.updateStreakSystem();
            this.awardXP(stats.accuracy * 100); // XP based on accuracy
            this.checkAchievements(stats);
        });
        
        // Listen for speech recognition events
        document.addEventListener('speechRecognized', (event) => {
            this.awardXP(5); // Small XP for each recognition
        });
    }
}

// CSS for gamification elements
const gamificationStyles = `
<style>
@keyframes achievementPop {
    0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0; }
    50% { transform: translate(-50%, -50%) scale(1.1); }
    100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
}

@keyframes achievementFadeOut {
    to { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
}

@keyframes levelUpPulse {
    0%, 100% { transform: translate(-50%, -50%) scale(1); }
    50% { transform: translate(-50%, -50%) scale(1.05); }
}

@keyframes confettiFall {
    to { 
        transform: translateY(100vh) rotate(720deg);
        opacity: 0;
    }
}

.gamification-widget {
    cursor: pointer;
}

.gamification-widget.expanded {
    max-height: 400px;
}

.widget-header {
    padding: 15px;
    border-bottom: 1px solid rgba(0,0,0,0.1);
}

.level-badge {
    background: linear-gradient(135deg, #ffd700, #ffed4e);
    color: #333;
    padding: 4px 12px;
    border-radius: 15px;
    font-weight: bold;
    font-size: 0.9rem;
}

.xp-bar {
    height: 6px;
    background: rgba(0,0,0,0.1);
    border-radius: 3px;
    margin-top: 8px;
    overflow: hidden;
}

.xp-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 3px;
    transition: width 0.5s ease;
}

.streak-info {
    display: flex;
    align-items: center;
    gap: 5px;
    margin-top: 10px;
}

.streak-info i {
    color: #ff6b35;
}

.widget-content {
    padding: 20px;
}

.daily-goal {
    margin-bottom: 20px;
}

.goal-progress {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 10px;
}

.goal-bar {
    flex: 1;
    height: 8px;
    background: rgba(0,0,0,0.1);
    border-radius: 4px;
    overflow: hidden;
}

.goal-fill {
    height: 100%;
    background: #28a745;
    border-radius: 4px;
    transition: width 0.5s ease;
}

.achievement-notification {
    border: 3px solid #fff;
}

.achievement-content {
    display: flex;
    align-items: center;
    gap: 20px;
}

.achievement-icon {
    font-size: 60px;
}

.achievement-text h3 {
    margin: 0 0 5px 0;
    font-size: 1.2rem;
}

.achievement-text h4 {
    margin: 0 0 8px 0;
    font-size: 1.4rem;
    font-weight: bold;
}

.achievement-text p {
    margin: 0 0 10px 0;
    opacity: 0.8;
}

.xp-reward {
    background: rgba(0,0,0,0.2);
    padding: 4px 8px;
    border-radius: 10px;
    font-weight: bold;
}

.achievement-close {
    position: absolute;
    top: 10px;
    right: 15px;
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #333;
}

.level-up-notification {
    text-align: center;
}

.level-up-icon {
    font-size: 80px;
    margin-bottom: 20px;
}

.level-display {
    font-size: 3rem;
    font-weight: bold;
    margin: 15px 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', gamificationStyles);

// Initialize gamification system
window.gamificationSystem = new GamificationSystem();

// Export for global use
window.GamificationSystem = GamificationSystem;