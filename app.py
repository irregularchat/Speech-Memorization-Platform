import tkinter as tk
from tkinter import scrolledtext, ttk, StringVar
import os
from utils.text_parser import parse_speech_text_file
from utils.ui_utils import configure_highlight_tag, highlight_word, clear_highlight

# Global variable to store loaded texts (title: content mapping)
loaded_texts_map = {}
# Global variable to track the end of the current highlight
current_highlight_end_index = "1.0"


def load_available_texts():
    """
    Scans the data/pre_texts/ directory for .json files, parses them,
    and returns a dictionary mapping titles to their full text content.
    Also populates the global loaded_texts_map.
    """
    global loaded_texts_map
    loaded_texts_map.clear() # Clear previous entries
    texts_path = "data/pre_texts/"
    if not os.path.exists(texts_path):
        print(f"Directory not found: {texts_path}")
        return {}

    titles = []
    for filename in os.listdir(texts_path):
        if filename.endswith(".json"):
            filepath = os.path.join(texts_path, filename)
            try:
                parsed_content = parse_speech_text_file(filepath)
                title = parsed_content.get("title", "Untitled")
                text_content = parsed_content.get("text", "")
                
                # Ensure unique titles for combobox, append filename if not unique
                original_title = title
                count = 1
                while title in loaded_texts_map:
                    title = f"{original_title} ({count})"
                    count += 1
                
                loaded_texts_map[title] = text_content
                titles.append(title)
            except FileNotFoundError:
                print(f"File not found during scan: {filepath}")
            except ValueError as e: # Handles JSONDecodeError from parser
                print(f"Error parsing JSON file {filepath}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred with {filepath}: {e}")
    return titles


def main():
    # Create the main window
    root = tk.Tk()
    root.title("Speech Memorization Platform")
    root.geometry("800x600")

    # --- Top frame for text selection ---
    top_frame = tk.Frame(root)
    top_frame.pack(padx=10, pady=(10,0), fill=tk.X)

    tk.Label(top_frame, text="Select Speech:").pack(side=tk.LEFT, padx=(0, 5))

    speech_titles = load_available_texts() # Load texts and get titles
    
    speech_combobox = ttk.Combobox(top_frame, values=speech_titles, state="readonly", width=50)
    if speech_titles:
        speech_combobox.current(0) # Select the first item if available
    speech_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # --- Text Area ---
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=25) # Adjusted height
    text_area.insert(tk.INSERT, "Select a speech from the dropdown to display its content.")
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Configure the highlight tag for the text_area
    configure_highlight_tag(text_area)

    def on_text_selected(event):
        global current_highlight_end_index
        selected_title = speech_combobox.get()
        if selected_title in loaded_texts_map:
            content = loaded_texts_map[selected_title]
            text_area.delete('1.0', tk.END)
            text_area.insert(tk.INSERT, content)
            current_highlight_end_index = "1.0" # Reset for new text
            clear_highlight(text_area) # Clear previous highlight
        else:
            text_area.delete('1.0', tk.END)
            text_area.insert(tk.INSERT, f"Content for '{selected_title}' not found.")

    speech_combobox.bind("<<ComboboxSelected>>", on_text_selected)

    # Initialize text area with the first speech if available
    if speech_titles:
        first_title = speech_titles[0]
        if first_title in loaded_texts_map:
             text_area.delete('1.0', tk.END)
             text_area.insert(tk.INSERT, loaded_texts_map[first_title])


    # --- Button Frame ---
    button_frame = tk.Frame(root)
    button_frame.pack(padx=10, pady=5, fill=tk.X, expand=False)

    # Create and pack the buttons
    mic_button = tk.Button(button_frame, text="Microphone")
    mic_button.pack(side=tk.LEFT, padx=5, pady=5)

    play_pause_button = tk.Button(button_frame, text="Play/Pause")
    play_pause_button.pack(side=tk.LEFT, padx=5, pady=5)

    restart_button = tk.Button(button_frame, text="Restart")
    restart_button.pack(side=tk.LEFT, padx=5, pady=5)

    select_text_button = tk.Button(button_frame, text="Select Text")
    select_text_button.pack(side=tk.LEFT, padx=5, pady=5)

    add_custom_text_button = tk.Button(button_frame, text="Add Custom Text")
    add_custom_text_button.pack(side=tk.LEFT, padx=5, pady=5)

    # --- Highlight Next Word Button and Functionality ---
    def highlight_next_word_in_textarea(text_widget: scrolledtext.ScrolledText):
        """Highlights the next word in the given ScrolledText widget sequentially."""
        global current_highlight_end_index
        
        count_var = StringVar() # Needed for search's count parameter, though not strictly used for end_index calculation here
        
        # Search for the next non-whitespace sequence starting from current_highlight_end_index
        start_index = text_widget.search(r'\S+', current_highlight_end_index, tk.END, regexp=True, count=count_var)
        
        if start_index:
            # Calculate end_index using wordend for robustness
            end_index = text_widget.index(f"{start_index} wordend")
            
            # Ensure a valid word is found (start and end are different)
            if start_index and end_index and start_index != end_index:
                highlight_word(text_widget, start_index, end_index)
                current_highlight_end_index = end_index # Update for next search
                text_widget.see(start_index) # Ensure the highlighted word is visible
            else:
                # This case might occur if search lands on something non-standard or at the very end
                print("Could not determine valid word boundaries from search result.")
                # Reset to restart highlighting from the beginning
                current_highlight_end_index = "1.0"
                clear_highlight(text_widget)
                print("Highlighting reset. Click 'Highlight Next Word' to start from the beginning.")
        else:
            # No more words found, reset to the beginning
            print("End of text reached. Highlighting will restart.")
            current_highlight_end_index = "1.0"
            clear_highlight(text_widget)

    highlight_next_button = tk.Button(
        button_frame, 
        text="Highlight Next Word", 
        command=lambda: highlight_next_word_in_textarea(text_area)
    )
    highlight_next_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()