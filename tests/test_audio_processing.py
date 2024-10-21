# ./tests/test_audio_processing.py
import unittest
from utils import audio_handler
import io

class TestAudioHandler(unittest.TestCase):
    def test_transcribe_audio(self):
        # Simulate an audio file using a valid wave file (You would need an actual audio file to test)
        audio_file = io.BytesIO(b"fake-audio-data")
        transcribed_text = audio_handler.transcribe_audio(audio_file)
        
        # We can't determine what the actual transcription will be without a real file, but we can check for exceptions
        self.assertIsInstance(transcribed_text, str)

if __name__ == '__main__':
    unittest.main()