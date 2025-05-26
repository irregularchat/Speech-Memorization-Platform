import tkinter as tk
from tkinter import scrolledtext

def main():
    # Create the main window
    root = tk.Tk()
    root.title("Speech Memorization Platform")

    # Set window size (optional, but good for starting)
    root.geometry("800x600")

    # Create a ScrolledText widget
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=30)
    text_area.insert(tk.INSERT, "Text will appear here.")
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Create a frame for the buttons
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

    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()