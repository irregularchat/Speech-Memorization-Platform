# ./tests/test_text_parser.py
import unittest
import json
import os
import shutil # For rmtree
from utils.text_parser import parse_speech_text_file, load_text_from_file, compare_text

class TestTextParser(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory for test files."""
        self.temp_dir = "tests/temp_test_files_for_parser"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create a dummy test_data/sample.txt for the existing test
        self.test_data_dir = "test_data"
        os.makedirs(self.test_data_dir, exist_ok=True)
        self.sample_txt_path = os.path.join(self.test_data_dir, "sample.txt")
        with open(self.sample_txt_path, 'w') as f:
            f.write("This is a sample text for testing.")

    def tearDown(self):
        """Remove the temporary directory and its contents after tests."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if os.path.exists(self.test_data_dir): # Clean up dummy sample.txt and its dir
            shutil.rmtree(self.test_data_dir)

    # Existing tests - ensure they can still run with setUp/tearDown
    def test_load_text_from_file(self):
        # Simulate loading text - uses the dummy file created in setUp
        result = load_text_from_file(self.sample_txt_path)
        expected = "This is a sample text for testing."
        self.assertEqual(result, expected)
    
    def test_compare_text(self):
        # Test transcribed text comparison
        original_text = "This is a sample text"
        transcribed_text = "This is a test text"
        # Note: compare_text was not in the provided utils.text_parser,
        # but I'm keeping the test structure. If compare_text is added later, this will be useful.
        # For now, I'll assume it's meant to be text_parser.compare_text if it exists.
        # If text_parser.compare_text is not defined, this test will fail or error out.
        # Based on previous steps, `compare_text` IS in `utils.text_parser`
        result = compare_text(transcribed_text, original_text)
        self.assertEqual(result['errors'], 1)
        self.assertEqual(result['total_words'], 5) # original_text has 5 words
        self.assertEqual(result['differences'], [("sample", "test")])


    # --- New tests for parse_speech_text_file ---

    def test_parse_valid_json_file_all_fields(self):
        """Test parsing a valid JSON file with all fields present."""
        file_path = os.path.join(self.temp_dir, "valid_all_fields.json")
        data = {
            "title": "Test Speech",
            "text": "Hello world.\nThis is a test.",
            "time_limit": 180,
            "description": "A test speech with all fields.",
            "tags": ["test", "all_fields"]
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        parsed_data = parse_speech_text_file(file_path)
        self.assertEqual(parsed_data, data)

    def test_parse_valid_json_file_mandatory_fields_only(self):
        """Test parsing a valid JSON file with only mandatory fields."""
        file_path = os.path.join(self.temp_dir, "valid_mandatory_only.json")
        data = {
            "title": "Minimal Speech",
            "text": "Just title and text."
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        parsed_data = parse_speech_text_file(file_path)
        expected_data = { # Optional fields should be absent, not None
            "title": "Minimal Speech",
            "text": "Just title and text."
        }
        self.assertEqual(parsed_data, expected_data)

    def test_parse_file_not_found(self):
        """Test parsing a non-existent file path."""
        non_existent_path = os.path.join(self.temp_dir, "non_existent.json")
        with self.assertRaises(FileNotFoundError):
            parse_speech_text_file(non_existent_path)

    def test_parse_malformed_json_file(self):
        """Test parsing a file with invalid JSON content."""
        file_path = os.path.join(self.temp_dir, "malformed.json")
        with open(file_path, 'w') as f:
            f.write('{"title": "Malformed", "text": "Missing quote and comma}') # Invalid JSON
        
        with self.assertRaises(ValueError) as context:
            parse_speech_text_file(file_path)
        self.assertTrue("Error decoding JSON" in str(context.exception))


    def test_parse_empty_json_file(self):
        """Test parsing an empty file (which is not valid JSON)."""
        file_path = os.path.join(self.temp_dir, "empty.json")
        with open(file_path, 'w') as f:
            pass # Create an empty file
        
        with self.assertRaises(ValueError) as context:
            parse_speech_text_file(file_path)
        self.assertTrue("Error decoding JSON" in str(context.exception) or "Expecting value" in str(context.exception))


if __name__ == '__main__':
    unittest.main()