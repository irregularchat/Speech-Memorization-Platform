# ./app.py
# Import necessary libraries
import streamlit as st
from utils import text_parser, audio_handler, user_management, spaced_repetition
import os

# Initialize spaced repetition manager and analytics
if 'sr_manager' not in st.session_state:
    st.session_state.sr_manager = spaced_repetition.SpacedRepetitionManager()
if 'analytics' not in st.session_state:
    from utils import analytics
    st.session_state.analytics = analytics.PerformanceAnalytics()

# Initialize session state variables
if 'current_text' not in st.session_state:
    st.session_state.current_text = None
if 'user_stats' not in st.session_state:
    st.session_state.user_stats = user_management.load_user_stats()
if 'mastery_percentage' not in st.session_state:
    st.session_state.mastery_percentage = 0

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
    try:
        if uploaded_file:
            st.session_state.current_text = text_parser.load_text_from_file(uploaded_file)
            st.success("Custom text loaded successfully!")
        else:
            st.session_state.current_text = text_parser.load_text_from_file(f"data/pre_texts/{selected_text}.txt")
            st.success(f"Text '{selected_text}' loaded successfully!")
        
        current_text = st.session_state.current_text
        
    except FileNotFoundError as e:
        st.error(f"❌ File not found: {e}")
        st.stop()
    except ValueError as e:
        st.error(f"❌ Invalid file: {e}")
        st.stop()
    except PermissionError as e:
        st.error(f"❌ Permission denied: {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading text: {e}")
        st.stop()

    st.subheader("Text to Memorize")
    
    # Spaced repetition controls
    col1, col2 = st.columns(2)
    with col1:
        mastery_percentage = st.slider("Mastery Level (% words hidden)", 
                                     min_value=0, max_value=100, 
                                     value=st.session_state.mastery_percentage,
                                     help="Hide words based on your memorization progress")
        st.session_state.mastery_percentage = mastery_percentage
    
    with col2:
        # Display word statistics
        word_stats = st.session_state.sr_manager.get_word_statistics(current_text)
        st.metric("Words Mastered", f"{word_stats['mastered_words']}/{word_stats['total_words']}")
        if word_stats['tracked_words'] > 0:
            st.metric("Average Mastery", f"{word_stats['average_mastery']:.1f}/5")
    
    # Apply spaced repetition to text
    display_text = st.session_state.sr_manager.apply_spaced_repetition(current_text, mastery_percentage)
    
    # Scrolling text display controls
    words_per_minute = st.slider("Words per Minute", min_value=50, max_value=300, value=150)
    
    # Auto-scroll toggle
    auto_scroll = st.checkbox("Enable Auto-Scroll", value=False)
    
    # Calculate scroll timing
    words = display_text.split()
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
            st.markdown(f'<div style="font-size: 18px; line-height: 1.6; padding: 20px; background-color: #f0f0f0; border-radius: 10px;">{display_text}</div>', unsafe_allow_html=True)
    
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
            
        # Check if recording was successful
        if transcribed_text.startswith(("Recording timeout", "Could not", "Error", "Invalid", "Microphone not", "Speech recognition")):
            st.error(f"❌ Recording failed: {transcribed_text}")
            st.stop()
        st.session_state.transcribed_text = transcribed_text
        st.write("Transcribed Text:")
        st.write(transcribed_text)
        
        # Compare with original text
        comparison_results = text_parser.compare_text(transcribed_text, current_text)
        st.write("Comparison Results:")
        accuracy = ((comparison_results['total_words'] - comparison_results['errors']) / comparison_results['total_words'] * 100)
        st.write(f"Accuracy: {accuracy:.1f}%")
        st.write(f"Total Words: {comparison_results['total_words']}")
        st.write(f"Errors: {comparison_results['errors']}")
        
        # Update spaced repetition data for each word
        words_spoken = transcribed_text.split()
        original_words = current_text.split()
        
        # Update word performance in spaced repetition system
        for i, original_word in enumerate(original_words):
            if i < len(words_spoken):
                spoken_word = words_spoken[i]
                # Clean words for comparison
                clean_original = text_parser.clean_word(original_word)
                clean_spoken = text_parser.clean_word(spoken_word)
                correct = clean_original.lower() == clean_spoken.lower()
                st.session_state.sr_manager.update_word_performance(clean_original, correct)
        
        if comparison_results['differences']:
            st.write("Word Differences:")
            for original, transcribed in comparison_results['differences']:
                st.write(f"Expected: '{original}' → You said: '{transcribed}'")
        
        # Update user stats
        user_management.update_stats(comparison_results)
        st.session_state.user_stats = user_management.load_user_stats()
        
        # Log session for analytics
        session_data = {
            'text_name': selected_text if selected_text != "No texts available" else "Custom Text",
            'words_practiced': comparison_results['total_words'],
            'accuracy': accuracy,
            'errors': comparison_results['errors'],
            'duration_minutes': recording_duration / 60,  # Convert seconds to minutes
            'words_per_minute': words_per_minute,
            'mastery_level': mastery_percentage
        }
        st.session_state.analytics.log_session(session_data)
    else:
        st.warning("Please select a text to memorize first!")

