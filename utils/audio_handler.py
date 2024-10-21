# ./utils/audio_handler.py
import speech_recognition as sr

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