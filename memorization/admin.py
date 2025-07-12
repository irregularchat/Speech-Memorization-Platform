from django.contrib import admin
from .models import Text, TextSection, WordProgress, PracticeSession, UserTextProgress


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
    list_display = ['user', 'text', 'word', 'mastery_level', 'accuracy', 'total_attempts', 'next_review']
    list_filter = ['mastery_level', 'text', 'next_review']
    search_fields = ['user__username', 'text__title', 'word']
    readonly_fields = ['first_seen', 'last_seen']
    
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
