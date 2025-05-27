import streamlit as st
import os
import json
import numpy as np
import sounddevice as sd
import soundfile as sf
import queue
import threading
import time
import platform
from utils.text_parser import parse_speech_text_file

# Set PulseAudio as the host API if available
try:
    # Check if PULSE_SERVER is set, which indicates we're using PulseAudio forwarding
    if 'PULSE_SERVER' in os.environ:
        st.write(f"PulseAudio server detected: {os.environ['PULSE_SERVER']}")
        # Try to configure sounddevice to use PulseAudio
        host_apis = sd.query_hostapis()
        for i, api in enumerate(host_apis):
            if 'pulse' in api['name'].lower():
                sd.default.hostapi = i
                st.write(f"Using PulseAudio as default host API")
                break
except Exception as e:
    st.write(f"Error configuring PulseAudio: {e}")
    # Continue anyway, as we'll try other methods

# Global variables for audio recording
audio_q = queue.Queue()
is_recording_active = False
recording_thread = None

def load_available_texts():
    """
    Scans the data/pre_texts/ directory for .json files, parses them,
    and returns a dictionary mapping titles to their full text content.
    """
    loaded_texts_map = {}
    texts_path = "data/pre_texts/"
    if not os.path.exists(texts_path):
        st.error(f"Directory not found: {texts_path}")
        return {}

    titles = []
    for filename in os.listdir(texts_path):
        if filename.endswith(".json"):
            filepath = os.path.join(texts_path, filename)
            try:
                parsed_content = parse_speech_text_file(filepath)
                title = parsed_content.get("title", "Untitled")
                text_content = parsed_content.get("text", "")
                
                # Ensure unique titles, append filename if not unique
                original_title = title
                count = 1
                while title in loaded_texts_map:
                    title = f"{original_title} ({count})"
                    count += 1
                
                loaded_texts_map[title] = text_content
                titles.append(title)
            except FileNotFoundError:
                st.error(f"File not found during scan: {filepath}")
            except ValueError as e:
                st.error(f"Error parsing JSON file {filepath}: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred with {filepath}: {e}")
    
    return loaded_texts_map, titles

def list_input_devices():
    """List available input audio devices with additional logging for debugging"""
    try:
        # Print debug info about the audio system
        st.write("Checking audio system...")
        devices = sd.query_devices()
        st.write(f"Found {len(devices)} audio devices in total.")
        
        input_devices = []
        for i, device in enumerate(devices):
            st.write(f"Device {i}: {device}")
            if device.get('max_input_channels', 0) > 0:
                device_name = device.get('name', f"Device {i}")
                input_devices.append({
                    "id": i, 
                    "name": device_name, 
                    "channels": device.get('max_input_channels'), 
                    "samplerate": device.get('default_samplerate')
                })
                
        # Try to force detection of the system default device
        try:
            default_device = sd.default.device[0]  # Index 0 is input device
            st.write(f"Default input device ID: {default_device}")
            
            # If we didn't find any input devices but have a default, add it
            if not input_devices and default_device is not None:
                default_info = sd.query_devices(default_device)
                if default_info.get('max_input_channels', 0) > 0:
                    st.write("Adding default device to list")
                    input_devices.append({
                        "id": default_device,
                        "name": default_info.get('name', f"Default Device {default_device}"),
                        "channels": default_info.get('max_input_channels'),
                        "samplerate": default_info.get('default_samplerate')
                    })
        except Exception as e:
            st.write(f"Error getting default device: {e}")
            
        return input_devices
    except Exception as e:
        st.error(f"Error listing audio devices: {e}")
        return []

def audio_callback(indata, frames, time, status):
    """This is called for each audio block"""
    if status:
        st.error(status)
    audio_q.put(indata.copy())

