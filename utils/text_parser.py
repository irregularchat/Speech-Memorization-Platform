# ./utils/text_parser.py
import json

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

def parse_speech_text_file(filepath: str) -> dict:
    """
    Parses a JSON speech text file and returns its content as a dictionary.

    Args:
        filepath: The path to the JSON file.

    Returns:
        A dictionary representing the parsed JSON object.

    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the JSON is malformed.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON from {filepath}: {e}")

if __name__ == "__main__":
    # Example usage and test for parse_speech_text_file
    # This assumes you have created the example_speech.json as in a previous step.
    # To run this test, execute this file directly: python utils/text_parser.py
    example_file_path = "data/pre_texts/example_speech.json"
    
    # First, ensure the example file exists or create a dummy one for testing
    try:
        with open(example_file_path, 'r') as f:
            pass # File exists
    except FileNotFoundError:
        print(f"Test file {example_file_path} not found. Creating a dummy version for testing.")
        # Create a dummy example_speech.json if it doesn't exist, for testing purposes
        dummy_data = {
            "title": "Dummy Test Speech",
            "text": "This is a dummy speech for testing the parser.",
            "description": "A dummy file created for testing parse_speech_text_file.",
            "tags": ["dummy", "test"]
        }
        try:
            # Ensure the directory exists
            import os
            os.makedirs(os.path.dirname(example_file_path), exist_ok=True)
            with open(example_file_path, 'w') as f:
                json.dump(dummy_data, f, indent=2)
            print(f"Dummy test file {example_file_path} created.")
        except Exception as e:
            print(f"Could not create dummy test file: {e}")
            # If dummy creation also fails, skip the test that depends on the file
            example_file_path = None


    if example_file_path:
        print(f"Attempting to parse: {example_file_path}")
        try:
            parsed_content = parse_speech_text_file(example_file_path)
            print("Parsed content:")
            print(json.dumps(parsed_content, indent=2))
        except FileNotFoundError:
            print(f"Error: The file {example_file_path} was not found.")
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    # Test with a non-existent file
    print("\nAttempting to parse a non-existent file:")
    try:
        parse_speech_text_file("non_existent_file.json")
    except FileNotFoundError:
        print("Successfully caught FileNotFoundError for non_existent_file.json")
    except Exception as e:
        print(f"An unexpected error occurred while testing non-existent file: {e}")

    # Test with a malformed JSON file
    malformed_file_path = "data/pre_texts/malformed_example.json"
    try:
        import os
        os.makedirs(os.path.dirname(malformed_file_path), exist_ok=True)
        with open(malformed_file_path, 'w') as f:
            f.write('{"title": "Malformed", "text": "This is not valid JSON",}') # Extra comma
        print(f"\nAttempting to parse malformed JSON file: {malformed_file_path}")
        parse_speech_text_file(malformed_file_path)
    except ValueError as e:
        print(f"Successfully caught ValueError for malformed JSON: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while testing malformed JSON: {e}")
    finally:
        # Clean up the malformed test file
        if os.path.exists(malformed_file_path):
            os.remove(malformed_file_path)