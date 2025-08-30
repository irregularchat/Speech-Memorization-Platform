"""
Real-time streaming speech recognition views using Google Cloud Speech
"""

import json
import logging
import asyncio
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer

from .google_speech_service import GoogleSpeechStreamingService
from .ai_speech_service import PhraseBasedPracticeEngine

logger = logging.getLogger(__name__)

# Global streaming sessions
streaming_sessions = {}


class StreamingSpeechConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time speech recognition"""
    
    async def connect(self):
        self.session_key = self.scope['url_route']['kwargs']['session_key']
        self.group_name = f'speech_stream_{self.session_key}'
        
        # Join session group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Initialize Google Speech streaming service
        try:
            self.speech_service = GoogleSpeechStreamingService(
                language_code="en-US",
                interim_results=True,
                single_utterance=False
            )
            
            # Set up callbacks
            self.speech_service.set_callbacks(
                on_interim_result=self.on_interim_result,
                on_final_result=self.on_final_result,
                on_error=self.on_speech_error,
                on_speech_start=self.on_speech_start,
                on_speech_end=self.on_speech_end
            )
            
            # Start streaming
            if self.speech_service.start_streaming():
                await self.send(text_data=json.dumps({
                    'type': 'status',
                    'message': 'Speech recognition started',
                    'status': 'listening'
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Failed to start speech recognition'
                }))
                
        except Exception as e:
            logger.error(f"Error initializing speech service: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Initialization error: {str(e)}'
            }))
    
    async def disconnect(self, close_code):
        # Stop speech recognition
        if hasattr(self, 'speech_service'):
            self.speech_service.stop_streaming()
        
        # Leave session group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'start_listening':
                if hasattr(self, 'speech_service'):
                    if self.speech_service.start_streaming():
                        await self.send(text_data=json.dumps({
                            'type': 'status',
                            'message': 'Listening started',
                            'status': 'listening'
                        }))
                    else:
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'message': 'Failed to start listening'
                        }))
            
            elif message_type == 'stop_listening':
                if hasattr(self, 'speech_service'):
                    self.speech_service.stop_streaming()
                    await self.send(text_data=json.dumps({
                        'type': 'status',
                        'message': 'Listening stopped',
                        'status': 'stopped'
                    }))
            
            elif message_type == 'process_phrase':
                # Process completed phrase against expected text
                transcript = data.get('transcript', '')
                await self.process_phrase_result(transcript)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON data'
            }))
        except Exception as e:
            logger.error(f"WebSocket receive error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Processing error: {str(e)}'
            }))
    
    def on_interim_result(self, transcript: str, confidence: float):
        """Handle interim speech recognition results"""
        asyncio.create_task(self.send(text_data=json.dumps({
            'type': 'interim_result',
            'transcript': transcript,
            'confidence': confidence,
            'is_final': False
        })))
    
    def on_final_result(self, transcript: str, confidence: float):
        """Handle final speech recognition results"""
        asyncio.create_task(self.send(text_data=json.dumps({
            'type': 'final_result',
            'transcript': transcript,
            'confidence': confidence,
            'is_final': True
        })))
        
        # Auto-process the phrase
        asyncio.create_task(self.process_phrase_result(transcript, confidence))
    
    def on_speech_error(self, error: str):
        """Handle speech recognition errors"""
        asyncio.create_task(self.send(text_data=json.dumps({
            'type': 'error',
            'message': error
        })))
    
    def on_speech_start(self):
        """Handle speech start event"""
        asyncio.create_task(self.send(text_data=json.dumps({
            'type': 'status',
            'message': 'Speech detected',
            'status': 'speaking'
        })))
    
    def on_speech_end(self):
        """Handle speech end event"""
        asyncio.create_task(self.send(text_data=json.dumps({
            'type': 'status',
            'message': 'Speech ended',
            'status': 'processing'
        })))
    
    async def process_phrase_result(self, transcript: str, confidence: float = 0.0):
        """Process the transcript against expected phrase"""
        try:
            # Get session data
            session_data = cache.get(self.session_key)
            if not session_data:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Session not found'
                }))
                return
            
            phrase_engine = session_data.get('phrase_engine')
            if not phrase_engine:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Phrase engine not found'
                }))
                return
            
            # Get current phrase
            current_phrase = phrase_engine.get_practice_phrase(
                session_data['text_content'],
                start_pos=session_data['current_position'],
                phrase_length=session_data['phrase_length']
            )
            
            # Process speech against expected phrase
            result = phrase_engine.process_phrase_speech(
                transcript,
                current_phrase['phrase_text'],
                context=f"Streaming practice, phrase {session_data['phrases_completed'] + 1}"
            )
            
            # Update session stats
            session_data['total_attempts'] += 1
            
            # Determine advancement
            phrase_id = f"{session_data['current_position']}_{current_phrase['phrase_text'][:20]}"
            attempt_count = phrase_engine.increment_attempt_count(phrase_id)
            
            should_advance = result.get('phrase_correct', False)
            
            # Smart progression logic
            if not should_advance:
                if (result.get('accuracy', 0) >= 60 and len(result.get('missed_words', [])) <= 2) or attempt_count >= 3:
                    should_advance = True
                    result['advancement_type'] = 'partial_progression'
                    result['phrase_correct'] = True
                    
                    if result.get('missed_words'):
                        phrase_engine.add_missed_words(result['missed_words'], current_phrase['phrase_text'])
            
            if should_advance:
                session_data['phrases_completed'] += 1
                session_data['current_position'] = current_phrase['end_position']
                
                if not current_phrase['is_complete']:
                    next_phrase = phrase_engine.get_practice_phrase(
                        session_data['text_content'],
                        start_pos=session_data['current_position'],
                        phrase_length=session_data['phrase_length']
                    )
                    result['next_phrase'] = next_phrase
                else:
                    result['practice_complete'] = True
            
            # Update cache
            cache.set(self.session_key, session_data, timeout=3600)
            
            # Send result back to client
            await self.send(text_data=json.dumps({
                'type': 'phrase_result',
                'result': result,
                'session_info': {
                    'phrases_completed': session_data['phrases_completed'],
                    'total_attempts': session_data['total_attempts'],
                    'current_position': session_data['current_position'],
                    'progress_percentage': (session_data['current_position'] / session_data['total_words']) * 100,
                    'missed_words_count': len(phrase_engine.missed_words_bank)
                },
                'recognition_confidence': confidence,
                'phrase_attempt_count': attempt_count
            }))
            
        except Exception as e:
            logger.error(f"Error processing phrase result: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Processing error: {str(e)}'
            }))


@login_required
@require_http_methods(["POST"])
def start_streaming_session(request):
    """Start a streaming speech recognition session"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        if not session_key:
            return JsonResponse({
                'success': False,
                'error': 'Session key is required'
            })
        
        # Check if Google Cloud Speech is available
        try:
            speech_service = GoogleSpeechStreamingService()
            if not speech_service.is_available():
                return JsonResponse({
                    'success': False,
                    'error': 'Google Cloud Speech service not available'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Speech service initialization failed: {str(e)}'
            })
        
        # Store session info
        streaming_sessions[session_key] = {
            'user_id': request.user.id,
            'started_at': timezone.now().isoformat(),
            'status': 'active'
        }
        
        return JsonResponse({
            'success': True,
            'websocket_url': f'/ws/speech/{session_key}/',
            'session_key': session_key
        })
        
    except Exception as e:
        logger.error(f"Error starting streaming session: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def stop_streaming_session(request):
    """Stop a streaming speech recognition session"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        if not session_key:
            return JsonResponse({
                'success': False,
                'error': 'Session key is required'
            })
        
        # Remove from active sessions
        session_info = streaming_sessions.pop(session_key, None)
        
        return JsonResponse({
            'success': True,
            'session_info': session_info
        })
        
    except Exception as e:
        logger.error(f"Error stopping streaming session: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def check_streaming_availability(request):
    """Check if streaming speech recognition is available"""
    try:
        speech_service = GoogleSpeechStreamingService()
        available = speech_service.is_available()
        
        return JsonResponse({
            'success': True,
            'available': available,
            'service': 'Google Cloud Speech' if available else 'None'
        })
        
    except Exception as e:
        logger.error(f"Error checking streaming availability: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'available': False
        })