def start_recording(device_id=None, samplerate=44100, channels=1, output_filename="temp_audio.wav"):
    global is_recording_active, audio_q, recording_thread
    
    if is_recording_active:
        st.warning("Recording is already active.")
        return False
    
    audio_q = queue.Queue()
    
    try:
        # Determine device_id
        selected_device_id = device_id
        if selected_device_id is None:
            try:
                selected_device_id = sd.default.device[0]
                if sd.query_devices(selected_device_id)['max_input_channels'] == 0:
                    raise IndexError("Default input device has no input channels.")
            except IndexError:
                available_devices = list_input_devices()
                if not available_devices:
                    st.error("No input devices found.")
                    return False
                selected_device_id = available_devices[0]['id']
        
        device_info = sd.query_devices(selected_device_id)
        actual_samplerate = samplerate if samplerate else device_info['default_samplerate']
        
        stream = sd.InputStream(
            samplerate=actual_samplerate,
            device=selected_device_id,
            channels=channels,
            callback=audio_callback,
            dtype='float32'
        )
        stream.start()
        is_recording_active = True
        
        # Start the thread for recording
        recording_thread = threading.Thread(
            target=record_to_file_thread, 
            args=(output_filename, channels, actual_samplerate, stream)
        )
        recording_thread.start()
        
        return True
    except Exception as e:
        st.error(f"Error starting recording: {e}")
        is_recording_active = False
        return False

def record_to_file_thread(output_filename, channels, samplerate, stream):
    global is_recording_active, audio_q
    
    all_data = []
    
    try:
        while is_recording_active:
            try:
                data = audio_q.get(timeout=0.1)
                all_data.append(data.copy())
            except queue.Empty:
                pass
                
    except Exception as e:
        st.error(f"Error in recording thread: {e}")
    finally:
        stream.stop()
        stream.close()
        
        if all_data and is_recording_active:
            # Convert all data to a single numpy array
            data_array = np.concatenate(all_data)
            # Save as WAV file
            sf.write(output_filename, data_array, int(samplerate))
            st.success(f"Recording saved to {output_filename}")
        else:
            st.warning("No data recorded or recording stopped prematurely")

def stop_recording():
    global is_recording_active, recording_thread
    
    if not is_recording_active:
        st.warning("Recording is not active.")
        return
    
    is_recording_active = False
    
    if recording_thread and recording_thread.is_alive():
        recording_thread.join(timeout=1.0)
    
    st.success("Recording stopped.")

def highlight_text(text, words_to_highlight=None, words_to_cover=None):
    """
    Returns HTML-formatted text with words highlighted or covered
    
    Args:
        text (str): The original text
        words_to_highlight (list): List of (start_idx, end_idx) for words to highlight
        words_to_cover (list): List of (start_idx, end_idx) for words to cover
    """
    if not words_to_highlight and not words_to_cover:
        return text
    
    # Split text into words
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        if words_to_highlight and i in words_to_highlight:
            result.append(f'<span style="background-color: yellow;">{word}</span>')
        elif words_to_cover and i in words_to_cover:
            result.append(f'<span style="color: white; background-color: white;">{word}</span>')
        else:
            result.append(word)
    
    return ' '.join(result)

