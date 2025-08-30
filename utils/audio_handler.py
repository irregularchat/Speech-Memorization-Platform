# ./utils/audio_handler.py
import speech_recognition as sr
import streamlit as st
import io
import threading
import time

def transcribe_audio(audio_file):
    """Transcribe audio file to text with robust error handling."""
    try:
        recognizer = sr.Recognizer()
        
        # Validate audio file
        if not audio_file:
            raise ValueError("No audio file provided")
        
        with sr.AudioFile(audio_file) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.record(source)
        
        # Use Google's speech recognition service
        transcribed_text = recognizer.recognize_google(audio)
        
        if not transcribed_text.strip():
            return "No speech detected in audio"
            
        return transcribed_text
        
    except sr.UnknownValueError:
        return "Could not understand audio - please speak more clearly"
    except sr.RequestError as e:
        return f"Speech recognition service error: {e}"
    except ValueError as e:
        return f"Invalid audio file: {e}"
    except Exception as e:
        return f"Unexpected error during transcription: {e}"

def record_live_audio(duration=5):
    """Record live audio from microphone with comprehensive error handling."""
    try:
        # Validate duration
        if duration <= 0 or duration > 60:
            raise ValueError("Duration must be between 1 and 60 seconds")
        
        recognizer = sr.Recognizer()
        
        # Check if microphone is available
        try:
            microphone = sr.Microphone()
        except OSError as e:
            return f"Microphone not available: {e}"
        
        # Adjust for ambient noise
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=min(1, duration/5))
        except Exception as e:
            return f"Could not initialize microphone: {e}"
        
        # Record audio
        try:
            with microphone as source:
                audio = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
        except sr.WaitTimeoutError:
            return "Recording timeout - no speech detected within time limit"
        except Exception as e:
            return f"Recording failed: {e}"
        
        # Transcribe the recorded audio
        try:
            transcribed_text = recognizer.recognize_google(audio)
            
            if not transcribed_text.strip():
                return "No speech detected - please try speaking louder or closer to microphone"
                
            return transcribed_text
            
        except sr.UnknownValueError:
            return "Could not understand audio - please speak more clearly"
        except sr.RequestError as e:
            return f"Speech recognition service unavailable: {e}"
            
    except ValueError as e:
        return f"Invalid parameters: {e}"
    except Exception as e:
        return f"Unexpected error during recording: {e}"

def start_continuous_recording():
    """Start continuous recording session with error handling."""
    try:
        recognizer = sr.Recognizer()
        
        # Check microphone availability
        try:
            microphone = sr.Microphone()
        except OSError as e:
            return f"Microphone not available: {e}"
        
        # Initialize microphone
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
            return "Microphone ready for recording"
        except Exception as e:
            return f"Error initializing microphone: {e}"
            
    except Exception as e:
        return f"Unexpected error: {e}"