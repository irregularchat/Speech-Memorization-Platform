import json
import base64
import logging
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.utils import timezone

from .models import Text, PracticeSession, WordProgress
from .practice_service import AdaptivePracticeEngine
from .ai_speech_service import SpeechToTextProcessor, IntelligentSpeechAnalyzer, AudioProcessor
import time
from threading import Lock

logger = logging.getLogger(__name__)

# Global state for streaming sessions
streaming_sessions = {}
session_lock = Lock()


@login_required
@require_http_methods(["POST"])
def process_ai_speech_input(request):
    """Process speech input using OpenAI Whisper and intelligent analysis"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        audio_data_b64 = data.get('audio_data')  # Base64 encoded audio
        audio_format = data.get('audio_format', 'webm')
        
        if not session_key or not audio_data_b64:
            return JsonResponse({
                'success': False,
                'error': 'Missing session key or audio data'
            })
        
        # Get practice engine from cache
        practice_engine = cache.get(session_key)
        if not practice_engine:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Decode audio data
        try:
            audio_data = base64.b64decode(audio_data_b64)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid audio data: {str(e)}'
            })
        
        # Validate audio quality
        audio_processor = AudioProcessor()
        quality_check = audio_processor.validate_audio_quality(audio_data)
        
        if not quality_check['suitable_for_recognition']:
            return JsonResponse({
                'success': False,
                'error': 'Audio quality too low for recognition',
                'quality_issues': quality_check['issues'],
                'suggestions': ['Speak louder', 'Move closer to microphone', 'Reduce background noise']
            })
        
        # Process audio for optimal recognition
        processed_audio = audio_processor.process_webm_audio(audio_data)
        
        # Transcribe using Whisper
        speech_processor = SpeechToTextProcessor()
        transcription_result = speech_processor.transcribe_audio(processed_audio, 'wav')
        
        if not transcription_result['success']:
            return JsonResponse({
                'success': False,
                'error': f'Speech recognition failed: {transcription_result.get("error", "Unknown error")}',
                'transcription_attempted': True
            })
        
        spoken_text = transcription_result['transcription']
        confidence = transcription_result.get('confidence', 0.5)
        
        # Get expected text for current word/phrase
        current_word_index = practice_engine.current_word_index
        if current_word_index >= len(practice_engine.words):
            return JsonResponse({
                'success': False,
                'error': 'Practice session complete'
            })
        
        current_word = practice_engine.words[current_word_index].word
        
        # Get context for better analysis (surrounding words)
        context_words = []
        for i in range(max(0, current_word_index - 2), 
                      min(len(practice_engine.words), current_word_index + 3)):
            context_words.append(practice_engine.words[i].word)
        expected_context = ' '.join(context_words)
        
        # Analyze speech with AI
        speech_analyzer = IntelligentSpeechAnalyzer()
        analysis_result = speech_analyzer.analyze_speech_accuracy(
            spoken_text, 
            current_word,
            context=expected_context
        )
        
        if not analysis_result['success']:
            return JsonResponse({
                'success': False,
                'error': f'Speech analysis failed: {analysis_result.get("error", "Unknown error")}'
            })
        
        # Enhanced word matching with fuzzy logic
        word_match = _enhanced_word_matching(
            spoken_text, 
            current_word, 
            analysis_result,
            confidence
        )
        
        # Process the result through practice engine
        if word_match['is_match']:
            # Word correctly recognized - advance
            practice_result = practice_engine.advance_to_word(current_word_index + 1)
            
            # Add AI analysis to result
            practice_result.update({
                'ai_analysis': {
                    'transcription': spoken_text,
                    'confidence': confidence,
                    'accuracy': analysis_result['overall_accuracy'],
                    'feedback': analysis_result.get('ai_feedback'),
                    'pronunciation_quality': 'good' if confidence > 0.8 else 'needs_improvement'
                },
                'word_recognized': True,
                'recognition_confidence': confidence
            })
        else:
            # Word not recognized or incorrect
            current_word_state = practice_engine.words[current_word_index]
            current_word_state.attempts += 1
            
            # Determine if hint should be applied based on confidence and attempts
            should_apply_hint = (
                confidence < 0.6 or 
                current_word_state.attempts >= 2 or
                analysis_result['overall_accuracy'] < 50
            )
            
            if should_apply_hint:
                hint_result = practice_engine.apply_hint('auto')
                practice_result = {
                    'success': False,
                    'word_found': False,
                    'hint_applied': True,
                    'hint_level': hint_result['hint_level'],
                    'display_text': hint_result['display_text'],
                    'attempts': current_word_state.attempts
                }
            else:
                practice_result = {
                    'success': False,
                    'word_found': False,
                    'hint_applied': False,
                    'display_text': practice_engine.get_display_text(),
                    'attempts': current_word_state.attempts
                }
            
            # Add detailed AI analysis for failed attempts
            practice_result.update({
                'ai_analysis': {
                    'transcription': spoken_text,
                    'expected_word': current_word,
                    'confidence': confidence,
                    'accuracy': analysis_result['overall_accuracy'],
                    'feedback': analysis_result.get('ai_feedback'),
                    'suggestions': analysis_result.get('suggestions', []),
                    'word_differences': analysis_result.get('word_differences', []),
                    'pronunciation_feedback': analysis_result.get('pronunciation_feedback'),
                    'error_type': word_match['error_type']
                },
                'word_recognized': False,
                'recognition_confidence': confidence
            })
        
        # Update cache
        cache.set(session_key, practice_engine, timeout=3600)
        
        return JsonResponse(practice_result)
        
    except Exception as e:
        logger.error(f"AI speech processing error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Speech processing failed: {str(e)}',
            'internal_error': True
        })


@login_required
@require_http_methods(["POST"])
def get_ai_pronunciation_feedback(request):
    """Get detailed AI pronunciation feedback for a specific word"""
    try:
        data = json.loads(request.body)
        spoken_text = data.get('spoken_text', '')
        expected_word = data.get('expected_word', '')
        user_context = data.get('context', '')
        
        if not spoken_text or not expected_word:
            return JsonResponse({
                'success': False,
                'error': 'Missing spoken text or expected word'
            })
        
        # Analyze with AI
        speech_analyzer = IntelligentSpeechAnalyzer()
        analysis_result = speech_analyzer.analyze_speech_accuracy(
            spoken_text,
            expected_word,
            context=user_context
        )
        
        if not analysis_result['success']:
            return JsonResponse({
                'success': False,
                'error': 'Analysis failed'
            })
        
        # Generate pronunciation tips using AI
        pronunciation_tips = _generate_pronunciation_tips(
            spoken_text, 
            expected_word, 
            analysis_result
        )
        
        return JsonResponse({
            'success': True,
            'analysis': analysis_result,
            'pronunciation_tips': pronunciation_tips,
            'detailed_feedback': True
        })
        
    except Exception as e:
        logger.error(f"Pronunciation feedback error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def test_microphone_quality(request):
    """Test microphone quality and provide setup recommendations"""
    try:
        data = json.loads(request.body)
        audio_data_b64 = data.get('audio_data')
        audio_format = data.get('audio_format', 'webm')
        
        if not audio_data_b64:
            return JsonResponse({
                'success': False,
                'error': 'No audio data provided'
            })
        
        # Decode and analyze audio
        audio_data = base64.b64decode(audio_data_b64)
        audio_processor = AudioProcessor()
        quality_check = audio_processor.validate_audio_quality(audio_data)
        
        # Test transcription quality
        speech_processor = SpeechToTextProcessor()
        processed_audio = audio_processor.process_webm_audio(audio_data)
        transcription_result = speech_processor.transcribe_audio(processed_audio, 'wav')
        
        recommendations = []
        quality_rating = "good"
        
        if quality_check['quality_score'] < 0.7:
            quality_rating = "poor"
            recommendations.extend([
                "Speak louder and clearer",
                "Move closer to your microphone",
                "Reduce background noise"
            ])
        elif quality_check['quality_score'] < 0.85:
            quality_rating = "fair"
            recommendations.append("Consider improving audio setup for better recognition")
        
        if transcription_result['success']:
            confidence = transcription_result.get('confidence', 0.5)
            if confidence < 0.6:
                recommendations.append("Try speaking more clearly for better recognition")
        else:
            quality_rating = "poor"
            recommendations.append("Audio quality too low for speech recognition")
        
        return JsonResponse({
            'success': True,
            'quality_rating': quality_rating,
            'quality_score': quality_check['quality_score'],
            'duration': quality_check.get('duration', 0),
            'issues': quality_check.get('issues', []),
            'recommendations': recommendations,
            'transcription_test': {
                'success': transcription_result['success'],
                'text': transcription_result.get('transcription', ''),
                'confidence': transcription_result.get('confidence', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Microphone test error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def _enhanced_word_matching(spoken_text: str, expected_word: str, 
                          analysis_result: dict, confidence: float) -> dict:
    """Enhanced word matching with fuzzy logic and AI insights"""
    spoken_words = spoken_text.lower().split()
    expected_word_lower = expected_word.lower()
    
    # Direct match
    if expected_word_lower in [word.lower() for word in spoken_words]:
        return {
            'is_match': True,
            'match_confidence': confidence,
            'error_type': None
        }
    
    # Fuzzy matching for pronunciation variants
    for spoken_word in spoken_words:
        similarity = _calculate_phonetic_similarity(spoken_word.lower(), expected_word_lower)
        if similarity > 0.8 and confidence > 0.5:
            return {
                'is_match': True,
                'match_confidence': confidence * similarity,
                'error_type': 'pronunciation_variant'
            }
    
    # Check for partial matches (for compound words or contractions)
    if len(expected_word_lower) > 6:  # Only for longer words
        for spoken_word in spoken_words:
            if (expected_word_lower.startswith(spoken_word.lower()) or 
                expected_word_lower.endswith(spoken_word.lower()) or
                spoken_word.lower() in expected_word_lower):
                if confidence > 0.6:
                    return {
                        'is_match': True,
                        'match_confidence': confidence * 0.8,
                        'error_type': 'partial_match'
                    }
    
    # No match found
    error_type = 'substitution'
    if not spoken_words:
        error_type = 'no_speech'
    elif len(spoken_words) > 3:
        error_type = 'too_many_words'
    elif analysis_result['overall_accuracy'] > 80:
        error_type = 'close_match'
    
    return {
        'is_match': False,
        'match_confidence': 0,
        'error_type': error_type
    }


def _calculate_phonetic_similarity(word1: str, word2: str) -> float:
    """Calculate phonetic similarity between words"""
    # Simple phonetic similarity based on common pronunciation patterns
    from difflib import SequenceMatcher
    
    # Basic similarity
    base_similarity = SequenceMatcher(None, word1, word2).ratio()
    
    # Boost for common pronunciation variations
    phonetic_patterns = [
        ('ph', 'f'), ('ck', 'k'), ('qu', 'kw'), ('x', 'ks'),
        ('c', 'k'), ('s', 'z'), ('ed', 'd'), ('ing', 'in')
    ]
    
    word1_phonetic = word1
    word2_phonetic = word2
    
    for pattern, replacement in phonetic_patterns:
        word1_phonetic = word1_phonetic.replace(pattern, replacement)
        word2_phonetic = word2_phonetic.replace(pattern, replacement)
    
    phonetic_similarity = SequenceMatcher(None, word1_phonetic, word2_phonetic).ratio()
    
    # Return the better of the two similarities
    return max(base_similarity, phonetic_similarity)


def _generate_pronunciation_tips(spoken_text: str, expected_word: str, 
                               analysis_result: dict) -> list:
    """Generate helpful pronunciation tips"""
    tips = []
    
    # Based on analysis results
    if analysis_result.get('pronunciation_feedback', {}).get('has_issues'):
        tips.append("Focus on clear pronunciation of each syllable")
    
    # Based on word differences
    differences = analysis_result.get('word_differences', [])
    if differences:
        for diff in differences[:2]:  # Limit to first 2 differences
            if diff['type'] == 'pronunciation':
                tips.append(f"Try pronouncing '{diff['expected']}' more clearly")
    
    # General tips based on accuracy
    accuracy = analysis_result.get('overall_accuracy', 0)
    if accuracy < 50:
        tips.extend([
            "Speak slower and more clearly",
            "Break the word into syllables",
            "Practice saying the word several times"
        ])
    elif accuracy < 80:
        tips.append("Good effort! Just focus on the specific sounds that are different")
    
    return tips[:3]  # Limit to 3 tips to avoid overwhelming the user


@login_required
@require_http_methods(["POST"])
def process_streaming_speech_chunk(request):
    """Process real-time streaming speech chunks for immediate recognition"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        audio_data_b64 = data.get('base64Data')  # Base64 encoded audio chunk
        chunk_info = data.get('chunk_info', {})
        
        if not session_key or not audio_data_b64:
            return JsonResponse({
                'success': False,
                'error': 'Missing session key or audio data'
            })
        
        # Get streaming session state
        with session_lock:
            if session_key not in streaming_sessions:
                streaming_sessions[session_key] = {
                    'chunks_processed': 0,
                    'partial_transcriptions': [],
                    'last_activity': time.time(),
                    'accumulated_text': '',
                    'confidence_buffer': []
                }
            
            session_state = streaming_sessions[session_key]
            session_state['last_activity'] = time.time()
        
        # Decode and process audio chunk
        audio_data = base64.b64decode(audio_data_b64)
        audio_processor = AudioProcessor()
        
        # Quick validation for real-time processing
        if len(audio_data) < 1000:  # Too small chunk
            return JsonResponse({
                'success': True,
                'is_streaming': True,
                'chunk_too_small': True,
                'transcription': '',
                'confidence': 0.0
            })
        
        # Process audio chunk
        try:
            processed_audio = audio_processor.process_webm_audio(audio_data)
            speech_processor = SpeechToTextProcessor()
            
            # Use existing transcribe_audio method for real-time processing
            transcription_result = speech_processor.transcribe_audio(
                processed_audio, 
                'wav'
            )
            
            if not transcription_result['success']:
                return JsonResponse({
                    'success': True,
                    'is_streaming': True,
                    'transcription_failed': True,
                    'transcription': '',
                    'confidence': 0.0
                })
            
            transcription = transcription_result.get('transcription', '').strip()
            confidence = transcription_result.get('confidence', 0.5)
            
            # Update session state
            with session_lock:
                session_state['chunks_processed'] += 1
                session_state['partial_transcriptions'].append({
                    'text': transcription,
                    'confidence': confidence,
                    'timestamp': time.time(),
                    'chunk_sequence': chunk_info.get('sequence', 0)
                })
                
                # Keep only recent transcriptions (last 5 chunks)
                session_state['partial_transcriptions'] = session_state['partial_transcriptions'][-5:]
                
                # Accumulate text for better context
                if transcription and confidence > 0.3:
                    session_state['accumulated_text'] += ' ' + transcription
                    session_state['accumulated_text'] = session_state['accumulated_text'][-200:]  # Keep recent
                
                session_state['confidence_buffer'].append(confidence)
                session_state['confidence_buffer'] = session_state['confidence_buffer'][-10:]  # Last 10 chunks
            
            # Calculate moving average confidence
            avg_confidence = sum(session_state['confidence_buffer']) / len(session_state['confidence_buffer'])
            
            # Determine if we should trigger word processing
            should_process_word = (
                confidence > 0.6 and 
                len(transcription.split()) <= 3 and  # Short phrases only
                any(char.isalpha() for char in transcription)  # Contains letters
            )
            
            response = {
                'success': True,
                'is_streaming': True,
                'transcription': transcription,
                'confidence': confidence,
                'avg_confidence': avg_confidence,
                'should_process_word': should_process_word,
                'chunk_sequence': chunk_info.get('sequence', 0),
                'chunks_processed': session_state['chunks_processed'],
                'accumulated_text': session_state['accumulated_text'].strip(),
                'processing_time': time.time() - session_state['last_activity']
            }
            
            # If confidence is high enough, include word matching hint
            if should_process_word:
                response['suggested_word_match'] = transcription
                response['ready_for_processing'] = True
            
            return JsonResponse(response)
            
        except Exception as audio_error:
            logger.error(f"Audio processing error in streaming: {str(audio_error)}")
            return JsonResponse({
                'success': True,
                'is_streaming': True,
                'audio_processing_error': True,
                'error': str(audio_error),
                'transcription': '',
                'confidence': 0.0
            })
        
    except Exception as e:
        logger.error(f"Streaming speech processing error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Streaming processing failed: {str(e)}',
            'is_streaming': True
        })


@login_required
@require_http_methods(["POST"])
def stop_streaming_session(request):
    """Stop a streaming speech session and cleanup"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        if not session_key:
            return JsonResponse({
                'success': False,
                'error': 'Missing session key'
            })
        
        # Get final session state
        final_state = None
        with session_lock:
            if session_key in streaming_sessions:
                final_state = streaming_sessions.pop(session_key)
        
        if final_state:
            return JsonResponse({
                'success': True,
                'final_state': {
                    'chunks_processed': final_state['chunks_processed'],
                    'final_transcription': final_state['accumulated_text'].strip(),
                    'session_duration': time.time() - final_state.get('start_time', time.time())
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'Session already ended or not found'
            })
        
    except Exception as e:
        logger.error(f"Stop streaming session error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })