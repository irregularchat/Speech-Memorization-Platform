import tkinter as tk
from tkinter import scrolledtext, ttk, StringVar, messagebox
import os
from utils.text_parser import parse_speech_text_file
from utils.ui_utils import (
    configure_highlight_tag, 
    highlight_word, 
    clear_highlight,
    configure_covered_tag,
    cover_word,
    clear_covered_word
)
from utils.audio_handler import list_input_devices, start_recording, stop_recording # is_recording_active

# Global variable to store loaded texts (title: content mapping)
loaded_texts_map = {}
# Global variables to track the end of the current highlight and cover
current_highlight_end_index = "1.0"
current_cover_end_index = "1.0"

# Global list to store audio device information
available_audio_devices = []
# Global UI element references for audio controls
mic_combobox = None
start_record_button = None
stop_record_button = None


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
    global mic_combobox, start_record_button, stop_record_button, available_audio_devices # Declare globals for UI elements

    # Create the main window
    root = tk.Tk()
    root.title("Speech Memorization Platform")
    root.geometry("800x700") # Increased height for audio controls

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
    # Explicitly set background to white for cover effect to work as expected
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=25, bg="white") 
    text_area.insert(tk.INSERT, "Select a speech from the dropdown to display its content.")
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Configure the highlight and covered word tags for the text_area
    configure_highlight_tag(text_area)
    configure_covered_tag(text_area, cover_color="white") # Ensure cover_color matches text_area bg

    def on_text_selected(event):
        global current_highlight_end_index, current_cover_end_index
        selected_title = speech_combobox.get()
        if selected_title in loaded_texts_map:
            content = loaded_texts_map[selected_title]
            text_area.delete('1.0', tk.END)
            text_area.insert(tk.INSERT, content)
            current_highlight_end_index = "1.0" # Reset for new text
            current_cover_end_index = "1.0"   # Reset for new text
            clear_highlight(text_area) # Clear previous highlight
            clear_covered_word(text_area) # Clear previous cover
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
        global current_highlight_end_index, current_cover_end_index
        
        # Mutual exclusivity: Clear cover and reset its index
        clear_covered_word(text_widget)
        current_cover_end_index = "1.0"

        count_var = StringVar() 
        start_index = text_widget.search(r'\S+', current_highlight_end_index, tk.END, regexp=True, count=count_var)
        
        if start_index:
            end_index = text_widget.index(f"{start_index} wordend")
            if start_index and end_index and start_index != end_index:
                highlight_word(text_widget, start_index, end_index)
                current_highlight_end_index = end_index 
                text_widget.see(start_index) 
            else:
                print("Could not determine valid word boundaries for highlight.")
                current_highlight_end_index = "1.0"
                clear_highlight(text_widget)
                print("Highlighting reset. Click 'Highlight Next Word' to start from the beginning.")
        else:
            print("End of text reached for highlight. Highlighting will restart.")
            current_highlight_end_index = "1.0"
            clear_highlight(text_widget)

    highlight_next_button = tk.Button(
        button_frame, 
        text="Highlight Next Word", 
        command=lambda: highlight_next_word_in_textarea(text_area)
    )
    highlight_next_button.pack(side=tk.LEFT, padx=5, pady=5)

    # --- Cover Next Word Button and Functionality ---
    def cover_next_word_in_textarea(text_widget: scrolledtext.ScrolledText):
        """Covers the next word in the given ScrolledText widget sequentially."""
        global current_cover_end_index, current_highlight_end_index

        # Mutual exclusivity: Clear highlight and reset its index
        clear_highlight(text_widget)
        current_highlight_end_index = "1.0"

        count_var = StringVar()
        start_index = text_widget.search(r'\S+', current_cover_end_index, tk.END, regexp=True, count=count_var)

        if start_index:
            end_index = text_widget.index(f"{start_index} wordend")
            if start_index and end_index and start_index != end_index:
                cover_word(text_widget, start_index, end_index)
                current_cover_end_index = end_index
                text_widget.see(start_index)
            else:
                print("Could not determine valid word boundaries for cover.")
                current_cover_end_index = "1.0"
                clear_covered_word(text_widget)
                print("Covering reset. Click 'Cover Next Word' to start from the beginning.")
        else:
            print("End of text reached for cover. Covering will restart.")
            current_cover_end_index = "1.0"
            clear_covered_word(text_widget)
            
    cover_next_button = tk.Button(
        button_frame,
        text="Cover Next Word",
        command=lambda: cover_next_word_in_textarea(text_area)
    )
    cover_next_button.pack(side=tk.LEFT, padx=5, pady=5)

    # --- Audio Controls Frame ---
    audio_controls_frame = tk.Frame(root)
    audio_controls_frame.pack(padx=10, pady=(5,10), fill=tk.X, expand=False)

    tk.Label(audio_controls_frame, text="Select Microphone:").pack(side=tk.LEFT, padx=(0, 5))
    
    available_audio_devices = list_input_devices()
    device_names = [dev['name'] for dev in available_audio_devices] if available_audio_devices else ["No devices found"]
    
    mic_combobox = ttk.Combobox(audio_controls_frame, state="readonly", width=35)
    mic_combobox['values'] = device_names
    if available_audio_devices:
        mic_combobox.current(0)
    else:
        mic_combobox.set("No devices found")
        mic_combobox.config(state=tk.DISABLED)
    mic_combobox.pack(side=tk.LEFT, padx=5)

    start_record_button = tk.Button(audio_controls_frame, text="Start Recording", command=handle_start_recording)
    if not available_audio_devices: # Disable if no devices
        start_record_button.config(state=tk.DISABLED)
    start_record_button.pack(side=tk.LEFT, padx=5)

    stop_record_button = tk.Button(audio_controls_frame, text="Stop Recording", command=handle_stop_recording, state=tk.DISABLED)
    stop_record_button.pack(side=tk.LEFT, padx=5)

    # Start the Tkinter event loop
    root.mainloop()

# --- Audio Handler Functions ---
def handle_start_recording():
    global mic_combobox, start_record_button, stop_record_button, available_audio_devices

    selected_device_name = mic_combobox.get()
    selected_device_id = None

    if not available_audio_devices:
        messagebox.showerror("Audio Error", "No audio input devices found.")
        return

    for device in available_audio_devices:
        if device['name'] == selected_device_name:
            selected_device_id = device['id']
            break
    
    # If no device is selected (e.g. combobox is empty or user typed something invalid),
    # start_recording in audio_handler will pick a default.
    # However, it's better to ensure a valid selection if possible or handle explicitly.
    if selected_device_name == "No devices found" or selected_device_id is None and selected_device_name:
         # Attempt to use the first available device if a specific one isn't clearly selected or if placeholder is there
        if available_audio_devices:
            selected_device_id = available_audio_devices[0]['id']
            print(f"No specific device selected or selection unclear, defaulting to first available: {available_audio_devices[0]['name']}")
        else: # Should be caught by earlier check, but as a safeguard
            messagebox.showerror("Audio Error", "Cannot start recording without an audio device.")
            return


    # Define output filename for the recording
    output_filename = "session_recording.wav" # Placed in the root directory of the app

    success = start_recording(device_id=selected_device_id, output_filename=output_filename)

    if success:
        if start_record_button: start_record_button.config(state=tk.DISABLED)
        if stop_record_button: stop_record_button.config(state=tk.NORMAL)
        if mic_combobox: mic_combobox.config(state=tk.DISABLED)
        messagebox.showinfo("Recording", f"Recording started...\nOutput will be saved to {output_filename}")
    else:
        messagebox.showerror("Error", "Failed to start recording. See console for details.")

def handle_stop_recording():
    global start_record_button, stop_record_button, mic_combobox
    
    stop_recording() # Call the function from audio_handler

    if start_record_button: start_record_button.config(state=tk.NORMAL)
    if stop_record_button: stop_record_button.config(state=tk.DISABLED)
    if mic_combobox and available_audio_devices : mic_combobox.config(state=tk.NORMAL if available_audio_devices else tk.DISABLED) # Re-enable only if devices exist
    
    messagebox.showinfo("Recording", "Recording stopped. Audio saved to session_recording.wav (check console for exact path or if relative to app root).")


if __name__ == "__main__":
    main()