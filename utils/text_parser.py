# ./utils/text_parser.py
def load_text_from_file(filepath):
    """Load text from a file and return it as a string."""
    with open(filepath, 'r') as file:
        text = file.read()
    return text


def format_text(text, title=None, time_limit=None, description=None, tags=None):
    """Format a given text with optional metadata."""
    return {
        'title': title,
        'text': text,
        'time_limit': time_limit,
        'description': description,
        'tags': tags
    }

def clean_word(word):
    """Clean word by removing punctuation and normalizing."""
    import re
    return re.sub(r'[^\w]', '', word).lower()

def compare_text(transcribed_text, original_text):
    """Compare transcribed text with the original text and highlight differences."""
    differences = []
    original_words = original_text.split()
    transcribed_words = transcribed_text.split()
    
    # Compare word by word, accounting for different lengths
    max_length = max(len(original_words), len(transcribed_words))
    
    for i in range(max_length):
        original_word = original_words[i] if i < len(original_words) else ""
        transcribed_word = transcribed_words[i] if i < len(transcribed_words) else ""
        
        # Clean words for comparison
        clean_original = clean_word(original_word)
        clean_transcribed = clean_word(transcribed_word)
        
        if clean_original != clean_transcribed:
            differences.append((original_word, transcribed_word))
    
    return {
        'total_words': len(original_words),
        'errors': len(differences),
        'differences': differences
    }