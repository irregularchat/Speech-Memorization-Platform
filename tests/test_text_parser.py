# ./tests/test_text_parser.py
import unittest
from utils import text_parser

class TestTextParser(unittest.TestCase):
    def test_load_text_from_file(self):
        # Simulate loading text
        result = text_parser.load_text_from_file("test_data/sample.txt")
        expected = "This is a sample text for testing."
        self.assertEqual(result, expected)
    
    def test_compare_text(self):
        # Test transcribed text comparison
        original_text = "This is a sample text"
        transcribed_text = "This is a test text"
        result = text_parser.compare_text(transcribed_text, original_text)
        self.assertEqual(result['errors'], 1)
        self.assertEqual(result['total_words'], 5)
        self.assertEqual(result['differences'], [("sample", "test")])

if __name__ == '__main__':
    unittest.main()