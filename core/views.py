from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from memorization.models import Text, PracticeSession, UserTextProgress
from memorization.services import SpacedRepetitionService, PracticeSessionService
from analytics.models import UserAnalytics


def home(request):
    """Home page view - main memorization interface."""
    if not request.user.is_authenticated:
        # Show public landing page
        texts = Text.objects.filter(is_public=True).order_by('-created_at')[:5]
        context = {
            'texts': texts,
            'is_public': True,
        }
        return render(request, 'core/home.html', context)
    
    # Get available texts
    texts = Text.objects.filter(is_public=True).order_by('-created_at')
    user_texts = Text.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Get user's recent sessions
    recent_sessions = PracticeSession.objects.filter(
        user=request.user
    ).order_by('-started_at')[:5]
    
    # Get user analytics
    user_analytics, created = UserAnalytics.objects.get_or_create(user=request.user)
    
    context = {
        'texts': texts,
        'user_texts': user_texts,
        'recent_sessions': recent_sessions,
        'user_analytics': user_analytics,
    }
    
    return render(request, 'core/home.html', context)


@login_required
def practice_text(request, text_id):
    """Practice page for a specific text."""
    text = get_object_or_404(Text, id=text_id)
    
    # Check if user has access (public texts or own texts)
    if not text.is_public and text.created_by != request.user:
        messages.error(request, "You don't have access to this text.")
        return redirect('home')
    
    # Get user's progress on this text
    user_progress, created = UserTextProgress.objects.get_or_create(
        user=request.user,
        text=text
    )
    
    # Get spaced repetition statistics
    sr_service = SpacedRepetitionService(request.user)
    text_stats = sr_service.get_text_statistics(text)
    
    # Get mastery level from session or use default
    mastery_level = request.session.get('mastery_level', 0)
    
    # Apply spaced repetition to get display text
    display_text = sr_service.apply_spaced_repetition(text, mastery_level)
    
    context = {
        'text': text,
        'display_text': display_text,
        'user_progress': user_progress,
        'text_stats': text_stats,
        'mastery_level': mastery_level,
    }
    
    return render(request, 'core/practice.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_mastery_level(request):
    """AJAX endpoint to update mastery level."""
    try:
        data = json.loads(request.body)
        mastery_level = int(data.get('mastery_level', 0))
        text_id = int(data.get('text_id'))
        
        # Validate mastery level
        if not 0 <= mastery_level <= 100:
            return JsonResponse({'error': 'Invalid mastery level'}, status=400)
        
        # Store in session
        request.session['mastery_level'] = mastery_level
        
        # Get updated display text
        text = get_object_or_404(Text, id=text_id)
        sr_service = SpacedRepetitionService(request.user)
        display_text = sr_service.apply_spaced_repetition(text, mastery_level)
        
        return JsonResponse({
            'success': True,
            'display_text': display_text,
            'mastery_level': mastery_level
        })
        
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return JsonResponse({'error': 'Invalid request data'}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def start_practice_session(request):
    """Start a new practice session."""
    try:
        data = json.loads(request.body)
        text_id = int(data.get('text_id'))
        session_type = data.get('session_type', 'full_text')
        
        text = get_object_or_404(Text, id=text_id)
        
        # Create practice session
        session_service = PracticeSessionService(request.user)
        session = session_service.create_session(text, session_type)
        
        # Store session ID in session
        request.session['current_session_id'] = session.id
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'text_content': text.content
        })
        
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return JsonResponse({'error': 'Invalid request data'}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def complete_practice_session(request):
    """Complete a practice session with results."""
    try:
        data = json.loads(request.body)
        session_id = int(data.get('session_id'))
        transcribed_text = data.get('transcribed_text', '')
        words_per_minute = int(data.get('words_per_minute', 150))
        mastery_level_used = int(data.get('mastery_level_used', 0))
        duration_seconds = int(data.get('duration_seconds', 0))
        
        # Get session
        session = get_object_or_404(PracticeSession, id=session_id, user=request.user)
        
        # Complete session
        session_service = PracticeSessionService(request.user)
        completed_session = session_service.complete_session(
            session,
            transcribed_text,
            words_per_minute,
            mastery_level_used,
            duration_seconds
        )
        
        # Clear session
        if 'current_session_id' in request.session:
            del request.session['current_session_id']
        
        return JsonResponse({
            'success': True,
            'accuracy': completed_session.accuracy_percentage,
            'errors': completed_session.error_count,
            'words_practiced': completed_session.words_practiced,
            'differences': completed_session.differences
        })
        
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return JsonResponse({'error': 'Invalid request data'}, status=400)


@login_required
def analytics(request):
    """Analytics dashboard view."""
    # Get user analytics
    user_analytics, created = UserAnalytics.objects.get_or_create(user=request.user)
    
    # Get recent sessions for trend analysis
    recent_sessions = PracticeSession.objects.filter(
        user=request.user,
        completed_at__isnull=False
    ).order_by('-completed_at')[:30]
    
    # Get text-specific progress
    text_progresses = UserTextProgress.objects.filter(user=request.user).order_by('-last_practiced')
    
    # Prepare data for charts
    accuracy_trend = [session.accuracy_percentage for session in recent_sessions]
    session_dates = [session.completed_at.strftime('%Y-%m-%d') for session in recent_sessions]
    
    context = {
        'user_analytics': user_analytics,
        'recent_sessions': recent_sessions,
        'text_progresses': text_progresses,
        'accuracy_trend': json.dumps(accuracy_trend[::-1]),  # Reverse for chronological order
        'session_dates': json.dumps(session_dates[::-1]),
    }
    
    return render(request, 'core/analytics.html', context)


@login_required
def text_list(request):
    """View for browsing and managing texts."""
    # Get public texts
    public_texts = Text.objects.filter(is_public=True).order_by('-created_at')
    
    # Get user's own texts
    user_texts = Text.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'public_texts': public_texts,
        'user_texts': user_texts,
    }
    
    return render(request, 'core/text_list.html', context)


def about(request):
    """About page."""
    return render(request, 'core/about.html')


@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for Google Cloud Run"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'speech-memorization-platform'
    })