def main():
    st.set_page_config(
        page_title="Speech Memorization Platform",
        page_icon="🎤",
        layout="wide"
    )
    
    st.title("Speech Memorization Platform")
    st.markdown("""
    An interactive application designed to help users memorize and practice speeches.
    """)
    
    # Initialize session state
    if 'loaded_texts_map' not in st.session_state:
        st.session_state.loaded_texts_map, titles = load_available_texts()
        st.session_state.titles = titles
        st.session_state.current_text = ""
        st.session_state.highlighted_words = []
        st.session_state.covered_words = []
        st.session_state.highlight_index = 0
        st.session_state.cover_index = 0
        st.session_state.is_recording = False
        st.session_state.audio_devices = list_input_devices()
    
    # Speech selection dropdown
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.titles:
            selected_title = st.selectbox(
                "Select Speech:", 
                st.session_state.titles,
                key="speech_selector"
            )
            
            if selected_title and selected_title in st.session_state.loaded_texts_map:
                st.session_state.current_text = st.session_state.loaded_texts_map[selected_title]
                # Reset highlighting and covering when a new text is selected
                st.session_state.highlighted_words = []
                st.session_state.covered_words = []
                st.session_state.highlight_index = 0
                st.session_state.cover_index = 0
        else:
            st.warning("No speech texts found. Please add speech texts to the data/pre_texts/ directory.")
    
    # Text display area
    st.markdown("## Speech Text")
    
    if st.session_state.current_text:
        # Show text with highlighted and covered words
        formatted_text = highlight_text(
            st.session_state.current_text,
            st.session_state.highlighted_words,
            st.session_state.covered_words
        )
        
        # Display the formatted text
        st.markdown(formatted_text, unsafe_allow_html=True)
    else:
        st.info("Select a speech from the dropdown to display its content.")
    
    # Control buttons
    st.markdown("## Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Highlight Next Word"):
            if st.session_state.current_text:
                words = st.session_state.current_text.split()
                if st.session_state.highlight_index < len(words):
                    # Remove any existing highlights
                    st.session_state.highlighted_words = [st.session_state.highlight_index]
                    # Remove any covering from this word
                    if st.session_state.highlight_index in st.session_state.covered_words:
                        st.session_state.covered_words.remove(st.session_state.highlight_index)
                    st.session_state.highlight_index += 1
                else:
                    # Reset if we've reached the end
                    st.session_state.highlighted_words = []
                    st.session_state.highlight_index = 0
                    st.info("End of text reached. Highlighting will restart.")
    
    with col2:
        if st.button("Cover Next Word"):
            if st.session_state.current_text:
                words = st.session_state.current_text.split()
                if st.session_state.cover_index < len(words):
                    # Add this word to covered words
                    if st.session_state.cover_index not in st.session_state.covered_words:
                        st.session_state.covered_words.append(st.session_state.cover_index)
                    # Remove any highlighting from this word
                    if st.session_state.highlight_index == st.session_state.cover_index:
                        st.session_state.highlighted_words = []
                    st.session_state.cover_index += 1
                else:
                    # Reset if we've reached the end
                    st.session_state.covered_words = []
                    st.session_state.cover_index = 0
                    st.info("End of text reached. Covering will restart.")
    
    with col3:
        if st.button("Reset Display"):
            st.session_state.highlighted_words = []
            st.session_state.covered_words = []
            st.session_state.highlight_index = 0
            st.session_state.cover_index = 0
    
    # Audio recording section
    st.markdown("## Audio Recording")
    
    # Check if running in Docker
    in_docker = os.path.exists('/.dockerenv')
    
    # Select microphone
    if st.session_state.audio_devices:
        device_names = [dev['name'] for dev in st.session_state.audio_devices]
        selected_device_name = st.selectbox("Select Microphone:", device_names)
        
        # Get the device ID for the selected name
        selected_device_id = None
        for device in st.session_state.audio_devices:
            if device['name'] == selected_device_name:
                selected_device_id = device['id']
                break
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.is_recording:
                if st.button("Start Recording"):
                    if start_recording(device_id=selected_device_id, output_filename="session_recording.wav"):
                        st.session_state.is_recording = True
                        st.experimental_rerun()
            else:
                st.info("Recording in progress...")
        
        with col2:
            if st.session_state.is_recording:
                if st.button("Stop Recording"):
                    stop_recording()
                    st.session_state.is_recording = False
                    st.experimental_rerun()
    else:
        if in_docker:
            st.warning("No audio input devices found in Docker container. Audio recording is not available when running in Docker because containers don't have access to host audio devices by default.")
            st.info("To use audio recording features, you can run the application directly on your host machine outside of Docker.")
            
            # Add a simulated recording option for testing in Docker
            if st.button("Simulate Recording (Docker Test)"):
                st.success("This is a simulated recording for testing the UI flow in Docker. No actual audio is being recorded.")
                st.info("In a real recording scenario, the recorded audio would be saved to 'session_recording.wav'.")
        else:
            st.error("No audio input devices found. Please check if your microphone is connected and properly configured.")
            st.info("If you have a microphone connected, try restarting the application.")

if __name__ == "__main__":
    main()
