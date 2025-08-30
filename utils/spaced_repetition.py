# ./utils/spaced_repetition.py
import json
import os
from datetime import datetime, timedelta
import re

class SpacedRepetitionManager:
    def __init__(self, user_data_dir="data/user_data/"):
        self.user_data_dir = user_data_dir
        self.repetition_file = os.path.join(user_data_dir, "logs", "word_repetition.json")
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(os.path.dirname(self.repetition_file), exist_ok=True)
    
    def load_word_data(self):
        """Load word repetition data from file."""
        if os.path.exists(self.repetition_file):
            try:
                with open(self.repetition_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def save_word_data(self, data):
        """Save word repetition data to file."""
        try:
            with open(self.repetition_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except IOError as e:
            print(f"Error saving word data: {e}")
    
    def update_word_performance(self, word, correct=True):
        """Update performance data for a specific word using Anki SM-2 algorithm."""
        data = self.load_word_data()
        word_lower = word.lower().strip()
        
        if word_lower not in data:
            data[word_lower] = {
                'easiness_factor': 2.5,
                'repetition': 0,
                'interval': 1,
                'next_review': datetime.now().isoformat(),
                'total_attempts': 0,
                'correct_attempts': 0,
                'last_seen': datetime.now().isoformat(),
                'mastery_level': 0  # 0-5 scale
            }
        
        word_data = data[word_lower]
        word_data['total_attempts'] += 1
        word_data['last_seen'] = datetime.now().isoformat()
        
        if correct:
            word_data['correct_attempts'] += 1
            word_data['repetition'] += 1
            
            # SM-2 algorithm implementation
            if word_data['repetition'] == 1:
                word_data['interval'] = 1
            elif word_data['repetition'] == 2:
                word_data['interval'] = 6
            else:
                word_data['interval'] = int(word_data['interval'] * word_data['easiness_factor'])
            
            # Update easiness factor
            accuracy = word_data['correct_attempts'] / word_data['total_attempts']
            quality = min(5, max(0, int(accuracy * 5)))  # 0-5 scale
            
            ef = word_data['easiness_factor']
            ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            word_data['easiness_factor'] = max(1.3, ef)
            
            # Update mastery level
            if accuracy >= 0.9 and word_data['repetition'] >= 3:
                word_data['mastery_level'] = min(5, word_data['mastery_level'] + 1)
        else:
            # Reset on failure
            word_data['repetition'] = 0
            word_data['interval'] = 1
            word_data['easiness_factor'] = max(1.3, word_data['easiness_factor'] - 0.2)
            word_data['mastery_level'] = max(0, word_data['mastery_level'] - 1)
        
        # Calculate next review date
        next_review = datetime.now() + timedelta(days=word_data['interval'])
        word_data['next_review'] = next_review.isoformat()
        
        self.save_word_data(data)
        return word_data
    
    def get_mastered_words(self, text, mastery_threshold=3):
        """Get list of words that have reached mastery threshold."""
        data = self.load_word_data()
        words = self.extract_words(text)
        mastered = []
        
        for word in words:
            word_lower = word.lower().strip()
            if word_lower in data:
                word_data = data[word_lower]
                if word_data['mastery_level'] >= mastery_threshold:
                    mastered.append(word)
        
        return mastered
    
    def get_words_for_review(self):
        """Get words that are due for review."""
        data = self.load_word_data()
        now = datetime.now()
        due_words = []
        
        for word, word_data in data.items():
            next_review = datetime.fromisoformat(word_data['next_review'])
            if now >= next_review:
                due_words.append({
                    'word': word,
                    'data': word_data
                })
        
        return sorted(due_words, key=lambda x: x['data']['next_review'])
    
    def extract_words(self, text):
        """Extract words from text, filtering out punctuation."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return [word for word in words if len(word) > 2]  # Filter out short words
    
    def apply_spaced_repetition(self, text, mastery_percentage=0):
        """Apply spaced repetition by hiding mastered words based on percentage."""
        if mastery_percentage == 0:
            return text
        
        words = text.split()
        mastered_words = self.get_mastered_words(text)
        
        if not mastered_words:
            return text
        
        # Calculate how many words to hide based on mastery percentage
        num_to_hide = int(len(mastered_words) * (mastery_percentage / 100))
        words_to_hide = mastered_words[:num_to_hide]
        
        # Replace mastered words with blanks
        result_words = []
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in [w.lower() for w in words_to_hide]:
                # Create blank with same length
                blank = '_' * len(clean_word)
                # Preserve punctuation
                result_word = re.sub(r'\w+', blank, word)
                result_words.append(result_word)
            else:
                result_words.append(word)
        
        return ' '.join(result_words)
    
    def get_word_statistics(self, text):
        """Get detailed statistics for words in the text."""
        data = self.load_word_data()
        words = self.extract_words(text)
        stats = {
            'total_words': len(words),
            'tracked_words': 0,
            'mastered_words': 0,
            'words_due_review': 0,
            'average_mastery': 0,
            'word_details': []
        }
        
        total_mastery = 0
        for word in set(words):  # Unique words only
            word_lower = word.lower().strip()
            if word_lower in data:
                word_data = data[word_lower]
                stats['tracked_words'] += 1
                total_mastery += word_data['mastery_level']
                
                if word_data['mastery_level'] >= 3:
                    stats['mastered_words'] += 1
                
                next_review = datetime.fromisoformat(word_data['next_review'])
                if datetime.now() >= next_review:
                    stats['words_due_review'] += 1
                
                stats['word_details'].append({
                    'word': word,
                    'mastery_level': word_data['mastery_level'],
                    'accuracy': word_data['correct_attempts'] / max(1, word_data['total_attempts']),
                    'total_attempts': word_data['total_attempts'],
                    'next_review': word_data['next_review']
                })
        
        if stats['tracked_words'] > 0:
            stats['average_mastery'] = total_mastery / stats['tracked_words']
        
        return stats