# ./tests/test_user_management.py
import unittest
import os
import json
from utils import user_management

class TestUserManagement(unittest.TestCase):
    def setUp(self):
        # Set up mock user stats
        self.mock_stats = {
            "total_words": 100,
            "errors": 5
        }
        if not os.path.exists('data/user_data/logs/'):
            os.makedirs('data/user_data/logs/')

        with open('data/user_data/logs/user_stats.json', 'w') as file:
            json.dump(self.mock_stats, file)

    def test_load_user_stats(self):
        stats = user_management.load_user_stats()
        self.assertEqual(stats["total_words"], 100)
        self.assertEqual(stats["errors"], 5)

    def test_update_stats(self):
        comparison_results = {
            "total_words": 10,
            "errors": 1
        }
        user_management.update_stats(comparison_results)
        stats = user_management.load_user_stats()
        self.assertEqual(stats["total_words"], 110)  # 100 + 10
        self.assertEqual(stats["errors"], 6)  # 5 + 1

    def tearDown(self):
        # Clean up any test artifacts
        if os.path.exists('data/user_data/logs/user_stats.json'):
            os.remove('data/user_data/logs/user_stats.json')

if __name__ == '__main__':
    unittest.main()