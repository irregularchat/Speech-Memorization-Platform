"""
Google Cloud Speech-to-Text Streaming Service
Based on the provided real-time streaming approach
"""

import os
import sys
import queue
import threading
import logging
import time
from typing import Dict, Optional, Callable, Any
import json

try:
    import pyaudio
    from google.cloud import speech
    HAS_GOOGLE_SPEECH = True
except ImportError:
    HAS_GOOGLE_SPEECH = False

logger = logging.getLogger(__name__)

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms chunks


class GoogleSpeechStreamingService:
    """Real-time Google Cloud Speech-to-Text streaming service"""
    
    def __init__(self, 
                 language_code: str = "en-US",
                 interim_results: bool = True,
                 single_utterance: bool = False,
                 max_alternatives: int = 1):
        """
        Initialize Google Speech streaming service
        
        Args:
            language_code: Language for speech recognition
            interim_results: Whether to return interim results
            single_utterance: Whether to stop after single utterance
            max_alternatives: Maximum number of recognition alternatives
        """
        if not HAS_GOOGLE_SPEECH:
            raise ImportError("Google Cloud Speech library not available. Install with: pip install google-cloud-speech pyaudio")
        
        self.language_code = language_code
        self.interim_results = interim_results
        self.single_utterance = single_utterance
        self.max_alternatives = max_alternatives
        
        # Audio components
        self.audio_buffer = None
        self.record_thread = None
        self.is_recording = False
        self.client = None
        
        # Callbacks
        self.on_interim_result = None
        self.on_final_result = None
        self.on_error = None
        self.on_speech_start = None
        self.on_speech_end = None
        
        # State tracking
        self.last_interim_result = ""
        self.accumulated_results = []
        self.session_start_time = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Speech client"""
        try:
            # Check for authentication
            credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
            
            if not credentials_path and not project_id:
                logger.warning("Google Cloud credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_CLOUD_PROJECT_ID")
                return
            
            self.client = speech.SpeechClient()
            logger.info("Google Cloud Speech client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Speech client: {str(e)}", exc_info=True)
            self.client = None
    
    def set_callbacks(self,
                     on_interim_result: Optional[Callable[[str, float], None]] = None,
                     on_final_result: Optional[Callable[[str, float], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None,
                     on_speech_start: Optional[Callable[[], None]] = None,
                     on_speech_end: Optional[Callable[[], None]] = None):
        """Set callback functions for speech events"""
        self.on_interim_result = on_interim_result
        self.on_final_result = on_final_result
        self.on_error = on_error
        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end
    
    def _record_audio(self):
        """Continuously read audio from microphone and push to buffer"""
        try:
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )
            
            logger.info("🎙️ Audio recording started")
            if self.on_speech_start:
                self.on_speech_start()
            
            while self.is_recording:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    if self.audio_buffer:
                        self.audio_buffer.put(data)
                except Exception as e:
                    logger.error(f"Error reading audio: {str(e)}", exc_info=True)
                    break
            
            stream.stop_stream()
            stream.close()
            pa.terminate()
            
            logger.info("🛑 Audio recording stopped")
            if self.on_speech_end:
                self.on_speech_end()
                
        except Exception as e:
            logger.error(f"Audio recording error: {str(e)}", exc_info=True)
            if self.on_error:
                self.on_error(f"Audio recording failed: {str(e)}")
    
    def _stream_generator(self):
        """Generate audio chunks for the API"""
        while self.is_recording:
            try:
                chunk = self.audio_buffer.get(timeout=1.0)
                if chunk is None:
                    break
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Stream generator error: {str(e)}", exc_info=True)
                break
    
    def _process_responses(self, responses):
        """Process streaming responses and trigger callbacks"""
        try:
            for response in responses:
                if not response.results:
                    continue
                
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                alternative = result.alternatives[0]
                transcript = alternative.transcript
                confidence = getattr(alternative, 'confidence', 0.0)
                
                if result.is_final:
                    logger.info(f"✔️ Final result: {transcript} (confidence: {confidence:.2f})")
                    self.accumulated_results.append({
                        'transcript': transcript,
                        'confidence': confidence,
                        'timestamp': time.time() - self.session_start_time
                    })
                    
                    if self.on_final_result:
                        self.on_final_result(transcript, confidence)
                    
                    # Clear interim result
                    self.last_interim_result = ""
                    
                    # Stop after single utterance if configured
                    if self.single_utterance:
                        self.stop_streaming()
                        break
                        
                else:
                    # Interim result
                    if transcript != self.last_interim_result:
                        logger.debug(f"⏳ Interim: {transcript}")
                        self.last_interim_result = transcript
                        
                        if self.on_interim_result:
                            self.on_interim_result(transcript, confidence)
                            
        except Exception as e:
            logger.error(f"Response processing error: {str(e)}", exc_info=True)
            if self.on_error:
                self.on_error(f"Response processing failed: {str(e)}")
    
    def start_streaming(self) -> bool:
        """Start streaming speech recognition"""
        if not self.client:
            error_msg = "Google Cloud Speech client not initialized"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(error_msg)
            return False
        
        if self.is_recording:
            logger.warning("Already recording")
            return True
        
        try:
            # Initialize components
            self.audio_buffer = queue.Queue()
            self.is_recording = True
            self.session_start_time = time.time()
            self.accumulated_results = []
            self.last_interim_result = ""
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code=self.language_code,
                max_alternatives=self.max_alternatives,
                enable_automatic_punctuation=True,
                use_enhanced=True  # Use enhanced model if available
            )
            
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=self.interim_results,
                single_utterance=self.single_utterance,
            )
            
            # Start audio recording thread
            self.record_thread = threading.Thread(target=self._record_audio, daemon=True)
            self.record_thread.start()
            
            # Start streaming recognition
            requests = self._stream_generator()
            responses = self.client.streaming_recognize(streaming_config, requests)
            
            # Process responses in separate thread to avoid blocking
            response_thread = threading.Thread(
                target=self._process_responses, 
                args=(responses,), 
                daemon=True
            )
            response_thread.start()
            
            logger.info("Google Cloud Speech streaming started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start streaming: {str(e)}", exc_info=True)
            self.is_recording = False
            if self.on_error:
                self.on_error(f"Failed to start streaming: {str(e)}")
            return False
    
    def stop_streaming(self):
        """Stop streaming speech recognition"""
        if not self.is_recording:
            return
        
        logger.info("Stopping Google Cloud Speech streaming...")
        self.is_recording = False
        
        # Stop audio buffer
        if self.audio_buffer:
            self.audio_buffer.put(None)
        
        # Wait for recording thread to finish
        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(timeout=2.0)
        
        logger.info("Google Cloud Speech streaming stopped")
    
    def get_session_results(self) -> Dict:
        """Get accumulated results from the current session"""
        return {
            'results': self.accumulated_results,
            'session_duration': time.time() - self.session_start_time if self.session_start_time else 0,
            'total_utterances': len(self.accumulated_results)
        }
    
    def is_available(self) -> bool:
        """Check if Google Cloud Speech service is available"""
        return HAS_GOOGLE_SPEECH and self.client is not None


class GoogleSpeechBatchService:
    """Non-streaming Google Cloud Speech service for batch processing"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Speech client"""
        try:
            if not HAS_GOOGLE_SPEECH:
                return
            
            self.client = speech.SpeechClient()
            logger.info("Google Cloud Speech batch client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Speech batch client: {str(e)}", exc_info=True)
            self.client = None
    
    def transcribe_audio(self, audio_data: bytes, audio_format: str = "wav") -> Dict:
        """
        Transcribe audio using Google Cloud Speech
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (wav, flac, etc.)
            
        Returns:
            Transcription result with confidence scores
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Google Cloud Speech client not available',
                'transcription': ''
            }
        
        try:
            # Configure audio
            if audio_format.lower() == "wav":
                encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            elif audio_format.lower() == "flac":
                encoding = speech.RecognitionConfig.AudioEncoding.FLAC
            else:
                encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            
            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=RATE,
                language_code="en-US",
                enable_automatic_punctuation=True,
                use_enhanced=True,
                max_alternatives=3
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Perform recognition
            response = self.client.recognize(config=config, audio=audio)
            
            if not response.results:
                return {
                    'success': True,
                    'transcription': '',
                    'confidence': 0.0,
                    'alternatives': []
                }
            
            # Get best result
            result = response.results[0]
            alternative = result.alternatives[0]
            
            # Get all alternatives
            alternatives = []
            for alt in result.alternatives:
                alternatives.append({
                    'transcript': alt.transcript,
                    'confidence': getattr(alt, 'confidence', 0.0)
                })
            
            return {
                'success': True,
                'transcription': alternative.transcript,
                'confidence': getattr(alternative, 'confidence', 0.0),
                'alternatives': alternatives
            }
            
        except Exception as e:
            logger.error(f"Google Cloud Speech transcription error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'transcription': ''
            }
    
    def is_available(self) -> bool:
        """Check if Google Cloud Speech batch service is available"""
        return HAS_GOOGLE_SPEECH and self.client is not None


def test_google_speech_streaming():
    """Test function for Google Cloud Speech streaming"""
    if not HAS_GOOGLE_SPEECH:
        print("Google Cloud Speech not available")
        return
    
    def on_interim(transcript, confidence):
        sys.stdout.write(f"\r⏳ Interim: {transcript}")
        sys.stdout.flush()
    
    def on_final(transcript, confidence):
        print(f"\n✔️ Final: {transcript} (confidence: {confidence:.2f})")
    
    def on_error(error):
        print(f"\n❌ Error: {error}")
    
    service = GoogleSpeechStreamingService()
    service.set_callbacks(
        on_interim_result=on_interim,
        on_final_result=on_final,
        on_error=on_error
    )
    
    if service.start_streaming():
        try:
            print("🎙️ Listening... Press Ctrl+C to stop")
            while service.is_recording:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            service.stop_streaming()
    else:
        print("Failed to start streaming")


if __name__ == "__main__":
    test_google_speech_streaming()