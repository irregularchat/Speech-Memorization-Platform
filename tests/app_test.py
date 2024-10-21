#./tests/app_test.py
import unittest
import streamlit as st
from utils.text_parser import load_text_from_file
from app import get_title

class TestApp(unittest.TestCase):

    def test_title_display(self):
        # Test case for displaying app title
        self.assertEqual(get_title(), "Speech Memorization Platform")

    def test_text_loading(self):
        # Test case for loading text
        text = load_text_from_file("data/sample_text.txt")
        self.assertIsNotNone(text)
        self.assertIn("Memorization", text)

if __name__ == '__main__':
    unittest.main()