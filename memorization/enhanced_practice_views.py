from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
from django.db import models
import json
import uuid
import time

from .models import (Text, PracticeSession, WordProgress, UserTextProgress,
                     PracticePattern, DelayedRecallSession, WordRevealSession)
from .enhanced_practice_service import AdvancedPracticeEngine


@login_required
def enhanced_practice_dashboard(request, text_id):
    """Enhanced practice dashboard with multiple practice modes"""
    text = get_object_or_404(Text, id=text_id)
    
    # Check permissions
    if not text.is_public and text.created_by != request.user:
        return render(request, 'core/error.html', {
            'error_message': 'You do not have permission to practice this text.',
            'redirect_url': '/texts/'
        })
    
    # Get user progress and analytics
    user_progress, created = UserTextProgress.objects.get_or_create(
        user=request.user,
        text=text
    )
    
    # Get word-level statistics
    word_progress = WordProgress.objects.filter(user=request.user, text=text)
    problem_words = word_progress.filter(is_problem_word=True)
    
    # Get practice patterns
    practice_patterns = PracticePattern.objects.filter(
        user=request.user, text=text
    ).order_by('-difficulty_score')[:5]
    
    # Get recent sessions
    recent_sessions = PracticeSession.objects.filter(
        user=request.user, text=text
    ).order_by('-started_at')[:10]
    
    # Check for active delayed recall sessions
    active_recall_sessions = DelayedRecallSession.objects.filter(
        user=request.user,
        text=text,
        is_completed=False
    )
    
    # Check for active word reveal sessions
    active_reveal_sessions = WordRevealSession.objects.filter(
        user=request.user,
        text=text,
        completed_at__isnull=True
    )
    
    context = {
        'text': text,
        'user_progress': user_progress,
        'word_progress_stats': {
            'total_words': len(text.content.split()),
            'tracked_words': word_progress.count(),
            'problem_words': problem_words.count(),
            'mastered_words': word_progress.filter(mastery_level__gte=0.8).count(),
            'average_mastery': word_progress.aggregate(
                avg_mastery=models.Avg('mastery_level')
            )['avg_mastery'] or 0.0,
        },
        'practice_patterns': practice_patterns,
        'recent_sessions': recent_sessions,
        'active_recall_sessions': active_recall_sessions,
        'active_reveal_sessions': active_reveal_sessions,
    }
    
    return render(request, 'memorization/enhanced_practice_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def start_word_reveal_session(request):
    """Start a progressive word reveal practice session"""
    try:
        data = json.loads(request.body)
        text_id = data.get('text_id')
        
        text = get_object_or_404(Text, id=text_id)
        
        # Create practice engine
        engine = AdvancedPracticeEngine(text, request.user, 'word_reveal')
        
        # Configure word reveal session
        config = {
            'strategy': data.get('strategy', 'progressive'),
            'reveal_percentage': data.get('reveal_percentage', 0.1),
            'increment_percentage': data.get('increment_percentage', 0.1),
            'auto_hide_enabled': data.get('auto_hide_enabled', True),
            'hide_delay_seconds': data.get('hide_delay_seconds', 3),
            'fade_duration_seconds': data.get('fade_duration_seconds', 2),
        }
        
        # Start session
        reveal_session = engine.start_word_reveal_session(config)
        
        # Store engine in cache
        session_key = f"enhanced_practice_{reveal_session.id}"
        cache.set(session_key, engine, timeout=3600)
        
        return JsonResponse({
            'success': True,
            'session_id': reveal_session.id,
            'session_key': session_key,
            'session_type': 'word_reveal',
            'display_text': engine.get_enhanced_display_text(),
            'config': config,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def start_delayed_recall_session(request):
    """Start a delayed recall practice session"""
    try:
        data = json.loads(request.body)
        text_id = data.get('text_id')
        
        text = get_object_or_404(Text, id=text_id)
        
        # Create practice engine
        engine = AdvancedPracticeEngine(text, request.user, 'delayed_recall')
        
        # Configure delayed recall session
        config = {
            'delay_minutes': data.get('delay_minutes', 15),
            'reveal_percentage': data.get('reveal_percentage', 0.3),
            'auto_hide_enabled': data.get('auto_hide_enabled', True),
            'auto_hide_delay': data.get('auto_hide_delay', 5),
        }
        
        # Start session
        recall_session = engine.start_delayed_recall_session(config)
        
        # Store engine in cache
        session_key = f"enhanced_practice_{recall_session.id}"
        cache.set(session_key, engine, timeout=7200)  # 2 hours for delayed recall
        
        return JsonResponse({
            'success': True,
            'session_id': recall_session.id,
            'session_key': session_key,
            'session_type': 'delayed_recall',
            'display_text': engine.get_enhanced_display_text(),
            'config': config,
            'study_phase': True,
            'words_to_recall': recall_session.words_to_recall,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def advance_word_reveal_round(request):
    """Advance to the next round in word reveal session"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        # Get practice engine from cache
        engine = cache.get(session_key)
        if not engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Update reveal session
        if engine.reveal_session:
            engine.reveal_session.current_round += 1
            engine.reveal_session.save()
            
            # Calculate new reveal set
            engine._update_word_reveal_state()
            
            # Update cache
            cache.set(session_key, engine, timeout=3600)
            
            return JsonResponse({
                'success': True,
                'current_round': engine.reveal_session.current_round,
                'display_text': engine.get_enhanced_display_text(),
                'visible_words': engine.reveal_session.currently_visible_words,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No active reveal session'
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def transition_to_recall_phase(request):
    """Transition delayed recall session from study to recall phase"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        # Get practice engine from cache
        engine = cache.get(session_key)
        if not engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Check if ready for recall
        if engine.delayed_recall_session and engine.delayed_recall_session.is_ready_for_recall:
            engine.delayed_recall_session.is_study_phase = False
            engine.delayed_recall_session.is_recall_phase = True
            engine.delayed_recall_session.recall_started_at = timezone.now()
            engine.delayed_recall_session.save()
            
            # Update cache
            cache.set(session_key, engine, timeout=3600)
            
            return JsonResponse({
                'success': True,
                'recall_phase': True,
                'display_text': engine.get_enhanced_display_text(),
                'words_to_recall': engine.delayed_recall_session.words_to_recall,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Not ready for recall phase yet'
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def process_enhanced_speech_input(request):
    """Process speech input with enhanced features"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        spoken_text = data.get('spoken_text', '')
        word_index = data.get('word_index', 0)
        
        # Get practice engine from cache
        engine = cache.get(session_key)
        if not engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Process the speech input (similar to original but with enhanced tracking)
        if word_index >= len(engine.words):
            return JsonResponse({
                'success': False,
                'error': 'Invalid word index'
            })
        
        word_state = engine.words[word_index]
        spoken_words = spoken_text.lower().split()
        expected_word = word_state.word.lower()
        
        # Track response time
        response_time = time.time() - (engine.word_start_time or time.time())
        
        # Check if word was spoken correctly
        word_found = any(
            expected_word in spoken_word or spoken_word in expected_word
            for spoken_word in spoken_words
        )
        
        # Update word progress
        if word_found:
            word_state.is_completed = True
            word_state.response_time = response_time
            
            # Update database
            word_progress, created = WordProgress.objects.get_or_create(
                user=request.user,
                text=engine.text,
                word_index=word_index,
                defaults={'word_text': word_state.word}
            )
            word_progress.update_mastery(True, response_time)
            
            # Track performance data
            engine.session_data['word_performance'].append({
                'word_index': word_index,
                'attempts': word_state.attempts + 1,
                'response_time': response_time,
                'success': True,
            })
            
            result = {
                'success': True,
                'word_found': True,
                'word_index': word_index,
                'next_word_index': word_index + 1,
                'display_text': engine.get_enhanced_display_text(),
                'response_time': response_time,
            }
        else:
            word_state.attempts += 1
            
            # Update database
            word_progress, created = WordProgress.objects.get_or_create(
                user=request.user,
                text=engine.text,
                word_index=word_index,
                defaults={'word_text': word_state.word}
            )
            word_progress.update_mastery(False, response_time)
            
            # Track performance data
            engine.session_data['word_performance'].append({
                'word_index': word_index,
                'attempts': word_state.attempts,
                'response_time': response_time,
                'success': False,
            })
            
            result = {
                'success': False,
                'word_found': False,
                'word_index': word_index,
                'attempts': word_state.attempts,
                'expected_word': word_state.word,
                'spoken_text': spoken_text,
                'display_text': engine.get_enhanced_display_text(),
            }
        
        # Update cache
        cache.set(session_key, engine, timeout=3600)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def apply_intelligent_hint(request):
    """Apply intelligent hint based on word characteristics"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        word_index = data.get('word_index', 0)
        hint_type = data.get('hint_type', 'auto')
        
        # Get practice engine from cache
        engine = cache.get(session_key)
        if not engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Apply hint
        result = engine.apply_intelligent_hint(word_index, hint_type)
        
        # Update cache
        cache.set(session_key, engine, timeout=3600)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def check_word_timing(request):
    """Check word timing for auto-hide and hint suggestions"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        word_index = data.get('word_index', 0)
        
        # Get practice engine from cache
        engine = cache.get(session_key)
        if not engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Process timing
        result = engine.process_word_timing(word_index)
        result['success'] = True
        result['display_text'] = engine.get_enhanced_display_text()
        
        # Update cache
        cache.set(session_key, engine, timeout=3600)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def complete_enhanced_session(request):
    """Complete enhanced practice session with analysis"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        # Get practice engine from cache
        engine = cache.get(session_key)
        if not engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Complete session with analysis
        result = engine.complete_session_with_analysis()
        
        # Clear cache
        cache.delete(session_key)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def get_practice_analytics(request, text_id):
    """Get detailed practice analytics for a text"""
    text = get_object_or_404(Text, id=text_id)
    
    # Get practice patterns
    patterns = PracticePattern.objects.filter(
        user=request.user, text=text
    ).order_by('-difficulty_score')
    
    # Get word progress
    word_progress = WordProgress.objects.filter(
        user=request.user, text=text
    ).order_by('word_index')
    
    # Calculate analytics
    analytics = {
        'total_patterns': patterns.count(),
        'high_difficulty_patterns': patterns.filter(difficulty_score__gte=0.7).count(),
        'pattern_types': {},
        'word_mastery_distribution': {
            'beginner': word_progress.filter(mastery_level__lt=0.3).count(),
            'intermediate': word_progress.filter(mastery_level__gte=0.3, mastery_level__lt=0.7).count(),
            'advanced': word_progress.filter(mastery_level__gte=0.7, mastery_level__lt=0.9).count(),
            'mastered': word_progress.filter(mastery_level__gte=0.9).count(),
        },
        'problem_areas': [],
    }
    
    # Pattern type distribution
    for pattern in patterns:
        pattern_type = pattern.get_pattern_type_display()
        if pattern_type not in analytics['pattern_types']:
            analytics['pattern_types'][pattern_type] = 0
        analytics['pattern_types'][pattern_type] += 1
    
    # Problem areas with recommendations
    for pattern in patterns.filter(difficulty_score__gte=0.5)[:10]:
        analytics['problem_areas'].append({
            'type': pattern.get_pattern_type_display(),
            'start_word': pattern.start_word_index,
            'end_word': pattern.end_word_index,
            'difficulty': pattern.difficulty_score,
            'frequency': pattern.frequency_encountered,
            'success_rate': pattern.success_rate,
        })
    
    return JsonResponse({
        'success': True,
        'analytics': analytics
    })


@login_required
def get_session_recommendations(request, text_id):
    """Get personalized practice session recommendations"""
    text = get_object_or_404(Text, id=text_id)
    
    # Analyze user's practice history
    word_progress = WordProgress.objects.filter(user=request.user, text=text)
    patterns = PracticePattern.objects.filter(user=request.user, text=text)
    
    recommendations = []
    
    # Recommend delayed recall for well-practiced areas
    if word_progress.filter(mastery_level__gte=0.6).count() > 10:
        recommendations.append({
            'type': 'delayed_recall',
            'title': 'Delayed Recall Session',
            'description': 'Test your memory retention with a delayed recall session',
            'config': {
                'delay_minutes': 15,
                'reveal_percentage': 0.3,
            },
            'priority': 'high',
        })
    
    # Recommend word reveal for struggling areas
    if word_progress.filter(is_problem_word=True).count() > 5:
        recommendations.append({
            'type': 'word_reveal',
            'title': 'Progressive Word Reveal',
            'description': 'Focus on problem words with gradual revelation',
            'config': {
                'strategy': 'mastery_based',
                'reveal_percentage': 0.2,
                'auto_hide_enabled': True,
            },
            'priority': 'high',
        })
    
    # Recommend pattern-specific practice
    high_difficulty_patterns = patterns.filter(difficulty_score__gte=0.7)
    if high_difficulty_patterns.exists():
        pattern_types = set(p.pattern_type for p in high_difficulty_patterns)
        for pattern_type in pattern_types:
            recommendations.append({
                'type': 'pattern_focus',
                'title': f'Focus on {pattern_type.replace("_", " ").title()}',
                'description': f'Target practice for {pattern_type.replace("_", " ")} difficulties',
                'config': {
                    'pattern_type': pattern_type,
                },
                'priority': 'medium',
            })
    
    return JsonResponse({
        'success': True,
        'recommendations': recommendations
    })


@login_required
@require_http_methods(["POST"])
def start_delayed_recall_session(request):
    """Start a delayed recall practice session"""
    try:
        data = json.loads(request.body)
        text_id = data.get('text_id')
        delay_minutes = data.get('delay_minutes', 15)
        reveal_percentage = data.get('reveal_percentage', 0.3)
        auto_hide_enabled = data.get('auto_hide_enabled', True)
        auto_hide_delay = data.get('auto_hide_delay', 5)
        
        text = get_object_or_404(Text, id=text_id)
        
        # Check if user can access this text
        if not text.is_public and text.created_by != request.user:
            return JsonResponse({'success': False, 'error': 'Access denied'})
        
        # Create delayed recall session
        from .models import DelayedRecallSession
        session = DelayedRecallSession.objects.create(
            user=request.user,
            text=text,
            delay_minutes=delay_minutes,
            reveal_percentage=reveal_percentage,
            auto_hide_enabled=auto_hide_enabled,
            auto_hide_delay=auto_hide_delay,
            is_study_phase=True
        )
        
        # Generate initial display (study phase)
        words = text.content.split()
        total_words = len(words)
        reveal_count = int(total_words * reveal_percentage)
        
        # Select words to reveal (prioritize beginning and important words)
        words_to_reveal = list(range(min(reveal_count, total_words)))
        session.words_to_recall = words_to_reveal
        session.save()
        
        # Create display HTML
        display_html = ""
        for i, word in enumerate(words):
            if i in words_to_reveal:
                display_html += f'<span class="word-visible" data-word-index="{i}">{word}</span> '
            else:
                display_html += f'<span class="word-masked" data-word-index="{i}">{"_" * len(word)}</span> '
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'study_phase': True,
            'delay_minutes': delay_minutes,
            'display_text': display_html,
            'instruction': f'Study the visible words for as long as you need. You will be tested after a {delay_minutes}-minute delay.',
            'total_words': total_words,
            'visible_words': len(words_to_reveal)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required 
@require_http_methods(["POST"])
def start_word_reveal_session(request):
    """Start a progressive word reveal practice session"""
    try:
        data = json.loads(request.body)
        text_id = data.get('text_id')
        reveal_strategy = data.get('reveal_strategy', 'progressive')
        reveal_percentage = data.get('reveal_percentage', 0.1)
        increment_percentage = data.get('increment_percentage', 0.1)
        
        text = get_object_or_404(Text, id=text_id)
        
        # Check if user can access this text
        if not text.is_public and text.created_by != request.user:
            return JsonResponse({'success': False, 'error': 'Access denied'})
        
        # Create word reveal session
        from .models import WordRevealSession
        session = WordRevealSession.objects.create(
            user=request.user,
            text=text,
            reveal_strategy=reveal_strategy,
            reveal_percentage=reveal_percentage,
            increment_percentage=increment_percentage,
            current_round=1
        )
        
        # Calculate initial word reveal
        words = text.content.split()
        total_words = len(words)
        initial_reveal_count = max(1, int(total_words * reveal_percentage))
        
        # Select initial words to reveal
        if reveal_strategy == 'progressive':
            # Start with first few words
            visible_words = list(range(initial_reveal_count))
        elif reveal_strategy == 'difficulty_adaptive':
            # Start with easier/shorter words
            word_difficulties = [(i, len(word)) for i, word in enumerate(words)]
            word_difficulties.sort(key=lambda x: x[1])  # Sort by length
            visible_words = [idx for idx, _ in word_difficulties[:initial_reveal_count]]
        else:
            # Random selection
            import random
            visible_words = random.sample(range(total_words), initial_reveal_count)
        
        session.currently_visible_words = visible_words
        session.save()
        
        # Create display HTML
        display_html = ""
        for i, word in enumerate(words):
            if i in visible_words:
                display_html += f'<span class="word-visible word-current" data-word-index="{i}">{word}</span> '
            else:
                display_html += f'<span class="word-masked" data-word-index="{i}">{"_" * len(word)}</span> '
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'session_type': 'word_reveal',
            'display_text': display_html,
            'current_round': 1,
            'visible_count': len(visible_words),
            'total_words': total_words,
            'strategy': reveal_strategy,
            'instruction': f'Practice the visible words. Round {session.current_round} - {len(visible_words)}/{total_words} words visible.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })