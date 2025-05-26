import tkinter as tk

HIGHLIGHT_TAG_NAME = "current_highlight"
COVERED_WORD_TAG_NAME = "current_cover"

def configure_highlight_tag(text_widget: tk.Text, background_color: str = "yellow", foreground_color: str = "black"):
    """Configures the appearance of the highlight tag."""
    text_widget.tag_configure(HIGHLIGHT_TAG_NAME, background=background_color, foreground=foreground_color)

def configure_covered_tag(text_widget: tk.Text, cover_color: str = "white"):
    """Configures the appearance of the covered word tag."""
    # As per prompt, setting both to cover_color, defaulting to white.
    # A more adaptive approach could use: actual_bg = text_widget.cget("background")
    # and then set foreground=actual_bg, background=actual_bg.
    text_widget.tag_configure(COVERED_WORD_TAG_NAME, foreground=cover_color, background=cover_color)

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
    text_widget.tag_remove(HIGHLIGHT_TAG_NAME, "1.0", tk.END) # Clear previous highlight

    # Add the new highlight
    text_widget.tag_add(HIGHLIGHT_TAG_NAME, start_index, end_index)

def clear_highlight(text_widget: tk.Text):
    """Clears any active highlight in the text widget."""
    text_widget.tag_remove(HIGHLIGHT_TAG_NAME, "1.0", tk.END)

def cover_word(text_widget: tk.Text, start_index: str, end_index: str):
    """
    Covers a word in the text widget given its start and end indices.
    Clears any previous cover.
    Assumes covered_tag is configured.
    """
    text_widget.tag_remove(COVERED_WORD_TAG_NAME, "1.0", tk.END) # Clear previous covers
    text_widget.tag_add(COVERED_WORD_TAG_NAME, start_index, end_index)

def clear_covered_word(text_widget: tk.Text):
    """Clears any active covered word tag in the text widget."""
    text_widget.tag_remove(COVERED_WORD_TAG_NAME, "1.0", tk.END)

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
    text = tk.Text(root, wrap=tk.WORD, width=40, height=10, background="white") # Set bg for testing cover
    text.pack(padx=10, pady=10)
    text.insert("1.0", "This is a test sentence for highlighting and covering words.\nSecond line.")

    # Configure the tags for this specific text widget instance
    configure_highlight_tag(text)
    # Using "white" as cover_color, assuming text widget background is white.
    # If text widget bg changes, cover_color should ideally match.
    configure_covered_tag(text, cover_color="white")


    # Example Usage for Highlight:
    # To highlight "test" in "This is a test sentence..."
    # Line 1, char 10 is 't' in 'test'.
    # word_start = text.index("1.10 wordstart") # Should be "1.10"
    # word_end = text.index("1.10 wordend")     # Should be "1.14"
    # print(f"Calculated start: {word_start}, end: {word_end}") # Debug
    
    # Correct way to find "test"
    highlight_search_pattern = r"highlighting" 
    h_start_char_index = text.search(highlight_search_pattern, "1.0", tk.END, regexp=False)

    if h_start_char_index:
        h_end_char_index = f"{h_start_char_index}+{len(highlight_search_pattern)}c"
        print(f"Highlighting from {h_start_char_index} to {h_end_char_index}")
        highlight_word(text, h_start_char_index, h_end_char_index)
    else:
        print(f"'{highlight_search_pattern}' not found for highlight.")

    clear_highlight_button = tk.Button(root, text="Clear Highlight", command=lambda: clear_highlight(text))
    clear_highlight_button.pack(pady=2)
    
    # Example Usage for Cover:
    cover_search_pattern = r"covering"
    c_start_char_index = text.search(cover_search_pattern, "1.0", tk.END, regexp=False)

    def do_cover_word():
        if c_start_char_index:
            c_end_char_index = f"{c_start_char_index}+{len(cover_search_pattern)}c"
            print(f"Covering from {c_start_char_index} to {c_end_char_index}")
            cover_word(text, c_start_char_index, c_end_char_index)
        else:
            print(f"'{cover_search_pattern}' not found for cover.")
            
    cover_button = tk.Button(root, text=f"Cover '{cover_search_pattern}'", command=do_cover_word)
    cover_button.pack(pady=2)

    clear_cover_button = tk.Button(root, text="Clear Cover", command=lambda: clear_covered_word(text))
    clear_cover_button.pack(pady=2)
    
    # Button to highlight "sentence"
    def highlight_sentence_word_example():
        s_start = text.search("sentence", "1.0", tk.END)
        if s_start:
            s_end = f"{s_start}+{len('sentence')}c"
            highlight_word(text, s_start, s_end)
    
    highlight_sentence_button = tk.Button(root, text="Highlight 'sentence'", command=highlight_sentence_word_example)
    highlight_sentence_button.pack(pady=2)

    root.mainloop()
