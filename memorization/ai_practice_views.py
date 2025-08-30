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
from .ai_speech_service import SpeechToTextProcessor, IntelligentSpeechAnalyzer, AudioProcessor, PhraseBasedPracticeEngine
from .google_speech_service import GoogleSpeechStreamingService, GoogleSpeechBatchService
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
                    'error_type': word_match['error_type'],
                    'provider_used': transcription_result.get('provider', 'unknown')
                },
                'word_recognized': False,
                'recognition_confidence': confidence
            })
        
        # Update adaptive processing with confidence feedback
        if hasattr(request, 'session'):
            confidence_key = f"confidence_history_{session_key}"
            confidence_history = request.session.get(confidence_key, [])
            confidence_history.append(confidence)
            # Keep only last 10 confidences
            request.session[confidence_key] = confidence_history[-10:]
        
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
    """Enhanced phonetic similarity using multiple algorithms"""
    from difflib import SequenceMatcher
    
    # Normalize words
    w1, w2 = word1.lower().strip(), word2.lower().strip()
    
    if w1 == w2:
        return 1.0
    
    # 1. Basic string similarity
    base_similarity = SequenceMatcher(None, w1, w2).ratio()
    
    # 2. Enhanced phonetic patterns
    phonetic_similarity = _advanced_phonetic_similarity(w1, w2)
    
    # 3. Metaphone-like algorithm
    metaphone_similarity = _metaphone_similarity(w1, w2)
    
    # 4. Edit distance based similarity
    edit_similarity = _levenshtein_similarity(w1, w2)
    
    # 5. Syllable-based similarity
    syllable_similarity = _syllable_similarity(w1, w2)
    
    # Weighted combination of similarities
    similarities = [
        (base_similarity, 0.2),
        (phonetic_similarity, 0.3),
        (metaphone_similarity, 0.2),
        (edit_similarity, 0.2),
        (syllable_similarity, 0.1)
    ]
    
    weighted_score = sum(score * weight for score, weight in similarities)
    
    # Boost for very short words that are close
    if len(w1) <= 3 and len(w2) <= 3 and abs(len(w1) - len(w2)) <= 1:
        weighted_score = min(1.0, weighted_score * 1.2)
    
    return weighted_score

def _advanced_phonetic_similarity(word1: str, word2: str) -> float:
    """Advanced phonetic pattern matching"""
    # Extended phonetic substitution patterns
    phonetic_patterns = [
        # Common English phonetic variations
        ('ph', 'f'), ('ck', 'k'), ('qu', 'kw'), ('x', 'ks'),
        ('c', 'k'), ('s', 'z'), ('ed', 'd'), ('ing', 'in'),
        ('tion', 'shun'), ('sion', 'zhun'), ('ough', 'uff'),
        ('augh', 'aff'), ('eigh', 'ay'), ('igh', 'eye'),
        ('kn', 'n'), ('wr', 'r'), ('mb', 'm'), ('bt', 't'),
        ('th', 'f'), ('dge', 'j'), ('tch', 'ch'),
        ('oo', 'u'), ('ea', 'ee'), ('ou', 'ow'), ('ow', 'o'),
        ('ai', 'ay'), ('ei', 'ay'), ('ie', 'ee'), ('ey', 'ay'),
        ('oe', 'o'), ('ue', 'oo'), ('ui', 'oo'),
        # Silent letters
        ('k', ''), ('b', ''), ('l', ''), ('t', ''), ('h', ''),
        # Double letters
        ('ll', 'l'), ('ss', 's'), ('ff', 'f'), ('gg', 'g'),
        ('mm', 'm'), ('nn', 'n'), ('pp', 'p'), ('rr', 'r'),
        ('tt', 't'), ('zz', 'z')
    ]
    
    # Apply transformations
    w1_transformed = word1
    w2_transformed = word2
    
    for pattern, replacement in phonetic_patterns:
        w1_transformed = w1_transformed.replace(pattern, replacement)
        w2_transformed = w2_transformed.replace(pattern, replacement)
    
    # Calculate similarity after transformation
    from difflib import SequenceMatcher
    return SequenceMatcher(None, w1_transformed, w2_transformed).ratio()

