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
pre_texts = ["Creed 1", "Creed 2", "Speech 1", "Speech 2"]
selected_text = st.sidebar.selectbox("Choose a pre-loaded text", pre_texts)

# Option to upload custom text
uploaded_file = st.sidebar.file_uploader("Upload custom text", type="txt")

# Display text (user can adjust the speed of words per minute)
if selected_text or uploaded_file:
    if uploaded_file:
        current_text = text_parser.load_text_from_file(uploaded_file)
    else:
        current_text = text_parser.load_text_from_file(f"data/pre_texts/{selected_text}.txt")

    st.subheader("Text to Memorize")
    st.write(current_text)

    words_per_minute = st.slider("Words per Minute", min_value=50, max_value=300, value=150)
    st.text(f"Text scrolling at {words_per_minute} WPM")

# Audio Input and Processing
st.subheader("Audio Input")
audio_file = st.file_uploader("Upload your audio file", type=["wav", "mp3"])

if audio_file:
    st.write("Processing audio...")
    transcribed_text = audio_handler.transcribe_audio(audio_file)
    st.write("Transcribed Text:")
    st.write(transcribed_text)

    # Compare transcribed text with the original
    if current_text:
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