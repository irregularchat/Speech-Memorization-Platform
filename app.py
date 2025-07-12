# ./app.py
# Import necessary libraries
import streamlit as st
from utils import text_parser, audio_handler, user_management

# Global variables to hold user state
current_text = None
user_stats = user_management.load_user_stats()

# Streamlit app configuration
st.set_page_config(page_title="Speech Memorization Platform", layout="centered")
def get_title():
    return "Speech Memorization Platform"

# Title of the app
st.title("Speech Memorization Platform")

# Sidebar for text selection
st.sidebar.header("Select or Add Text")

# Load pre-existing texts
import os
pre_texts_dir = "data/pre_texts/"
pre_texts = []
if os.path.exists(pre_texts_dir):
    pre_texts = [f[:-4] for f in os.listdir(pre_texts_dir) if f.endswith('.txt')]
pre_texts = pre_texts if pre_texts else ["No texts available"]
selected_text = st.sidebar.selectbox("Choose a pre-loaded text", pre_texts)

# Option to upload custom text
uploaded_file = st.sidebar.file_uploader("Upload custom text", type="txt")

# Display text (user can adjust the speed of words per minute)
if selected_text and selected_text != "No texts available" or uploaded_file:
    if uploaded_file:
        current_text = text_parser.load_text_from_file(uploaded_file)
    else:
        current_text = text_parser.load_text_from_file(f"data/pre_texts/{selected_text}.txt")

    st.subheader("Text to Memorize")
    
    # Scrolling text display controls
    words_per_minute = st.slider("Words per Minute", min_value=50, max_value=300, value=150)
    
    # Auto-scroll toggle
    auto_scroll = st.checkbox("Enable Auto-Scroll", value=False)
    
    # Calculate scroll timing
    words = current_text.split()
    total_words = len(words)
    scroll_delay = 60 / words_per_minute  # seconds per word
    
    # Text display container with scrolling
    text_container = st.container()
    
    if auto_scroll:
        # Initialize session state for scrolling
        if 'scroll_position' not in st.session_state:
            st.session_state.scroll_position = 0
        if 'scroll_active' not in st.session_state:
            st.session_state.scroll_active = False
            
        # Scroll controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("▶️ Start Scroll"):
                st.session_state.scroll_active = True
                st.session_state.scroll_position = 0
        with col2:
            if st.button("⏸️ Pause Scroll"):
                st.session_state.scroll_active = False
        with col3:
            if st.button("🔄 Reset Scroll"):
                st.session_state.scroll_position = 0
                st.session_state.scroll_active = False
        
        # Display scrolling text
        with text_container:
            # Show current position indicator
            st.write(f"Progress: {st.session_state.scroll_position}/{total_words} words")
            
            # Create highlighted text display
            highlighted_text = ""
            for i, word in enumerate(words):
                if i < st.session_state.scroll_position:
                    # Already covered words (dimmed)
                    highlighted_text += f'<span style="color: #888888;">{word}</span> '
                elif i == st.session_state.scroll_position:
                    # Current word (highlighted)
                    highlighted_text += f'<span style="background-color: #ffff00; font-weight: bold;">{word}</span> '
                else:
                    # Upcoming words (normal)
                    highlighted_text += f'{word} '
            
            st.markdown(highlighted_text, unsafe_allow_html=True)
            
        # Auto-advance logic (simplified for demo)
        if st.session_state.scroll_active and st.session_state.scroll_position < total_words:
            # Manual advance for demo - in real implementation, this would be time-based
            if st.button("➡️ Next Word"):
                st.session_state.scroll_position += 1
                st.rerun()
                
        # Show completion
        if st.session_state.scroll_position >= total_words:
            st.success("🎉 Text completed!")
            st.session_state.scroll_active = False
    else:
        # Static text display
        with text_container:
            st.markdown(f'<div style="font-size: 18px; line-height: 1.6; padding: 20px; background-color: #f0f0f0; border-radius: 10px;">{current_text}</div>', unsafe_allow_html=True)
    
    st.text(f"Text contains {total_words} words - estimated time: {(total_words * scroll_delay / 60):.1f} minutes at {words_per_minute} WPM")

# Audio Input and Processing
st.subheader("Audio Input")

# Live recording controls
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🎤 Start Recording"):
        if 'recording_state' not in st.session_state:
            st.session_state.recording_state = 'ready'
        st.session_state.recording_state = 'recording'
        st.success("Recording started...")

with col2:
    if st.button("⏸️ Pause"):
        if 'recording_state' in st.session_state:
            st.session_state.recording_state = 'paused'
        st.info("Recording paused")

with col3:
    if st.button("▶️ Resume"):
        if 'recording_state' in st.session_state:
            st.session_state.recording_state = 'recording'
        st.success("Recording resumed")

with col4:
    if st.button("🔄 Restart"):
        st.session_state.recording_state = 'ready'
        st.session_state.transcribed_text = ""
        st.info("Ready to record")

# Record duration setting
recording_duration = st.slider("Recording Duration (seconds)", min_value=3, max_value=30, value=10)

# Live recording functionality
if st.button("📝 Record and Transcribe"):
    if 'current_text' in locals() and current_text:
        with st.spinner(f"Recording for {recording_duration} seconds..."):
            transcribed_text = audio_handler.record_live_audio(recording_duration)
        st.session_state.transcribed_text = transcribed_text
        st.write("Transcribed Text:")
        st.write(transcribed_text)
        
        # Compare with original text
        comparison_results = text_parser.compare_text(transcribed_text, current_text)
        st.write("Comparison Results:")
        st.write(f"Accuracy: {((comparison_results['total_words'] - comparison_results['errors']) / comparison_results['total_words'] * 100):.1f}%")
        st.write(f"Total Words: {comparison_results['total_words']}")
        st.write(f"Errors: {comparison_results['errors']}")
        
        if comparison_results['differences']:
            st.write("Word Differences:")
            for original, transcribed in comparison_results['differences']:
                st.write(f"Expected: '{original}' → You said: '{transcribed}'")
        
        # Update user stats
        user_management.update_stats(comparison_results)
    else:
        st.warning("Please select a text to memorize first!")

# File upload option (keep existing functionality)
st.write("---")
st.write("Or upload an audio file:")
audio_file = st.file_uploader("Upload your audio file", type=["wav", "mp3"])

if audio_file:
    st.write("Processing audio...")
    transcribed_text = audio_handler.transcribe_audio(audio_file)
    st.write("Transcribed Text:")
    st.write(transcribed_text)

    # Compare transcribed text with the original
    if 'current_text' in locals() and current_text:
        comparison_results = text_parser.compare_text(transcribed_text, current_text)
        st.write("Comparison Results:")
        st.write(comparison_results['differences'])

        # Update and display user performance statistics
        user_management.update_stats(comparison_results)
        st.write(f"Total Words: {comparison_results['total_words']}")
        st.write(f"Errors: {comparison_results['errors']}")

# Display user's statistics
st.sidebar.subheader("User Stats")
st.sidebar.write(f"Total Words Memorized: {user_stats['total_words']}")
st.sidebar.write(f"Total Errors: {user_stats['errors']}")