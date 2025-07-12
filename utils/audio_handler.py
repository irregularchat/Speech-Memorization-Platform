# ./utils/audio_handler.py
import speech_recognition as sr
import streamlit as st
import io
import threading
import time

def transcribe_audio(audio_file):
    """Transcribe audio file to text."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    
    try:
        # Use Google's speech recognition service
        transcribed_text = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        transcribed_text = "Could not understand audio"
    except sr.RequestError as e:
        transcribed_text = f"Could not request results from service; {e}"
    
    return transcribed_text

def record_live_audio(duration=5):
    """Record live audio from microphone for specified duration."""
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
        
        with microphone as source:
            audio = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
        
        # Transcribe the recorded audio
        transcribed_text = recognizer.recognize_google(audio)
        return transcribed_text
    except sr.WaitTimeoutError:
        return "Recording timeout - no speech detected"
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Could not request results from service; {e}"
    except Exception as e:
        return f"Error during recording: {e}"

def start_continuous_recording():
    """Start continuous recording session (placeholder for real-time implementation)."""
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
        return "Microphone ready for recording"
    except Exception as e:
        return f"Error initializing microphone: {e}"