def _metaphone_similarity(word1: str, word2: str) -> float:
    """Simplified metaphone algorithm for phonetic similarity"""
    def simple_metaphone(word):
        """Simplified metaphone encoding"""
        if not word:
            return ""
        
        word = word.upper()
        metaphone_code = ""
        
        # Skip initial silent letters
        i = 0
        if word.startswith(('KN', 'GN', 'PN', 'WR')):
            i = 1
        
        while i < len(word):
            char = word[i]
            
            # Handle special combinations
            if i < len(word) - 1:
                two_char = word[i:i+2]
                if two_char in ['SH', 'CH', 'TH', 'PH']:
                    if two_char == 'PH':
                        metaphone_code += 'F'
                    elif two_char == 'TH':
                        metaphone_code += 'T'
                    else:
                        metaphone_code += two_char[0]
                    i += 2
                    continue
            
            # Handle individual characters
            if char in 'AEIOU':
                if i == 0:  # Only add vowels at the beginning
                    metaphone_code += char
            elif char == 'C':
                if i < len(word) - 1 and word[i+1] in 'EIY':
                    metaphone_code += 'S'
                else:
                    metaphone_code += 'K'
            elif char == 'G':
                if i < len(word) - 1 and word[i+1] in 'EIY':
                    metaphone_code += 'J'
                else:
                    metaphone_code += 'G'
            elif char == 'Q':
                metaphone_code += 'K'
            elif char == 'X':
                metaphone_code += 'KS'
            elif char == 'Z':
                metaphone_code += 'S'
            elif char in 'BCDFGHJKLMNPQRSTVWXYZ':
                metaphone_code += char
            
            i += 1
        
        return metaphone_code[:4]  # Limit to 4 characters
    
    m1 = simple_metaphone(word1)
    m2 = simple_metaphone(word2)
    
    if not m1 or not m2:
        return 0.0
    
    from difflib import SequenceMatcher
    return SequenceMatcher(None, m1, m2).ratio()

def _levenshtein_similarity(word1: str, word2: str) -> float:
    """Calculate similarity based on Levenshtein distance"""
    if len(word1) == 0:
        return 0.0 if len(word2) > 0 else 1.0
    if len(word2) == 0:
        return 0.0
    
    # Create matrix
    matrix = [[0] * (len(word2) + 1) for _ in range(len(word1) + 1)]
    
    # Initialize first row and column
    for i in range(len(word1) + 1):
        matrix[i][0] = i
    for j in range(len(word2) + 1):
        matrix[0][j] = j
    
    # Fill matrix
    for i in range(1, len(word1) + 1):
        for j in range(1, len(word2) + 1):
            if word1[i-1] == word2[j-1]:
                cost = 0
            else:
                cost = 1
            
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # deletion
                matrix[i][j-1] + 1,      # insertion
                matrix[i-1][j-1] + cost  # substitution
            )
    
    max_len = max(len(word1), len(word2))
    distance = matrix[len(word1)][len(word2)]
    
    return 1.0 - (distance / max_len)

