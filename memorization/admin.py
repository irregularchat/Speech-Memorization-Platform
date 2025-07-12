from django.contrib import admin
from .models import (Text, TextSection, WordProgress, PracticeSession, UserTextProgress,
                     PracticePattern, DelayedRecallSession, WordRevealSession)


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'word_count', 'created_by', 'is_public', 'created_at']
    list_filter = ['difficulty', 'is_public', 'created_at']
    search_fields = ['title', 'description', 'tags']
    readonly_fields = ['word_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'description')
        }),
        ('Classification', {
            'fields': ('difficulty', 'tags', 'time_limit')
        }),
        ('Publishing', {
            'fields': ('created_by', 'is_public')
        }),
        ('Metadata', {
            'fields': ('word_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(TextSection)
class TextSectionAdmin(admin.ModelAdmin):
    list_display = ['text', 'section_type', 'order', 'start_position', 'end_position']
    list_filter = ['section_type', 'text']
    search_fields = ['text__title', 'content']


@admin.register(WordProgress)
class WordProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'word_text', 'mastery_level', 'accuracy', 'times_practiced', 'is_problem_word', 'next_review']
    list_filter = ['mastery_level', 'text', 'is_problem_word', 'needs_review', 'next_review']
    search_fields = ['user__username', 'text__title', 'word_text']
    readonly_fields = ['first_seen', 'last_practiced']
    
    def accuracy(self, obj):
        return f"{obj.accuracy:.1f}%"
    accuracy.short_description = 'Accuracy'


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'session_type', 'accuracy_percentage', 'words_practiced', 'started_at', 'completed_at']
    list_filter = ['session_type', 'started_at', 'completed_at']
    search_fields = ['user__username', 'text__title']
    readonly_fields = ['started_at', 'completed_at', 'error_count', 'duration_minutes']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'text', 'session_type')
        }),
        ('Performance', {
            'fields': ('words_practiced', 'words_correct', 'accuracy_percentage', 'duration_seconds', 'words_per_minute', 'mastery_level_used')
        }),
        ('Audio Data', {
            'fields': ('audio_file', 'transcription'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('differences', 'error_count', 'duration_minutes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserTextProgress)
class UserTextProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'overall_mastery_percentage', 'words_mastered', 'total_sessions', 'best_accuracy', 'last_practiced']
    list_filter = ['text', 'last_practiced']
    search_fields = ['user__username', 'text__title']
    readonly_fields = ['first_practiced', 'last_practiced']


@admin.register(PracticePattern)
class PracticePatternAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'pattern_type', 'start_word_index', 'end_word_index', 'difficulty_score', 'success_rate', 'frequency_encountered']
    list_filter = ['pattern_type', 'difficulty_score', 'text']
    search_fields = ['user__username', 'text__title']
    readonly_fields = ['first_identified', 'last_practiced']
    
    def success_rate(self, obj):
        return f"{obj.success_rate:.1f}%"
    success_rate.short_description = 'Success Rate'


@admin.register(DelayedRecallSession)
class DelayedRecallSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'delay_minutes', 'is_study_phase', 'is_recall_phase', 'recall_accuracy', 'study_started_at']
    list_filter = ['delay_minutes', 'is_study_phase', 'is_recall_phase', 'is_completed']
    search_fields = ['user__username', 'text__title']
    readonly_fields = ['study_started_at', 'recall_started_at', 'completed_at', 'is_ready_for_recall']
    
    def recall_accuracy(self, obj):
        return f"{obj.recall_accuracy:.1f}%"
    recall_accuracy.short_description = 'Recall Accuracy'


@admin.register(WordRevealSession)
class WordRevealSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'reveal_strategy', 'current_round', 'reveal_percentage', 'total_rounds_completed', 'started_at']
    list_filter = ['reveal_strategy', 'auto_hide_enabled', 'completed_at']
    search_fields = ['user__username', 'text__title']
    readonly_fields = ['started_at', 'last_round_at', 'completed_at']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'text', 'reveal_strategy')
        }),
        ('Configuration', {
            'fields': ('reveal_percentage', 'increment_percentage', 'auto_hide_enabled', 'hide_delay_seconds', 'fade_duration_seconds')
        }),
        ('Current State', {
            'fields': ('current_round', 'currently_visible_words', 'mastered_words', 'problem_words')
        }),
        ('Performance', {
            'fields': ('total_rounds_completed', 'total_practice_time', 'average_accuracy_per_round'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'last_round_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
