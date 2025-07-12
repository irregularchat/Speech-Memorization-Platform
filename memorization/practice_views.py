from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
import json
import uuid

from .models import Text, PracticeSession, WordProgress, UserTextProgress
from .practice_service import AdaptivePracticeEngine


def practice_text_enhanced(request, text_id):
    """Enhanced practice view with adaptive word-level features"""
    text = get_object_or_404(Text, id=text_id)
    
    # Check permissions
    if not text.is_public and text.created_by != request.user:
        return render(request, 'core/error.html', {
            'error_message': 'You do not have permission to practice this text.',
            'redirect_url': '/texts/'
        })
    
    # Get or create user progress
    user_progress = None
    if request.user.is_authenticated:
        user_progress, created = UserTextProgress.objects.get_or_create(
            user=request.user,
            text=text
        )
    
    # Get word-level statistics
    word_stats = _get_word_statistics(text, request.user)
    
    # Initialize practice engine
    practice_engine = AdaptivePracticeEngine(text, request.user)
    
    context = {
        'text': text,
        'user_progress': user_progress,
        'word_stats': word_stats,
        'initial_display_text': practice_engine.get_display_text(),
        'total_words': len(practice_engine.words),
        'mastery_threshold': practice_engine.mastery_threshold * 100,
    }
    
    return render(request, 'memorization/practice_enhanced.html', context)


@login_required
@require_http_methods(["POST"])
def start_adaptive_session(request):
    """Start a new adaptive practice session"""
    try:
        data = json.loads(request.body)
        text_id = data.get('text_id')
        session_type = data.get('session_type', 'adaptive')
        
        text = get_object_or_404(Text, id=text_id)
        
        # Create practice session
        practice_session = PracticeSession.objects.create(
            user=request.user,
            text=text,
            session_type=session_type,
            started_at=timezone.now()
        )
        
        # Initialize practice engine and store in cache
        practice_engine = AdaptivePracticeEngine(text, request.user)
        practice_engine.practice_session = practice_session
        
        # Store session in cache with unique key
        session_key = f"practice_session_{practice_session.id}"
        cache.set(session_key, practice_engine, timeout=3600)  # 1 hour timeout
        
        # Start with first word
        result = practice_engine.advance_to_word(0)
        result['session_id'] = practice_session.id
        result['session_key'] = session_key
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def process_speech_input(request):
    """Process speech input and update practice state"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        spoken_text = data.get('spoken_text', '')
        
        # Get practice engine from cache
        practice_engine = cache.get(session_key)
        if not practice_engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Process the speech input
        result = practice_engine.process_speech_input(spoken_text)
        
        # Update cache
        cache.set(session_key, practice_engine, timeout=3600)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def request_hint(request):
    """Request a hint for the current word"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        hint_type = data.get('hint_type', 'auto')  # auto, letter, partial, full
        
        # Get practice engine from cache
        practice_engine = cache.get(session_key)
        if not practice_engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Apply hint
        result = practice_engine.apply_hint(hint_type)
        
        # Update cache
        cache.set(session_key, practice_engine, timeout=3600)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def advance_word(request):
    """Manually advance to the next word"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        # Get practice engine from cache
        practice_engine = cache.get(session_key)
        if not practice_engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Advance to next word
        result = practice_engine.advance_to_word(practice_engine.current_word_index + 1)
        
        # Update cache
        cache.set(session_key, practice_engine, timeout=3600)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def check_word_timing(request):
    """Check if current word needs hints based on timing"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        # Get practice engine from cache
        practice_engine = cache.get(session_key)
        if not practice_engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Check timing
        result = practice_engine.check_word_timing()
        
        # Update cache
        cache.set(session_key, practice_engine, timeout=3600)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def complete_adaptive_session(request):
    """Complete the adaptive practice session"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        # Get practice engine from cache
        practice_engine = cache.get(session_key)
        if not practice_engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Complete session
        result = practice_engine._complete_session()
        
        # Update database session record
        if practice_engine.practice_session:
            session = practice_engine.practice_session
            session.completed_at = timezone.now()
            session.accuracy = result['statistics']['accuracy']
            session.words_per_minute = result['statistics']['words_per_minute']
            session.total_words = result['statistics']['total_words']
            session.correct_words = result['statistics']['completed_words']
            session.session_data = {
                'hints_used': result['statistics']['hints_used'],
                'total_attempts': result['statistics']['total_attempts']
            }
            session.save()
        
        # Clear cache
        cache.delete(session_key)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def get_session_state(request):
    """Get current session state"""
    try:
        session_key = request.GET.get('session_key')
        
        # Get practice engine from cache
        practice_engine = cache.get(session_key)
        if not practice_engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Get current state
        result = practice_engine.get_session_state()
        result['success'] = True
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def _get_word_statistics(text: Text, user) -> dict:
    """Get word-level statistics for the text"""
    if not user.is_authenticated:
        return {
            'total_words': len(text.content.split()),
            'mastered_words': 0,
            'average_mastery': 0.0,
            'words_due_review': 0,
            'tracked_words': 0
        }
    
    # Get word progress data
    word_progress_entries = WordProgress.objects.filter(
        user=user,
        text=text
    )
    
    total_words = len(text.content.split())
    tracked_words = word_progress_entries.count()
    mastered_words = word_progress_entries.filter(mastery_level__gte=0.8).count()
    
    if tracked_words > 0:
        average_mastery = sum(wp.mastery_level for wp in word_progress_entries) / tracked_words * 100
        words_due_review = word_progress_entries.filter(
            mastery_level__lt=0.6,
            last_practiced__lt=timezone.now() - timezone.timedelta(days=1)
        ).count()
    else:
        average_mastery = 0.0
        words_due_review = 0
    
    return {
        'total_words': total_words,
        'mastered_words': mastered_words,
        'average_mastery': average_mastery,
        'words_due_review': words_due_review,
        'tracked_words': tracked_words
    }