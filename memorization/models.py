from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
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
    word = models.CharField(max_length=100)
    word_position = models.PositiveIntegerField()  # Position in text
    
    # Spaced repetition data (SM-2 algorithm)
    easiness_factor = models.FloatField(default=2.5)
    repetition = models.PositiveIntegerField(default=0)
    interval = models.PositiveIntegerField(default=1)  # Days until next review
    next_review = models.DateTimeField()
    
    # Performance tracking
    total_attempts = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)
    mastery_level = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Timestamps
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'text', 'word', 'word_position']
        indexes = [
            models.Index(fields=['user', 'text']),
            models.Index(fields=['next_review']),
            models.Index(fields=['mastery_level']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.word} ({self.mastery_level}/5)"
    
    @property
    def accuracy(self):
        """Calculate accuracy percentage"""
        if self.total_attempts == 0:
            return 0.0
        return (self.correct_attempts / self.total_attempts) * 100


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
