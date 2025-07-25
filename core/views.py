from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import AnonymousUser
from functools import wraps
import json

# Try to import models, but handle gracefully if they don't exist
try:
    from memorization.models import Text, PracticeSession, UserTextProgress
    from memorization.services import SpacedRepetitionService, PracticeSessionService
    from analytics.models import UserAnalytics
    MODELS_AVAILABLE = True
except Exception:
    MODELS_AVAILABLE = False


def demo_login_required(view_func):
    """Custom login decorator that works with demo mode."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated normally
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        
        # Check if demo session exists
        if request.session.get('demo_user'):
            return view_func(request, *args, **kwargs)
        
        # Not authenticated, redirect to login
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path(), '/login/')
    
    return wrapper


def home(request):
    """Home page view - main memorization interface."""
    
    # Demo data for when database is not available
    demo_texts = [
        {
            'id': 1,
            'title': 'Army Creed',
            'description': 'The Soldier\'s Creed - fundamental beliefs of American soldiers',
            'word_count': 89,
            'content': 'I am an American Soldier. I am a warrior and a member of a team. I serve the people of the United States, and live the Army Values...'
        },
        {
            'id': 2,
            'title': 'Navy Creed',
            'description': 'The Sailor\'s Creed - core values of Navy personnel',
            'word_count': 76,
            'content': 'I am a United States Sailor. I will support and defend the Constitution of the United States of America...'
        },
        {
            'id': 3,
            'title': 'Air Force Creed',
            'description': 'The Airman\'s Creed - commitment to excellence in all we do',
            'word_count': 95,
            'content': 'I am an American Airman. I am a Warrior. I have answered my Nation\'s call...'
        },
        {
            'id': 4,
            'title': 'Marine Corps Creed',
            'description': 'My Creed - the spirit that has sustained Marines for over 240 years',
            'word_count': 112,
            'content': 'My rifle and myself know that what counts in this war is not the rounds we fire...'
        }
    ]
    
    if MODELS_AVAILABLE:
        try:
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
        except Exception:
            # Fallback to demo data
            context = {
                'texts': demo_texts,
                'is_demo': True,
                'demo_message': 'Demo mode - database not available'
            }
    else:
        # Use demo data
        context = {
            'texts': demo_texts,
            'is_demo': True,
            'demo_message': 'Demo mode - showing sample military creeds'
        }
    
    return render(request, 'core/home.html', context)


@demo_login_required
def practice_text(request, text_id):
    """Practice page for a specific text."""
    if not MODELS_AVAILABLE:
        # Demo practice page
        demo_text = {
            'id': text_id,
            'title': 'Army Creed (Demo)',
            'content': 'I am an American Soldier. I am a warrior and a member of a team. I serve the people of the United States, and live the Army Values. I will always place the mission first. I will never accept defeat. I will never quit. I will never leave a fallen comrade.',
            'word_count': 47
        }
        context = {
            'text': demo_text,
            'display_text': demo_text['content'],
            'is_demo': True,
            'demo_message': 'Demo mode - practice interface'
        }
        return render(request, 'core/practice.html', context)
    
    try:
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
    except Exception:
        return redirect('home')


@csrf_exempt
@require_http_methods(["POST"])
def update_mastery_level(request):
    """AJAX endpoint to update mastery level."""
    if not MODELS_AVAILABLE:
        return JsonResponse({'success': True, 'message': 'Demo mode - mastery level updated'})
    
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


@demo_login_required
def analytics(request):
    """Analytics dashboard view."""
    if not MODELS_AVAILABLE:
        # Demo analytics
        context = {
            'is_demo': True,
            'demo_message': 'Demo analytics - sample data shown',
            'total_sessions': 15,
            'total_words_practiced': 1247,
            'average_accuracy': 85.6,
            'current_streak': 7
        }
        return render(request, 'core/analytics.html', context)
    
    try:
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
    except Exception:
        # Fallback to demo data
        context = {
            'is_demo': True,
            'demo_message': 'Demo analytics - database error',
            'total_sessions': 5,
            'total_words_practiced': 423,
            'average_accuracy': 78.4,
            'current_streak': 3
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


def demo_login(request):
    """Demo login view that bypasses database authentication."""
    if request.method == 'POST':
        # In demo mode, always succeed
        username = request.POST.get('username', 'demo')
        
        # Create a fake session for demo purposes
        request.session['demo_user'] = True
        request.session['demo_username'] = username
        
        # Redirect to next page or home
        next_url = request.GET.get('next', '/')
        messages.success(request, f'Demo mode: Logged in as {username}')
        return redirect(next_url)
    
    return render(request, 'registration/login.html', {
        'demo_mode': True,
        'demo_message': 'Demo mode - any credentials will work'
    })


def demo_logout(request):
    """Demo logout view."""
    # Clear demo session
    if 'demo_user' in request.session:
        del request.session['demo_user']
    if 'demo_username' in request.session:
        del request.session['demo_username']
    
    messages.success(request, 'Demo mode: Logged out successfully')
    return redirect('/')


@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for Google Cloud Run"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'speech-memorization-platform',
        'message': 'Speech Memorization Platform for Military Creeds',
        'features': ['Military Creeds', 'Speech Practice', 'Real-time Feedback', 'Progress Tracking', 'Spaced Repetition'],
        'version': '2.0.0'
    })
