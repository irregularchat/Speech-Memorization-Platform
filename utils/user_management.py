# ./utils/user_management.py
import os
import json

def save_custom_text(custom_text, time_limit, description, tags):
    """Save a custom text to the user's text directory."""
    if not os.path.exists('data/user_data/texts/'):
        os.makedirs('data/user_data/texts/')
    
    text_data = {
        'text': custom_text,
        'time_limit': time_limit,
        'description': description,
        'tags': tags
    }
    
    with open(f"data/user_data/texts/custom_text_{len(os.listdir('data/user_data/texts/'))}.json", 'w') as file:
        json.dump(text_data, file)

def update_stats(comparison_results):
    """Update user stats with the latest performance data."""
    user_stats = load_user_stats()
    
    user_stats['total_words'] += comparison_results['total_words']
    user_stats['errors'] += comparison_results['errors']
    
    save_user_stats(user_stats)

def load_user_stats():
    """Load the user statistics from a file."""
    if os.path.exists('data/user_data/logs/user_stats.json'):
        with open('data/user_data/logs/user_stats.json', 'r') as file:
            return json.load(file)
    return {'total_words': 0, 'errors': 0}

def save_user_stats(stats):
    """Save the user statistics to a file."""
    with open('data/user_data/logs/user_stats.json', 'w') as file:
        json.dump(stats, file)