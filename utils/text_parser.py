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

def compare_text(transcribed_text, original_text):
    """Compare transcribed text with the original text and highlight differences."""
    differences = []
    for original_word, transcribed_word in zip(original_text.split(), transcribed_text.split()):
        if original_word != transcribed_word:
            differences.append((original_word, transcribed_word))
    
    return {
        'total_words': len(original_text.split()),
        'errors': len(differences),
        'differences': differences
    }