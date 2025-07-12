from django.db import models
from django.contrib.auth.models import User
from memorization.models import Text, PracticeSession


class UserAnalytics(models.Model):
    """Model for storing user analytics and performance metrics"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    
    # Overall statistics
    total_sessions = models.PositiveIntegerField(default=0)
    total_practice_time = models.PositiveIntegerField(default=0)  # In seconds
    total_words_practiced = models.PositiveIntegerField(default=0)
    total_words_correct = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    average_accuracy = models.FloatField(default=0.0)
    best_accuracy = models.FloatField(default=0.0)
    improvement_rate = models.FloatField(default=0.0)  # Percentage improvement
    
    # Streak tracking
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_practice_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} Analytics"
    
    @property
    def overall_accuracy(self):
        """Calculate overall accuracy percentage"""
        if self.total_words_practiced == 0:
            return 0.0
        return (self.total_words_correct / self.total_words_practiced) * 100


class DailyStats(models.Model):
    """Model for tracking daily performance statistics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    
    # Daily metrics
    sessions_count = models.PositiveIntegerField(default=0)
    practice_time = models.PositiveIntegerField(default=0)  # In seconds
    words_practiced = models.PositiveIntegerField(default=0)
    words_correct = models.PositiveIntegerField(default=0)
    average_accuracy = models.FloatField(default=0.0)
    
    # Text-specific data
    texts_practiced = models.ManyToManyField(Text, blank=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class WeeklyStats(models.Model):
    """Model for tracking weekly performance statistics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    week = models.PositiveIntegerField()  # Week number (1-53)
    
    # Weekly metrics
    sessions_count = models.PositiveIntegerField(default=0)
    practice_time = models.PositiveIntegerField(default=0)  # In seconds
    words_practiced = models.PositiveIntegerField(default=0)
    words_correct = models.PositiveIntegerField(default=0)
    average_accuracy = models.FloatField(default=0.0)
    days_practiced = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'year', 'week']
        ordering = ['-year', '-week']
        
    def __str__(self):
        return f"{self.user.username} - {self.year} Week {self.week}"


class MonthlyStats(models.Model):
    """Model for tracking monthly performance statistics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()  # Month number (1-12)
    
    # Monthly metrics
    sessions_count = models.PositiveIntegerField(default=0)
    practice_time = models.PositiveIntegerField(default=0)  # In seconds
    words_practiced = models.PositiveIntegerField(default=0)
    words_correct = models.PositiveIntegerField(default=0)
    average_accuracy = models.FloatField(default=0.0)
    days_practiced = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'year', 'month']
        ordering = ['-year', '-month']
        
    def __str__(self):
        return f"{self.user.username} - {self.year}/{self.month:02d}"


class TextAnalytics(models.Model):
    """Model for tracking text-specific analytics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    
    # Text-specific metrics
    sessions_count = models.PositiveIntegerField(default=0)
    total_practice_time = models.PositiveIntegerField(default=0)  # In seconds
    words_practiced = models.PositiveIntegerField(default=0)
    words_correct = models.PositiveIntegerField(default=0)
    average_accuracy = models.FloatField(default=0.0)
    best_accuracy = models.FloatField(default=0.0)
    
    # Progress tracking
    first_practice_date = models.DateTimeField(auto_now_add=True)
    last_practice_date = models.DateTimeField(auto_now=True)
    mastery_percentage = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['user', 'text']
        
    def __str__(self):
        return f"{self.user.username} - {self.text.title}"


class PerformanceTrend(models.Model):
    """Model for tracking performance trends over time"""
    
    TREND_TYPES = [
        ('accuracy', 'Accuracy'),
        ('speed', 'Speed'),
        ('consistency', 'Consistency'),
        ('mastery', 'Mastery'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trend_type = models.CharField(max_length=20, choices=TREND_TYPES)
    date = models.DateField()
    value = models.FloatField()
    
    # Optional context
    text = models.ForeignKey(Text, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.user.username} - {self.trend_type} ({self.value})"


class Achievement(models.Model):
    """Model for tracking user achievements and milestones"""
    
    ACHIEVEMENT_TYPES = [
        ('streak', 'Practice Streak'),
        ('accuracy', 'Accuracy Milestone'),
        ('time', 'Practice Time'),
        ('mastery', 'Text Mastery'),
        ('sessions', 'Session Count'),
        ('words', 'Words Practiced'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    threshold_value = models.FloatField()  # The value needed to achieve this
    achieved_value = models.FloatField()   # The actual value when achieved
    
    # Optional context
    text = models.ForeignKey(Text, on_delete=models.CASCADE, null=True, blank=True)
    
    # Timestamps
    achieved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'achievement_type', 'threshold_value']
        ordering = ['-achieved_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.title}"
