import os
import io
import logging
import tempfile
import base64
from typing import Dict, List, Tuple, Optional
import numpy as np

# Disable librosa caching to avoid Docker issues
os.environ['NUMBA_DISABLE_JIT'] = '1'
os.environ['LIBROSA_CACHE_DIR'] = '/tmp'

import librosa
import soundfile as sf
from difflib import SequenceMatcher
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class SpeechToTextProcessor:
    """OpenAI Whisper-powered speech-to-text processor with intelligent analysis"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.supported_formats = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']
        
    def transcribe_audio(self, audio_data: bytes, audio_format: str = 'webm') -> Dict:
        """
        Transcribe audio using OpenAI Whisper API
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, wav, mp3, etc.)
            
        Returns:
            Dict with transcription results and confidence metrics
        """
        try:
            # Validate audio format
            if audio_format not in self.supported_formats:
                return {
                    'success': False,
                    'error': f'Unsupported audio format: {audio_format}',
                    'transcription': ''
                }
            
            # Create temporary file for Whisper API
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                try:
                    # Process with Whisper
                    with open(temp_file.name, 'rb') as audio_file:
                        transcript = self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="verbose_json",
                            language="en"  # Can be made configurable
                        )
                    
                    # Extract transcription and confidence
                    transcription = transcript.text.strip()
                    
                    # Calculate confidence based on segment data if available
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
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file.name)
                    except OSError:
                        pass
                        
        except Exception as e:
            logger.error(f"Whisper transcription error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transcription': ''
            }
    
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


class IntelligentSpeechAnalyzer:
    """Analyzes speech against expected text with AI-powered insights"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def analyze_speech_accuracy(self, spoken_text: str, expected_text: str, 
                              context: str = "") -> Dict:
        """
        Analyze speech accuracy with detailed feedback
        
        Args:
            spoken_text: What the user actually said
            expected_text: What they should have said
            context: Additional context for better analysis
            
        Returns:
            Detailed analysis with corrections and suggestions
        """
        try:
            # Basic similarity analysis
            similarity = self._calculate_similarity(spoken_text, expected_text)
            word_accuracy = self._calculate_word_accuracy(spoken_text, expected_text)
            
            # Get AI-powered feedback for complex cases
            ai_feedback = None
            if similarity < 0.8 or len(spoken_text.split()) != len(expected_text.split()):
                ai_feedback = self._get_ai_feedback(spoken_text, expected_text, context)
            
            return {
                'success': True,
                'overall_accuracy': similarity * 100,
                'word_accuracy': word_accuracy,
                'similarity_score': similarity,
                'word_differences': self._find_word_differences(spoken_text, expected_text),
                'pronunciation_feedback': self._analyze_pronunciation(spoken_text, expected_text),
                'ai_feedback': ai_feedback,
                'suggestions': self._generate_suggestions(spoken_text, expected_text)
            }
            
        except Exception as e:
            logger.error(f"Speech analysis error: {str(e)}")
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
    
    def _find_word_differences(self, spoken: str, expected: str) -> List[Dict]:
        """Find specific word differences with positions"""
        spoken_words = spoken.lower().split()
        expected_words = expected.lower().split()
        
        differences = []
        max_len = max(len(spoken_words), len(expected_words))
        
        for i in range(max_len):
            expected_word = expected_words[i] if i < len(expected_words) else "[MISSING]"
            spoken_word = spoken_words[i] if i < len(spoken_words) else "[MISSING]"
            
            if expected_word != spoken_word:
                differences.append({
                    'position': i,
                    'expected': expected_word,
                    'spoken': spoken_word,
                    'type': self._classify_error(expected_word, spoken_word)
                })
        
        return differences
    
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
    
    def _get_ai_feedback(self, spoken: str, expected: str, context: str) -> Optional[Dict]:
        """Get AI-powered feedback for complex speech analysis"""
        try:
            prompt = f"""
            Analyze this speech practice attempt and provide helpful feedback:
            
            Expected text: "{expected}"
            User spoke: "{spoken}"
            Context: {context or "Speech memorization practice"}
            
            Please provide:
            1. What the user did well
            2. Specific areas for improvement
            3. Tips for better pronunciation or memorization
            4. Whether this was likely a memory issue or pronunciation issue
            
            Keep feedback encouraging and constructive. Limit to 2-3 sentences.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful speech coach providing constructive feedback for speech memorization practice."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            feedback = response.choices[0].message.content.strip()
            
            return {
                'ai_analysis': feedback,
                'has_feedback': True
            }
            
        except Exception as e:
            logger.warning(f"AI feedback generation failed: {str(e)}")
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