# File upload option (keep existing functionality)
st.write("---")
st.write("Or upload an audio file:")
audio_file = st.file_uploader("Upload your audio file", type=["wav", "mp3"])

if audio_file:
    try:
        st.write("Processing audio...")
        transcribed_text = audio_handler.transcribe_audio(audio_file)
        
        # Check if transcription was successful
        if transcribed_text.startswith(("Could not", "Speech recognition", "Invalid", "No speech", "Unexpected")):
            st.error(f"❌ Transcription failed: {transcribed_text}")
        else:
            st.write("Transcribed Text:")
            st.write(transcribed_text)

            # Compare transcribed text with the original
            if 'current_text' in locals() and current_text:
                try:
                    comparison_results = text_parser.compare_text(transcribed_text, current_text)
                    st.write("Comparison Results:")
                    st.write(comparison_results['differences'])

                    # Update and display user performance statistics
                    user_management.update_stats(comparison_results)
                    st.write(f"Total Words: {comparison_results['total_words']}")
                    st.write(f"Errors: {comparison_results['errors']}")
                except Exception as e:
                    st.error(f"❌ Error comparing texts: {e}")
            else:
                st.warning("⚠️ No text selected for comparison")
                
    except Exception as e:
        st.error(f"❌ Error processing audio file: {e}")

# Performance Analytics Sidebar
st.sidebar.subheader("📊 Performance Analytics")

# Get analytics data
analytics_data = st.session_state.analytics.get_detailed_analytics()
overview = analytics_data['overview']
recent_30 = analytics_data['recent_performance']['last_30_days']

# Overview metrics
st.sidebar.metric("Current Streak", f"{overview['current_streak']} days")
st.sidebar.metric("Total Sessions", overview['total_sessions'])
st.sidebar.metric("Practice Time", f"{overview['total_practice_time']:.1f} min")

if recent_30:
    st.sidebar.metric("30-Day Accuracy", f"{recent_30['average_accuracy']:.1f}%")
    
    # Show improvement trend
    trend = recent_30['improvement_trend']
    trend_emoji = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
    st.sidebar.write(f"{trend_emoji} Trend: {trend:+.1f}%")

# Best session info
if overview['best_session']['accuracy'] > 0:
    st.sidebar.write("🏆 Best Session:")
    st.sidebar.write(f"  {overview['best_session']['accuracy']:.1f}% accuracy")

# Show detailed analytics button
if st.sidebar.button("📈 View Detailed Analytics"):
    st.session_state.show_analytics = True

# Detailed analytics display
if st.session_state.get('show_analytics', False):
    st.subheader("📊 Detailed Performance Analytics")
    
    if recent_30:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("30-Day Sessions", recent_30['total_sessions'])
        with col2:
            st.metric("Words Practiced", recent_30['total_words_practiced'])
        with col3:
            st.metric("Avg Accuracy", f"{recent_30['average_accuracy']:.1f}%")
        with col4:
            st.metric("Daily Consistency", f"{recent_30['daily_consistency']}/30 days")
        
        # Text performance breakdown
        if recent_30['text_performance']:
            st.write("**Text Performance (Last 30 Days):**")
            for text_name, perf in recent_30['text_performance'].items():
                st.write(f"• {text_name}: {perf['avg_accuracy']:.1f}% avg ({perf['sessions']} sessions)")
        
        # Accuracy trend chart
        if analytics_data['trends']['accuracy_trend']:
            st.line_chart(analytics_data['trends']['accuracy_trend'])
    
    if st.button("❌ Close Analytics"):
        st.session_state.show_analytics = False

# Basic user stats (keep existing)
st.sidebar.subheader("User Stats")
st.sidebar.write(f"Total Words Memorized: {st.session_state.user_stats['total_words']}")
st.sidebar.write(f"Total Errors: {st.session_state.user_stats['errors']}")