def _syllable_similarity(word1: str, word2: str) -> float:
    """Calculate similarity based on syllable structure"""
    def count_syllables(word):
        """Estimate syllable count"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Words ending in 'e' usually don't count the 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)  # Minimum 1 syllable
    
    syl1 = count_syllables(word1)
    syl2 = count_syllables(word2)
    
    if syl1 == syl2:
        return 1.0
    
    max_syl = max(syl1, syl2)
    min_syl = min(syl1, syl2)
    
    return min_syl / max_syl


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
            
            # Update frontend adaptive processing if chunk info available
            if 'processingRate' in chunk_info:
                response['frontend_processing_rate'] = chunk_info['processingRate']
                response['should_adjust_rate'] = avg_confidence < 0.5 or avg_confidence > 0.9
            
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


# =============================================================================
# PHRASE-BASED PRACTICE VIEWS (New Natural Speech Approach)
# =============================================================================

@login_required
@require_http_methods(["POST"])
def start_phrase_practice_session(request):
    """Start a new phrase-based practice session for natural speech"""
    try:
        data = json.loads(request.body)
        text_id = data.get('text_id')
        phrase_length = data.get('phrase_length', 8)  # Default 8 words per phrase
        
        if not text_id:
            return JsonResponse({
                'success': False,
                'error': 'Text ID is required'
            })
        
        text = get_object_or_404(Text, id=text_id, user=request.user)
        
        # Create phrase-based practice engine
        phrase_engine = PhraseBasedPracticeEngine()
        
        # Get first phrase
        first_phrase = phrase_engine.get_practice_phrase(
            text.content, 
            start_pos=0, 
            phrase_length=phrase_length
        )
        
        # Create session
        session = PracticeSession.objects.create(
            user=request.user,
            text=text,
            practice_type='phrase_based',
            started_at=timezone.now()
        )
        
        # Store session data in cache
        session_key = f"phrase_practice_{session.id}_{request.user.id}"
        session_data = {
            'session_id': session.id,
            'text_id': text.id,
            'text_content': text.content,
            'phrase_length': phrase_length,
            'current_position': 0,
            'total_words': len(text.content.split()),
            'phrases_completed': 0,
            'total_attempts': 0,
            'phrase_engine': phrase_engine,
            'created_at': time.time()
        }
        
        cache.set(session_key, session_data, timeout=3600)  # 1 hour timeout
        
        return JsonResponse({
            'success': True,
            'session_key': session_key,
            'phrase_data': first_phrase,
            'session_info': {
                'total_words': session_data['total_words'],
                'phrase_length': phrase_length,
                'progress_percentage': first_phrase['progress_percentage']
            }
        })
        
    except Exception as e:
        logger.error(f"Start phrase practice session error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])  
def process_phrase_speech(request):
    """Process spoken phrase and provide diff-based feedback"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        transcription = data.get('transcription')
        confidence = data.get('confidence', 0.5)
        method = data.get('method', 'unknown')
        
        if not session_key or not transcription:
            return JsonResponse({
                'success': False,
                'error': 'Missing session key or transcription'
            })
        
        # Get session data
        session_data = cache.get(session_key)
        if not session_data:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        phrase_engine = session_data['phrase_engine']
        
        # Get current phrase
        current_phrase = phrase_engine.get_practice_phrase(
            session_data['text_content'],
            start_pos=session_data['current_position'],
            phrase_length=session_data['phrase_length']
        )
        
        # Process speech against expected phrase
        result = phrase_engine.process_phrase_speech(
            transcription,
            current_phrase['phrase_text'],
            context=f"Memorizing text, phrase {session_data['phrases_completed'] + 1}"
        )
        
        # Update session stats
        session_data['total_attempts'] += 1
        
        # Track attempts for this phrase
        phrase_id = f"{session_data['current_position']}_{current_phrase['phrase_text'][:20]}"
        attempt_count = phrase_engine.increment_attempt_count(phrase_id)
        
        # Check if phrase was correct enough to advance OR if we should allow progression
        should_advance = result.get('phrase_correct', False)
        
        # Special logic: Allow advancement with partial success or after multiple attempts
        if not should_advance:
            # If user got most words right (60%+) OR tried 3+ times, allow advancement
            if (result.get('accuracy', 0) >= 60 and len(result.get('missed_words', [])) <= 2) or attempt_count >= 3:
                should_advance = True
                result['advancement_type'] = 'partial_progression'
                result['phrase_correct'] = True  # Override for UI
                
                # Add missed words to review bank
                if result.get('missed_words'):
                    phrase_engine.add_missed_words(result['missed_words'], current_phrase['phrase_text'])
                    result['words_added_to_review'] = len(result['missed_words'])
        
        if should_advance:
            session_data['phrases_completed'] += 1
            session_data['current_position'] = current_phrase['end_position']
            
            # Get next phrase if not complete
            if not current_phrase['is_complete']:
                next_phrase = phrase_engine.get_practice_phrase(
                    session_data['text_content'],
                    start_pos=session_data['current_position'],
                    phrase_length=session_data['phrase_length']
                )
                result['next_phrase'] = next_phrase
            else:
                result['practice_complete'] = True
                
                # Add missed words summary for final review
                missed_words_for_review = phrase_engine.get_missed_words_for_review()
                result['missed_words_summary'] = missed_words_for_review
                
                # Update database session
                try:
                    session = PracticeSession.objects.get(id=session_data['session_id'])
                    session.completed_at = timezone.now()
                    session.accuracy_score = min(100, result.get('accuracy', 0))
                    session.save()
                except PracticeSession.DoesNotExist:
                    pass
        else:
            # Add attempt count info for UI feedback
            result['attempt_count'] = attempt_count
            result['max_attempts'] = 3
            result['can_skip_after'] = 3 - attempt_count if attempt_count < 3 else 0
        
        # Update cache
        cache.set(session_key, session_data, timeout=3600)
        
        # Add session info to response
        result.update({
            'session_info': {
                'phrases_completed': session_data['phrases_completed'],
                'total_attempts': session_data['total_attempts'],
                'current_position': session_data['current_position'],
                'progress_percentage': (session_data['current_position'] / session_data['total_words']) * 100,
                'missed_words_count': len(phrase_engine.missed_words_bank)
            },
            'recognition_method': method,
            'recognition_confidence': confidence,
            'phrase_attempt_count': attempt_count
        })
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Process phrase speech error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def get_next_phrase(request):
    """Get the next phrase for practice"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        if not session_key:
            return JsonResponse({
                'success': False,
                'error': 'Session key is required'
            })
        
        session_data = cache.get(session_key)
        if not session_data:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        phrase_engine = session_data['phrase_engine']
        
        # Get current phrase
        phrase_data = phrase_engine.get_practice_phrase(
            session_data['text_content'],
            start_pos=session_data['current_position'],
            phrase_length=session_data['phrase_length']
        )
        
        return JsonResponse({
            'success': True,
            'phrase_data': phrase_data,
            'session_info': {
                'phrases_completed': session_data['phrases_completed'],
                'total_attempts': session_data['total_attempts'],
                'progress_percentage': phrase_data['progress_percentage']
            }
        })
        
    except Exception as e:
        logger.error(f"Get next phrase error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required  
@require_http_methods(["POST"])
def complete_phrase_practice_session(request):
    """Complete a phrase-based practice session"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        if not session_key:
            return JsonResponse({
                'success': False,
                'error': 'Session key is required'  
            })
        
        session_data = cache.get(session_key)
        if not session_data:
            return JsonResponse({
                'success': False,
                'error': 'Practice session not found or expired'
            })
        
        # Update database session
        try:
            session = PracticeSession.objects.get(id=session_data['session_id'])
            session.completed_at = timezone.now()
            
            # Calculate final accuracy (phrases completed vs total possible phrases)
            total_words = session_data['total_words']
            phrase_length = session_data['phrase_length']
            total_possible_phrases = (total_words + phrase_length - 1) // phrase_length  # Ceiling division
            
            completion_rate = (session_data['phrases_completed'] / max(total_possible_phrases, 1)) * 100
            session.accuracy_score = min(100, completion_rate)
            session.save()
            
            # Get missed words for review
            phrase_engine = session_data['phrase_engine']
            missed_words_for_review = phrase_engine.get_missed_words_for_review()
            
            # Clear session from cache
            cache.delete(session_key)
            
            return JsonResponse({
                'success': True,
                'session_summary': {
                    'phrases_completed': session_data['phrases_completed'],
                    'total_attempts': session_data['total_attempts'],
                    'completion_rate': completion_rate,
                    'total_words_covered': session_data['current_position'],
                    'total_words': total_words,
                    'session_duration': time.time() - session_data['created_at'],
                    'missed_words_for_review': missed_words_for_review[:10]  # Top 10 missed words
                }
            })
            
        except PracticeSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found in database'
            })
        
    except Exception as e:
        logger.error(f"Complete phrase practice session error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })