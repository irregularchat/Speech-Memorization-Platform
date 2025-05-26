import tkinter as tk

HIGHLIGHT_TAG_NAME = "current_highlight"

def configure_highlight_tag(text_widget: tk.Text, background_color: str = "yellow", foreground_color: str = "black"):
    """Configures the appearance of the highlight tag."""
    text_widget.tag_configure(HIGHLIGHT_TAG_NAME, background=background_color, foreground=foreground_color)

def highlight_word(text_widget: tk.Text, start_index: str, end_index: str):
    """
    Highlights a word in the text widget given its start and end indices.
    Clears any previous highlight.
    """
    # Ensure the highlight tag is configured (can be called multiple times, it's idempotent)
    # Or, it could be configured once when the app starts / text widget is created.
    # For simplicity here, let's assume it's configured.
    # If not, add: configure_highlight_tag(text_widget)

    # Remove any existing highlight
    text_widget.tag_remove(HIGHLIGHT_TAG_NAME, "1.0", tk.END)

    # Add the new highlight
    text_widget.tag_add(HIGHLIGHT_TAG_NAME, start_index, end_index)

def clear_highlight(text_widget: tk.Text):
    """Clears any active highlight in the text widget."""
    text_widget.tag_remove(HIGHLIGHT_TAG_NAME, "1.0", tk.END)

# Example of how to get word boundaries (will be used in app.py later)
# def get_word_at_index(text_widget: tk.Text, current_pos_str: str) -> tuple[str, str] | None:
#     start_index = text_widget.index(f"{current_pos_str} wordstart")
#     end_index = text_widget.index(f"{current_pos_str} wordend")
#     if start_index == end_index: # No word found (e.g., on whitespace)
#         return None
#     return start_index, end_index

if __name__ == "__main__":
    # Basic test setup for the functions
    root = tk.Tk()
    root.title("Highlight Test")
    text = tk.Text(root, wrap=tk.WORD, width=40, height=10)
    text.pack(padx=10, pady=10)
    text.insert("1.0", "This is a test sentence for highlighting words.\nSecond line.")

    # Configure the highlight tag for this specific text widget instance
    configure_highlight_tag(text)

    # Example Usage:
    # To highlight "test" in "This is a test sentence..."
    # Line 1, char 10 is 't' in 'test'.
    # word_start = text.index("1.10 wordstart") # Should be "1.10"
    # word_end = text.index("1.10 wordend")     # Should be "1.14"
    # print(f"Calculated start: {word_start}, end: {word_end}") # Debug
    
    # Correct way to find "test"
    search_pattern = r"test" # Using regex might be more robust for general search
    start_char_index = text.search(search_pattern, "1.0", tk.END, regexp=False) # regexp=False for simple string

    if start_char_index:
        end_char_index = f"{start_char_index}+{len(search_pattern)}c"
        print(f"Highlighting from {start_char_index} to {end_char_index}")
        highlight_word(text, start_char_index, end_char_index)
    else:
        print(f"'{search_pattern}' not found.")

    # Button to clear highlight
    clear_button = tk.Button(root, text="Clear Highlight", command=lambda: clear_highlight(text))
    clear_button.pack(pady=5)
    
    # Button to highlight "sentence"
    def highlight_sentence_word():
        s_start = text.search("sentence", "1.0", tk.END)
        if s_start:
            s_end = f"{s_start}+{len('sentence')}c"
            highlight_word(text, s_start, s_end)
    
    highlight_sentence_button = tk.Button(root, text="Highlight 'sentence'", command=highlight_sentence_word)
    highlight_sentence_button.pack(pady=5)

    root.mainloop()
