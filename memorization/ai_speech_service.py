import os
import io
import logging
import tempfile
import base64
from typing import Dict, List, Tuple, Optional
import numpy as np
import json
import time

# Disable librosa caching to avoid Docker issues
os.environ['NUMBA_DISABLE_JIT'] = '1'
os.environ['LIBROSA_CACHE_DIR'] = '/tmp'

import librosa
import soundfile as sf
from difflib import SequenceMatcher
from django.conf import settings
from openai import OpenAI

# Additional speech API imports
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)


class SpeechToTextProcessor:
    """Multi-provider speech-to-text processor with intelligent fallbacks"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.supported_formats = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']
        
        # API provider configuration
        self.providers = {
            'openai': {
                'enabled': bool(os.getenv('OPENAI_API_KEY')),
                'priority': 1,
                'rate_limit': 50,  # requests per minute
                'last_request_time': 0,
                'error_count': 0
            },
            'google': {
                'enabled': bool(os.getenv('GOOGLE_CLOUD_API_KEY')) and HAS_SPEECH_RECOGNITION,
                'priority': 2,
                'rate_limit': 100,
                'last_request_time': 0,
                'error_count': 0
            },
            'azure': {
                'enabled': bool(os.getenv('AZURE_SPEECH_KEY')) and HAS_REQUESTS,
                'priority': 3,
                'rate_limit': 200,
                'last_request_time': 0,
                'error_count': 0
            },
            'local': {
                'enabled': HAS_SPEECH_RECOGNITION,
                'priority': 4,
                'rate_limit': 1000,
                'last_request_time': 0,
                'error_count': 0
            }
        }
        
        # Initialize speech recognition for fallbacks
        if HAS_SPEECH_RECOGNITION:
            self.recognizer = sr.Recognizer()
            # Optimized settings for natural speech
            self.recognizer.energy_threshold = 100  # Lower threshold for quieter speech
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 1.2   # Longer pause tolerance
            self.recognizer.operation_timeout = 15  # Longer timeout for complete sentences
            self.recognizer.phrase_threshold = 0.3  # More sensitive phrase detection
            self.recognizer.non_speaking_duration = 0.8  # Allow natural pauses
        
    def transcribe_audio(self, audio_data: bytes, audio_format: str = 'webm') -> Dict:
        """
        Transcribe audio using multiple providers with intelligent fallbacks
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, wav, mp3, etc.)
            
        Returns:
            Dict with transcription results and confidence metrics
        """
        # Validate audio format
        if audio_format not in self.supported_formats:
            return {
                'success': False,
                'error': f'Unsupported audio format: {audio_format}',
                'transcription': ''
            }
        
        # Try providers in order of priority and availability
        providers_to_try = self._get_available_providers()
        
        for provider_name in providers_to_try:
            try:
                result = self._transcribe_with_provider(audio_data, audio_format, provider_name)
                if result['success']:
                    result['provider'] = provider_name
                    self._update_provider_success(provider_name)
                    return result
                else:
                    logger.warning(f"{provider_name} provider failed: {result.get('error', 'Unknown error')}")
                    self._update_provider_error(provider_name)
                    
            except Exception as e:
                logger.error(f"{provider_name} provider exception: {str(e)}")
                self._update_provider_error(provider_name)
                continue
        
        # All providers failed
        return {
            'success': False,
            'error': 'All speech recognition providers failed',
            'transcription': '',
            'providers_tried': providers_to_try
        }
    
    def _get_available_providers(self) -> List[str]:
        """Get list of available providers sorted by priority and health"""
        available = []
        
        for name, config in self.providers.items():
            if config['enabled'] and self._is_provider_healthy(name):
                available.append((name, config['priority'], config['error_count']))
        
        # Sort by priority (lower is better) and error count (lower is better)
        available.sort(key=lambda x: (x[1], x[2]))
        
        return [name for name, _, _ in available]
    
    def _is_provider_healthy(self, provider_name: str) -> bool:
        """Check if provider is healthy (not rate limited or too many errors)"""
        config = self.providers[provider_name]
        
        # Check rate limiting
        time_since_last = time.time() - config['last_request_time']
        if time_since_last < 60 / config['rate_limit']:  # Convert to seconds
            return False
        
        # Check error threshold
        if config['error_count'] > 5:
            return False
        
        return True
    
    def _transcribe_with_provider(self, audio_data: bytes, audio_format: str, provider: str) -> Dict:
        """Transcribe with specific provider"""
        self.providers[provider]['last_request_time'] = time.time()
        
        if provider == 'openai':
            return self._transcribe_openai(audio_data, audio_format)
        elif provider == 'google':
            return self._transcribe_google(audio_data, audio_format)
        elif provider == 'azure':
            return self._transcribe_azure(audio_data, audio_format)
        elif provider == 'local':
            return self._transcribe_local(audio_data, audio_format)
        else:
            return {'success': False, 'error': f'Unknown provider: {provider}'}
    
    def _transcribe_openai(self, audio_data: bytes, audio_format: str) -> Dict:
        """Transcribe using OpenAI Whisper"""
        with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file.flush()
            
            try:
                with open(temp_file.name, 'rb') as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        language="en",
                        prompt="This is conversational speech for memorization practice. Please transcribe naturally spoken sentences.",
                        temperature=0.0
                    )
                
                transcription = transcript.text.strip()
                confidence = self._calculate_confidence(transcript)
                
                return {
                    'success': True,
                    'transcription': transcription,
                    'confidence': confidence,
                    'language': getattr(transcript, 'language', 'en'),
                    'duration': getattr(transcript, 'duration', 0),
                    'segments': getattr(transcript, 'segments', [])
                }
                
            finally:
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass
    
    def _transcribe_google(self, audio_data: bytes, audio_format: str) -> Dict:
        """Transcribe using Google Speech-to-Text"""
        if not HAS_SPEECH_RECOGNITION:
            return {'success': False, 'error': 'Speech recognition library not available'}
        
        try:
            # Convert to WAV if needed
            if audio_format != 'wav':
                audio_data = AudioProcessor.process_webm_audio(audio_data)
            
            with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                with sr.AudioFile(temp_file.name) as source:
                    audio = self.recognizer.record(source)
                
                # Try Google Cloud Speech if API key available
                api_key = os.getenv('GOOGLE_CLOUD_API_KEY')
                if api_key:
                    transcription = self.recognizer.recognize_google_cloud(
                        audio, 
                        credentials_json=api_key,
                        language='en-US'
                    )
                else:
                    # Fallback to free Google service
                    transcription = self.recognizer.recognize_google(audio, language='en-US')
                
                return {
                    'success': True,
                    'transcription': transcription,
                    'confidence': 0.7,  # Default confidence
                    'language': 'en'
                }
                
        except sr.UnknownValueError:
            return {'success': False, 'error': 'Google could not understand audio'}
        except sr.RequestError as e:
            return {'success': False, 'error': f'Google service error: {str(e)}'}
    
    def _transcribe_azure(self, audio_data: bytes, audio_format: str) -> Dict:
        """Transcribe using Azure Speech Services"""
        if not HAS_REQUESTS:
            return {'success': False, 'error': 'Requests library not available'}
        
        api_key = os.getenv('AZURE_SPEECH_KEY')
        region = os.getenv('AZURE_SPEECH_REGION', 'eastus')
        
        if not api_key:
            return {'success': False, 'error': 'Azure Speech API key not configured'}
        
        try:
            # Convert to WAV if needed
            if audio_format != 'wav':
                audio_data = AudioProcessor.process_webm_audio(audio_data)
            
            url = f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
            headers = {
                'Ocp-Apim-Subscription-Key': api_key,
                'Content-Type': 'audio/wav',
                'Accept': 'application/json'
            }
            params = {
                'language': 'en-US',
                'format': 'detailed'
            }
            
            response = requests.post(url, headers=headers, params=params, data=audio_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('RecognitionStatus') == 'Success':
                    best_result = result['NBest'][0] if result.get('NBest') else result
                    return {
                        'success': True,
                        'transcription': best_result.get('Display', ''),
                        'confidence': best_result.get('Confidence', 0.7),
                        'language': 'en'
                    }
            
            return {'success': False, 'error': f'Azure API error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': f'Azure transcription failed: {str(e)}'}
    
    def _transcribe_local(self, audio_data: bytes, audio_format: str) -> Dict:
        """Transcribe using local speech recognition (offline fallback)"""
        if not HAS_SPEECH_RECOGNITION:
            return {'success': False, 'error': 'Speech recognition library not available'}
        
        try:
            # Convert to WAV if needed
            if audio_format != 'wav':
                audio_data = AudioProcessor.process_webm_audio(audio_data)
            
            with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                with sr.AudioFile(temp_file.name) as source:
                    audio = self.recognizer.record(source)
                
                # Try built-in recognition engines
                try:
                    transcription = self.recognizer.recognize_sphinx(audio)
                    confidence = 0.5  # Lower confidence for local recognition
                except:
                    # Ultimate fallback - return empty but successful result
                    return {
                        'success': True,
                        'transcription': '',
                        'confidence': 0.1,
                        'language': 'en',
                        'note': 'Local recognition failed, returned empty result'
                    }
                
                return {
                    'success': True,
                    'transcription': transcription,
                    'confidence': confidence,
                    'language': 'en'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Local transcription failed: {str(e)}'}
    
    def _update_provider_success(self, provider_name: str):
        """Update provider stats on success"""
        if provider_name in self.providers:
            self.providers[provider_name]['error_count'] = max(0, self.providers[provider_name]['error_count'] - 1)
    
    def _update_provider_error(self, provider_name: str):
        """Update provider stats on error"""
        if provider_name in self.providers:
            self.providers[provider_name]['error_count'] += 1
    
    def _calculate_confidence(self, transcript) -> float:
        """Calculate confidence score from Whisper response"""
        if hasattr(transcript, 'segments') and transcript.segments:
            # Average confidence from segments if available
            confidences = []
            for segment in transcript.segments:
                if hasattr(segment, 'avg_logprob'):
                    # Convert log probability to confidence (rough approximation)
                    confidence = min(1.0, max(0.0, (segment.avg_logprob + 1.0)))
                    confidences.append(confidence)
            
            if confidences:
                return sum(confidences) / len(confidences)
        
        # Default confidence based on transcription length and quality
        if hasattr(transcript, 'text'):
            text_length = len(transcript.text.strip())
            if text_length == 0:
                return 0.0
            elif text_length < 5:
                return 0.6
            else:
                return 0.8
        
        return 0.5


class PhraseBasedSpeechAnalyzer:
    """Analyzes full phrases/sentences against expected text with AI-powered insights"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def analyze_phrase_accuracy(self, spoken_text: str, expected_text: str, 
                                context: str = "") -> Dict:
        """
        Analyze full phrase/sentence accuracy with word-level diff highlighting
        
        Args:
            spoken_text: What the user actually said (full phrase/sentence)
            expected_text: What they should have said (full phrase/sentence)
            context: Additional context for better analysis
            
        Returns:
            Detailed analysis with word-level highlighting and corrections
        """
        try:
            # Clean and normalize text
            spoken_clean = self._normalize_text(spoken_text)
            expected_clean = self._normalize_text(expected_text)
            
            # Calculate similarity
            similarity = self._calculate_similarity(spoken_clean, expected_clean)
            
            # Generate word-level diff
            word_diff = self._generate_word_diff(spoken_clean, expected_clean)
            
            # Create highlighted HTML for display
            highlighted_html = self._create_highlighted_display(word_diff, expected_clean)
            
            # Get AI-powered feedback
            ai_feedback = None
            if similarity < 0.9:  # Get AI feedback for non-perfect matches
                ai_feedback = self._get_ai_phrase_feedback(spoken_clean, expected_clean, word_diff, context)
            
            # Calculate phrase-level accuracy
            phrase_accuracy = self._calculate_phrase_accuracy(word_diff)
            
            return {
                'success': True,
                'overall_accuracy': similarity * 100,
                'phrase_accuracy': phrase_accuracy,
                'similarity_score': similarity,
                'word_differences': word_diff,
                'highlighted_html': highlighted_html,
                'spoken_text': spoken_clean,
                'expected_text': expected_clean,
                'ai_feedback': ai_feedback,
                'needs_retry': phrase_accuracy < 80,  # Suggest retry if accuracy below 80%
                'perfect_match': similarity > 0.95
            }
            
        except Exception as e:
            logger.error(f"Phrase analysis error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'overall_accuracy': 0
            }
    
    def _calculate_similarity(self, spoken: str, expected: str) -> float:
        """Calculate text similarity using sequence matching"""
        return SequenceMatcher(None, spoken.lower(), expected.lower()).ratio()
    
    def _calculate_word_accuracy(self, spoken: str, expected: str) -> Dict:
        """Calculate word-level accuracy statistics"""
        spoken_words = spoken.lower().split()
        expected_words = expected.lower().split()
        
        correct_words = 0
        total_words = len(expected_words)
        
        # Simple word matching (can be enhanced with fuzzy matching)
        for i, expected_word in enumerate(expected_words):
            if i < len(spoken_words) and spoken_words[i] == expected_word:
                correct_words += 1
        
        return {
            'correct_words': correct_words,
            'total_words': total_words,
            'accuracy_percentage': (correct_words / max(total_words, 1)) * 100,
            'missing_words': max(0, total_words - len(spoken_words)),
            'extra_words': max(0, len(spoken_words) - total_words)
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        import re
        # Remove extra whitespace and punctuation for comparison
        text = re.sub(r'[^\w\s]', '', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _generate_word_diff(self, spoken: str, expected: str) -> List[Dict]:
        """Generate word-level diff using sequence matching"""
        from difflib import SequenceMatcher
        
        spoken_words = spoken.split()
        expected_words = expected.split()
        
        matcher = SequenceMatcher(None, expected_words, spoken_words)
        differences = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Words match correctly
                for i in range(i1, i2):
                    differences.append({
                        'position': i,
                        'expected_word': expected_words[i],
                        'spoken_word': expected_words[i],  # Same as expected
                        'type': 'correct',
                        'status': 'correct'
                    })
            elif tag == 'replace':
                # Words were substituted
                for i in range(i1, i2):
                    spoken_word = spoken_words[j1 + (i - i1)] if j1 + (i - i1) < len(spoken_words) else '[MISSING]'
                    differences.append({
                        'position': i,
                        'expected_word': expected_words[i],
                        'spoken_word': spoken_word,
                        'type': 'substitution',
                        'status': 'error'
                    })
            elif tag == 'delete':
                # Words were missing in spoken text
                for i in range(i1, i2):
                    differences.append({
                        'position': i,
                        'expected_word': expected_words[i],
                        'spoken_word': '[MISSING]',
                        'type': 'missing',
                        'status': 'error'
                    })
            elif tag == 'insert':
                # Extra words in spoken text
                for j in range(j1, j2):
                    differences.append({
                        'position': len(expected_words) + j - j1,
                        'expected_word': '[EXTRA]',
                        'spoken_word': spoken_words[j],
                        'type': 'extra',
                        'status': 'error'
                    })
        
        return differences
    
    def _create_highlighted_display(self, word_diff: List[Dict], expected_text: str) -> str:
        """Create HTML with highlighted errors"""
        html_parts = []
        expected_words = expected_text.split()
        
        for diff in word_diff:
            if diff['type'] == 'correct':
                html_parts.append(f'<span class="word-correct">{diff["expected_word"]}</span>')
            elif diff['type'] in ['substitution', 'missing']:
                html_parts.append(f'<span class="word-error" title="You said: {diff["spoken_word"]}">{diff["expected_word"]}</span>')
            # Skip extra words for now - they'll be handled separately
        
        return ' '.join(html_parts)
    
    def _calculate_phrase_accuracy(self, word_diff: List[Dict]) -> float:
        """Calculate overall phrase accuracy percentage"""
        if not word_diff:
            return 0.0
        
        correct_words = sum(1 for diff in word_diff if diff['status'] == 'correct')
        total_words = len([diff for diff in word_diff if diff['type'] != 'extra'])
        
        return (correct_words / max(total_words, 1)) * 100
    
    def _classify_error(self, expected: str, spoken: str) -> str:
        """Classify the type of speech error"""
        if expected == "[MISSING]":
            return "extra_word"
        elif spoken == "[MISSING]":
            return "missing_word"
        elif self._is_similar_pronunciation(expected, spoken):
            return "pronunciation"
        else:
            return "substitution"
    
    def _is_similar_pronunciation(self, word1: str, word2: str) -> bool:
        """Check if words might be pronunciation variants"""
        # Simple phonetic similarity check
        if len(word1) == len(word2):
            differences = sum(c1 != c2 for c1, c2 in zip(word1, word2))
            return differences <= 2
        return False
    
    def _analyze_pronunciation(self, spoken: str, expected: str) -> Dict:
        """Analyze pronunciation patterns"""
        spoken_words = spoken.lower().split()
        expected_words = expected.lower().split()
        
        pronunciation_issues = []
        
        for i, (exp, spk) in enumerate(zip(expected_words, spoken_words)):
            if exp != spk and self._is_similar_pronunciation(exp, spk):
                pronunciation_issues.append({
                    'position': i,
                    'expected_word': exp,
                    'spoken_word': spk,
                    'issue_type': 'pronunciation_variant'
                })
        
        return {
            'pronunciation_issues': pronunciation_issues,
            'has_issues': len(pronunciation_issues) > 0
        }
    
    def _get_ai_phrase_feedback(self, spoken: str, expected: str, word_diff: List[Dict], context: str) -> Optional[Dict]:
        """Get AI-powered feedback for phrase-level analysis"""
        try:
            # Summarize errors for AI context
            errors = [diff for diff in word_diff if diff['status'] == 'error']
            error_summary = ", ".join([f"{diff['expected_word']} (said: {diff['spoken_word']})" for diff in errors[:5]])
            
            prompt = f"""
            Analyze this speech memorization attempt for a full phrase/sentence:
            
            Expected: "{expected}"
            User spoke: "{spoken}"
            Word-level errors: {error_summary if errors else "None - perfect match!"}
            Context: {context or "Speech memorization practice"}
            
            Provide specific, encouraging feedback focusing on:
            1. Overall phrase flow and natural speech
            2. Specific word corrections needed
            3. Memory vs pronunciation issues
            4. Tips for improvement
            
            Keep feedback constructive and encouraging. 2-3 sentences max.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful speech coach providing feedback for natural phrase-based speech practice. Focus on helping users speak naturally while memorizing text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            feedback = response.choices[0].message.content.strip()
            
            return {
                'ai_analysis': feedback,
                'error_count': len(errors),
                'has_feedback': True
            }
            
        except Exception as e:
            logger.warning(f"AI phrase feedback generation failed: {str(e)}")
            return None
    
    def _generate_suggestions(self, spoken: str, expected: str) -> List[str]:
        """Generate helpful suggestions for improvement"""
        suggestions = []
        
        spoken_words = spoken.lower().split()
        expected_words = expected.lower().split()
        
        # Length-based suggestions
        if len(spoken_words) < len(expected_words):
            suggestions.append("Try to include all words from the text. Some words might be missing.")
        elif len(spoken_words) > len(expected_words):
            suggestions.append("Focus on the exact text. You might be adding extra words.")
        
        # Similarity-based suggestions
        similarity = self._calculate_similarity(spoken, expected)
        if similarity < 0.5:
            suggestions.append("This section needs more practice. Try breaking it into smaller chunks.")
        elif similarity < 0.8:
            suggestions.append("Good effort! Focus on the specific words that are different.")
        else:
            suggestions.append("Great job! Just a few minor adjustments needed.")
        
        return suggestions


# Compatibility alias for existing code
IntelligentSpeechAnalyzer = PhraseBasedSpeechAnalyzer


class PhraseBasedPracticeEngine:
    """Practice engine that works with phrases/sentences instead of individual words"""
    
    def __init__(self):
        self.speech_analyzer = PhraseBasedSpeechAnalyzer()
        self.missed_words_bank = []  # Track words to review later
        self.attempt_counts = {}     # Track attempts per phrase
        
    def get_practice_phrase(self, text: str, start_pos: int = 0, phrase_length: int = 10) -> Dict:
        """Get a phrase for practice (multiple words)"""
        words = text.split()
        
        # Get phrase starting from start_pos
        end_pos = min(start_pos + phrase_length, len(words))
        phrase_words = words[start_pos:end_pos]
        phrase_text = ' '.join(phrase_words)
        
        return {
            'phrase_text': phrase_text,
            'start_position': start_pos,
            'end_position': end_pos,
            'word_count': len(phrase_words),
            'is_complete': end_pos >= len(words),
            'progress_percentage': (end_pos / len(words)) * 100
        }
    
    def add_missed_words(self, words: List[str], phrase_context: str):\n        \"\"\"Add missed words to review bank\"\"\"\n        import time\n        for word in words:\n            if word not in [item['word'] for item in self.missed_words_bank]:\n                self.missed_words_bank.append({\n                    'word': word,\n                    'context': phrase_context,\n                    'missed_count': 1,\n                    'timestamp': time.time()\n                })\n            else:\n                # Increment miss count for existing word\n                for item in self.missed_words_bank:\n                    if item['word'] == word:\n                        item['missed_count'] += 1\n                        break\n    \n    def get_missed_words_for_review(self) -> List[Dict]:\n        \"\"\"Get words that need review\"\"\"\n        # Sort by miss count and recency\n        import time\n        return sorted(\n            self.missed_words_bank,\n            key=lambda x: (x['missed_count'], -x['timestamp']),\n            reverse=True\n        )\n    \n    def should_allow_skip(self, phrase_id: str, attempt_count: int) -> bool:\n        \"\"\"Determine if user should be allowed to skip after multiple attempts\"\"\"\n        # Allow skip after 3 attempts\n        return attempt_count >= 3\n    \n    def increment_attempt_count(self, phrase_id: str) -> int:\n        \"\"\"Track attempt counts per phrase\"\"\"\n        if phrase_id not in self.attempt_counts:\n            self.attempt_counts[phrase_id] = 0\n        self.attempt_counts[phrase_id] += 1\n        return self.attempt_counts[phrase_id]
    
    def process_phrase_speech(self, spoken_text: str, expected_phrase: str, context: str = "") -> Dict:
        """Process spoken phrase with smart progression logic"""
        try:
            # Analyze the full phrase
            analysis = self.speech_analyzer.analyze_phrase_accuracy(
                spoken_text, expected_phrase, context
            )
            
            if not analysis['success']:
                return analysis
            
            # Smart progression logic - multiple ways to advance
            accuracy = analysis['phrase_accuracy']
            
            # Determine advancement strategy
            advancement_result = self._determine_advancement(
                analysis['word_differences'], 
                accuracy, 
                expected_phrase
            )
            
            return {
                'success': True,
                'phrase_correct': advancement_result['should_advance'],
                'advancement_type': advancement_result['type'],
                'accuracy': accuracy,
                'similarity_score': analysis['similarity_score'],
                'highlighted_html': analysis['highlighted_html'],
                'word_differences': analysis['word_differences'],
                'missed_words': advancement_result['missed_words'],
                'ai_feedback': analysis.get('ai_feedback'),
                'needs_retry': advancement_result['needs_retry'],
                'perfect_match': analysis['perfect_match'],
                'spoken_text': analysis['spoken_text'],
                'expected_text': analysis['expected_text'],
                'progress_message': advancement_result['message']
            }
            
        except Exception as e:
            logger.error(f"Phrase processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'phrase_correct': False
            }
    
    def _determine_advancement(self, word_differences: List[Dict], accuracy: float, expected_phrase: str) -> Dict:
        """Determine if user should advance and how"""
        total_words = len(expected_phrase.split())
        correct_words = len([diff for diff in word_differences if diff['status'] == 'correct'])
        error_words = [diff for diff in word_differences if diff['status'] == 'error']
        
        # Perfect or near-perfect
        if accuracy >= 95:
            return {
                'should_advance': True,
                'type': 'perfect',
                'message': 'Perfect! Moving to next phrase.',
                'missed_words': [],
                'needs_retry': False
            }
        
        # Very good - minor mistakes allowed
        elif accuracy >= 80:
            return {
                'should_advance': True,
                'type': 'good',
                'message': f'Great job! {accuracy:.0f}% accuracy - continuing.',
                'missed_words': [diff['expected_word'] for diff in error_words],
                'needs_retry': False
            }
        
        # Decent - but check if it's mostly correct with just a few key misses
        elif accuracy >= 60:
            # If user got most words right but missed just 1-2 key words, allow progression
            if len(error_words) <= 2 and correct_words >= total_words * 0.6:
                return {
                    'should_advance': True,
                    'type': 'partial_with_skips',
                    'message': f'Good progress! We\'ll review the missed words later.',
                    'missed_words': [diff['expected_word'] for diff in error_words],
                    'needs_retry': False
                }
            else:
                return {
                    'should_advance': False,
                    'type': 'needs_improvement',
                    'message': f'Getting there! {accuracy:.0f}% - try again focusing on the highlighted words.',
                    'missed_words': [diff['expected_word'] for diff in error_words],
                    'needs_retry': True
                }
        
        # Struggling - offer more chances but eventually allow skip
        elif accuracy >= 40:
            return {
                'should_advance': False,
                'type': 'struggling',
                'message': f'Keep trying! {accuracy:.0f}% accuracy. Focus on the red highlighted words.',
                'missed_words': [diff['expected_word'] for diff in error_words],
                'needs_retry': True
            }
        
        # Very low accuracy - definitely needs retry
        else:
            return {
                'should_advance': False,
                'type': 'retry_needed',
                'message': f'Let\'s try that again. Focus on speaking clearly.',
                'missed_words': [diff['expected_word'] for diff in error_words],
                'needs_retry': True
            }


class AudioProcessor:
    """Process and optimize audio for speech recognition"""
    
    @staticmethod
    def process_webm_audio(audio_data: bytes) -> bytes:
        """
        Process WebM audio data for optimal Whisper processing
        
        Args:
            audio_data: Raw WebM audio bytes
            
        Returns:
            Processed audio bytes (WAV format)
        """
        try:
            # Convert to numpy array using librosa
            with tempfile.NamedTemporaryFile(suffix='.webm') as temp_input:
                temp_input.write(audio_data)
                temp_input.flush()
                
                # Load and resample audio
                audio, sr = librosa.load(temp_input.name, sr=16000, mono=True)
                
                # Apply noise reduction and normalization
                audio = AudioProcessor._enhance_audio(audio)
                
                # Convert to WAV bytes
                with io.BytesIO() as wav_buffer:
                    sf.write(wav_buffer, audio, sr, format='WAV')
                    return wav_buffer.getvalue()
                    
        except Exception as e:
            logger.error(f"Audio processing error: {str(e)}")
            # Return original data if processing fails
            return audio_data
    
    @staticmethod
    def _enhance_audio(audio: np.ndarray) -> np.ndarray:
        """Apply audio enhancement techniques"""
        # Normalize audio
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))
        
        # Simple noise gate (remove very quiet sections)
        noise_threshold = 0.01
        audio[np.abs(audio) < noise_threshold] = 0
        
        return audio
    
    @staticmethod
    def validate_audio_quality(audio_data: bytes) -> Dict:
        """Validate audio quality and provide feedback"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.webm') as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                # Load audio for analysis
                audio, sr = librosa.load(temp_file.name, sr=None, mono=True)
                
                # Calculate quality metrics
                duration = len(audio) / sr
                rms_energy = np.sqrt(np.mean(audio**2))
                zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(audio))
                
                # Quality assessment
                quality_score = 1.0
                issues = []
                
                if duration < 0.5:
                    quality_score *= 0.5
                    issues.append("Audio too short")
                
                if rms_energy < 0.01:
                    quality_score *= 0.7
                    issues.append("Audio level too low")
                elif rms_energy > 0.8:
                    quality_score *= 0.8
                    issues.append("Audio might be clipped")
                
                return {
                    'quality_score': quality_score,
                    'duration': duration,
                    'energy_level': rms_energy,
                    'issues': issues,
                    'suitable_for_recognition': quality_score > 0.6
                }
                
        except Exception as e:
            logger.error(f"Audio quality validation error: {str(e)}")
            return {
                'quality_score': 0.5,
                'issues': ['Could not analyze audio quality'],
                'suitable_for_recognition': True  # Assume it's ok if we can't analyze
            }