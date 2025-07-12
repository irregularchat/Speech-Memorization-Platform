from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class Text(models.Model):
    """Model for memorization texts (speeches, creeds, etc.)"""
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    description = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Suggested time limit in minutes")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_texts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    word_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-calculate word count
        self.word_count = len(self.content.split())
        super().save(*args, **kwargs)
    
    def get_tags_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []


class TextSection(models.Model):
    """Model for text sections (paragraphs, sentences, etc.)"""
    
    SECTION_TYPES = [
        ('paragraph', 'Paragraph'),
        ('sentence', 'Sentence'),
        ('verse', 'Verse'),
        ('custom', 'Custom'),
    ]
    
    text = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES, default='paragraph')
    content = models.TextField()
    order = models.PositiveIntegerField()
    start_position = models.PositiveIntegerField()  # Character position in original text
    end_position = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['text', 'order']
        unique_together = ['text', 'order']
        
    def __str__(self):
        return f"{self.text.title} - Section {self.order}"


class WordProgress(models.Model):
    """Model for tracking individual word memorization progress"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    word_text = models.CharField(max_length=100, default='')
    word_index = models.PositiveIntegerField(default=0)  # Position in text
    
    # Enhanced mastery tracking
    mastery_level = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    times_practiced = models.PositiveIntegerField(default=0)
    times_correct = models.PositiveIntegerField(default=0)
    
    # Spaced repetition data (SM-2 algorithm)
    ease_factor = models.FloatField(default=2.5)
    repetition = models.PositiveIntegerField(default=0)
    interval = models.PositiveIntegerField(default=1)  # Days until next review
    next_review = models.DateTimeField(auto_now_add=True)
    
    # Difficulty identification
    is_problem_word = models.BooleanField(default=False)
    consecutive_failures = models.PositiveIntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)  # seconds
    needs_review = models.BooleanField(default=True)
    
    # Timestamps
    first_seen = models.DateTimeField(auto_now_add=True)
    last_practiced = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'text', 'word_index']
        indexes = [
            models.Index(fields=['user', 'text']),
            models.Index(fields=['next_review']),
            models.Index(fields=['mastery_level']),
            models.Index(fields=['is_problem_word']),
            models.Index(fields=['needs_review']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.word_text} ({self.mastery_level:.2f})"
    
    @property
    def accuracy(self):
        """Calculate accuracy percentage"""
        if self.times_practiced == 0:
            return 0.0
        return (self.times_correct / self.times_practiced) * 100
    
    def update_mastery(self, success: bool, response_time: float = 0.0):
        """Update mastery level based on performance"""
        self.times_practiced += 1
        if success:
            self.times_correct += 1
            self.consecutive_failures = 0
            # Increase mastery
            improvement = 0.1 * (1.0 - self.mastery_level)
            self.mastery_level = min(self.mastery_level + improvement, 1.0)
        else:
            self.consecutive_failures += 1
            # Decrease mastery
            reduction = 0.05 + (self.consecutive_failures * 0.02)
            self.mastery_level = max(self.mastery_level - reduction, 0.0)
        
        # Update response time
        if response_time > 0:
            if self.average_response_time == 0:
                self.average_response_time = response_time
            else:
                self.average_response_time = (self.average_response_time * 0.8) + (response_time * 0.2)
        
        # Mark as problem word if struggling
        self.is_problem_word = (self.consecutive_failures >= 3 or 
                               self.mastery_level < 0.3 or 
                               self.average_response_time > 5.0)
        
        # Update spaced repetition
        self.needs_review = self.mastery_level < 0.8
        if self.mastery_level >= 0.8:
            self.ease_factor = min(self.ease_factor * 1.1, 3.0)
            self.interval = max(self.interval * self.ease_factor, 1)
        else:
            self.ease_factor = max(self.ease_factor * 0.9, 1.0)
            self.interval = 1
        
        from datetime import timedelta
        self.next_review = timezone.now() + timedelta(days=self.interval)
        self.save()


class PracticeSession(models.Model):
    """Model for tracking practice sessions"""
    
    SESSION_TYPES = [
        ('full_text', 'Full Text'),
        ('section', 'Section Practice'),
        ('fill_blanks', 'Fill in the Blanks'),
        ('speed_challenge', 'Speed Challenge'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='full_text')
    
    # Session data
    words_practiced = models.PositiveIntegerField(default=0)
    words_correct = models.PositiveIntegerField(default=0)
    accuracy_percentage = models.FloatField(default=0.0)
    duration_seconds = models.PositiveIntegerField(default=0)
    words_per_minute = models.PositiveIntegerField(default=150)
    mastery_level_used = models.PositiveIntegerField(default=0)
    
    # Audio data
    audio_file = models.FileField(upload_to='session_audio/', null=True, blank=True)
    transcription = models.TextField(blank=True)
    
    # Performance comparison
    differences = models.JSONField(default=list, blank=True)  # List of (expected, actual) word pairs
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.text.title} ({self.accuracy_percentage:.1f}%)"
    
    @property
    def error_count(self):
        """Calculate number of errors"""
        return self.words_practiced - self.words_correct
    
    @property
    def duration_minutes(self):
        """Get duration in minutes"""
        return self.duration_seconds / 60


class UserTextProgress(models.Model):
    """Model for tracking overall progress on a text"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    
    # Progress metrics
    overall_mastery_percentage = models.FloatField(default=0.0)
    words_mastered = models.PositiveIntegerField(default=0)
    total_practice_time = models.PositiveIntegerField(default=0)  # In seconds
    total_sessions = models.PositiveIntegerField(default=0)
    best_accuracy = models.FloatField(default=0.0)
    average_accuracy = models.FloatField(default=0.0)
    current_streak = models.PositiveIntegerField(default=0)
    
    # Preferences
    preferred_words_per_minute = models.PositiveIntegerField(default=150)
    preferred_session_duration = models.PositiveIntegerField(default=300)  # 5 minutes
    
    # Timestamps
    first_practiced = models.DateTimeField(auto_now_add=True)
    last_practiced = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'text']
        
    def __str__(self):
        return f"{self.user.username} - {self.text.title} ({self.overall_mastery_percentage:.1f}%)"
    
    @property
    def total_practice_time_minutes(self):
        """Get total practice time in minutes"""
        return self.total_practice_time / 60


class PracticePattern(models.Model):
    """Model for tracking practice patterns and identifying problem areas"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    
    # Pattern identification
    pattern_type = models.CharField(max_length=50, choices=[
        ('word_sequence', 'Word Sequence Difficulty'),
        ('sentence_start', 'Sentence Start Problems'),
        ('paragraph_transition', 'Paragraph Transition Issues'),
        ('long_words', 'Long Word Difficulty'),
        ('similar_words', 'Similar Word Confusion'),
        ('rapid_sequence', 'Rapid Sequence Challenge'),
    ])
    
    # Pattern details
    start_word_index = models.PositiveIntegerField()
    end_word_index = models.PositiveIntegerField()
    difficulty_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    frequency_encountered = models.PositiveIntegerField(default=1)
    
    # Context information
    context_words = models.JSONField(default=list)  # Surrounding words
    common_errors = models.JSONField(default=list)  # Common mistakes in this area
    
    # Performance tracking
    practice_attempts = models.PositiveIntegerField(default=0)
    successful_completions = models.PositiveIntegerField(default=0)
    average_time_spent = models.FloatField(default=0.0)  # seconds
    
    # Timestamps
    first_identified = models.DateTimeField(auto_now_add=True)
    last_practiced = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'text', 'pattern_type', 'start_word_index']
        indexes = [
            models.Index(fields=['user', 'text']),
            models.Index(fields=['difficulty_score']),
            models.Index(fields=['pattern_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.pattern_type} ({self.start_word_index}-{self.end_word_index})"
    
    @property
    def success_rate(self):
        """Calculate success rate for this pattern"""
        if self.practice_attempts == 0:
            return 0.0
        return (self.successful_completions / self.practice_attempts) * 100


class DelayedRecallSession(models.Model):
    """Model for delayed recall practice sessions"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    
    # Session configuration
    delay_minutes = models.PositiveIntegerField(default=15)  # How long to wait before recall
    reveal_percentage = models.FloatField(default=0.3)  # Percentage of words to reveal initially
    auto_hide_enabled = models.BooleanField(default=True)
    auto_hide_delay = models.PositiveIntegerField(default=5)  # seconds before auto-hide
    
    # Practice data
    words_to_recall = models.JSONField(default=list)  # Word indices to practice
    initial_study_time = models.PositiveIntegerField(default=0)  # seconds
    recall_attempts = models.PositiveIntegerField(default=0)
    successful_recalls = models.PositiveIntegerField(default=0)
    
    # Session state
    is_study_phase = models.BooleanField(default=True)
    is_waiting_phase = models.BooleanField(default=False)
    is_recall_phase = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    
    # Timestamps
    study_started_at = models.DateTimeField(auto_now_add=True)
    recall_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-study_started_at']
    
    def __str__(self):
        return f"{self.user.username} - Delayed Recall: {self.text.title}"
    
    @property
    def is_ready_for_recall(self):
        """Check if enough time has passed for recall phase"""
        if self.is_study_phase or not self.delay_minutes:
            return False
        
        from datetime import timedelta
        wait_until = self.study_started_at + timedelta(minutes=self.delay_minutes)
        return timezone.now() >= wait_until
    
    @property
    def recall_accuracy(self):
        """Calculate recall accuracy"""
        if self.recall_attempts == 0:
            return 0.0
        return (self.successful_recalls / self.recall_attempts) * 100


