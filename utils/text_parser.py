# ./utils/text_parser.py
def load_text_from_file(filepath):
    """Load text from a file with robust error handling."""
    try:
        # Validate filepath
        if not filepath:
            raise ValueError("No filepath provided")
        
        # Check if file exists
        import os
        if hasattr(filepath, 'read'):  # It's a file-like object (uploaded file)
            try:
                content = filepath.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                return content.strip()
            except UnicodeDecodeError:
                raise ValueError("File encoding not supported - please use UTF-8 text files")
        else:  # It's a filepath string
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")
            
            if not os.path.isfile(filepath):
                raise ValueError(f"Path is not a file: {filepath}")
            
            # Try to read the file
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    text = file.read().strip()
                    
                if not text:
                    raise ValueError("File is empty")
                    
                return text
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    with open(filepath, 'r', encoding='latin-1') as file:
                        text = file.read().strip()
                        return text
                except Exception:
                    raise ValueError("Could not decode file - unsupported encoding")
                    
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Text file not found: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid text file: {e}")
    except PermissionError:
        raise PermissionError(f"Permission denied accessing file: {filepath}")
    except Exception as e:
        raise Exception(f"Unexpected error loading text file: {e}")


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