class WordRevealSession(models.Model):
    """Model for progressive word reveal practice"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    
    # Reveal configuration
    reveal_strategy = models.CharField(max_length=30, choices=[
        ('progressive', 'Progressive Reveal'),
        ('mastery_based', 'Mastery-Based Hiding'),
        ('random_hide', 'Random Word Hiding'),
        ('sentence_by_sentence', 'Sentence by Sentence'),
        ('difficulty_adaptive', 'Difficulty Adaptive'),
    ], default='progressive')
    
    reveal_percentage = models.FloatField(default=0.1)  # Start with 10% visible
    increment_percentage = models.FloatField(default=0.1)  # Increase by 10% each round
    
    # Auto-hide settings
    auto_hide_enabled = models.BooleanField(default=True)
    hide_delay_seconds = models.PositiveIntegerField(default=3)
    fade_duration_seconds = models.PositiveIntegerField(default=2)
    
    # Session state
    current_round = models.PositiveIntegerField(default=1)
    currently_visible_words = models.JSONField(default=list)  # Word indices currently visible
    mastered_words = models.JSONField(default=list)  # Word indices that are mastered
    problem_words = models.JSONField(default=list)  # Word indices that need more practice
    
    # Performance tracking
    total_rounds_completed = models.PositiveIntegerField(default=0)
    total_practice_time = models.PositiveIntegerField(default=0)  # seconds
    average_accuracy_per_round = models.JSONField(default=list)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    last_round_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - Word Reveal: {self.text.title} (Round {self.current_round})"
    
    def calculate_next_reveal_set(self):
        """Calculate which words to reveal in the next round"""
        words = self.text.content.split()
        total_words = len(words)
        
        if self.reveal_strategy == 'progressive':
            # Progressive reveal: show more words each round
            target_visible = min(
                int(total_words * (self.reveal_percentage + 
                                  (self.current_round - 1) * self.increment_percentage)),
                total_words
            )
            
            # Prioritize words that aren't mastered yet
            non_mastered = [i for i in range(total_words) if i not in self.mastered_words]
            visible_words = self.currently_visible_words + non_mastered[:target_visible - len(self.currently_visible_words)]
            
        elif self.reveal_strategy == 'mastery_based':
            # Hide well-mastered words, show struggling words
            user_progress = WordProgress.objects.filter(
                user=self.user, text=self.text
            ).values('word_index', 'mastery_level')
            
            mastery_map = {wp['word_index']: wp['mastery_level'] for wp in user_progress}
            
            visible_words = []
            for i in range(total_words):
                mastery = mastery_map.get(i, 0.0)
                # Show words with low mastery or problem words
                if mastery < 0.7 or i in self.problem_words:
                    visible_words.append(i)
                elif i in self.currently_visible_words and mastery < 0.9:
                    # Keep showing words that aren't fully mastered
                    visible_words.append(i)
        
        else:
            # Default to progressive
            visible_words = self.currently_visible_words
        
        return visible_words[:int(total_words * 0.8)]  # Cap at 80% visible
